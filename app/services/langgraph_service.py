"""
LangGraph 서비스 - 조건부 분기를 통한 지능적 경로 선택

새로운 플로우:
사용자 요청 → 의도 분석 → 벡터 유사도 분석 → {
    유사도 < 0.43: 다른 Agent로 경로 재탐색
    유사도 >= 0.43: 기존 경로 top k 순위화
} → 최종 경로 선택
"""

import json
import time
from typing import TypedDict, List, Optional
import os
import re
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from app.services import neo4j_service
from app.services.embedding_service import generate_embedding


class PathSelectionState(TypedDict):
    """State for conditional path selection workflow"""
    user_query: str
    domain_hint: Optional[str]
    query_embedding: List[float]
    intent_analysis: dict  # 의도 분석 결과
    similarity_threshold: float  # 벡터 유사도 임계값
    max_similarity: float  # 최대 유사도 점수
    selected_paths: List[dict]  # 최종 선택된 경로들
    processing_strategy: str  # 사용된 처리 전략
    reasoning: str
    limit: int  # 반환할 경로 수
    cached_search_results: Optional[dict]  # 캐시된 검색 결과 (중복 검색 방지)
    
# Util 함수
def parse_llm_json(text: str) -> dict:
    # 1) 방어적 정리: 양끝 공백, BOM 제거
    s = text.lstrip("\ufeff").strip()

    # 2) 코드펜스 제거 (```json ... ```, ``` ... ```)
    if s.startswith("```"):
        # 첫 줄이 ```json 또는 ``` 인 경우만 잘라내기
        # (맨 끝의 ``` 제거)
        s = re.sub(r"^```[a-zA-Z0-9]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s)

    # 3) 문자열 전체가 JSON이 아닐 수도 있으니 {...} 블록만 추출
    #    - 가장 앞의 '{'와 가장 뒤의 '}' 사이를 잘라서 시도
    if not (s.startswith("{") and s.endswith("}")):
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            s = s[start:end+1]

    return json.loads(s)

# ============================================================================
# LangGraph 워크플로우 노드 구현
# ============================================================================

def _debug_node_execution(node_name: str, state: dict, is_start: bool = True):
    """노드 실행 디버깅 출력"""
    action = "시작" if is_start else "완료"
    print(f"🔍 [{node_name}] {action}")
    if is_start:
        print(f"   입력 상태: {list(state.keys())}")
    else:
        print(f"   출력 상태: {list(state.keys())}")
    print("-" * 50)


def _debug_edge_transition(from_node: str, to_node: str, condition: str = None):
    """엣지 전환 디버깅 출력"""
    if condition:
        print(f"➡️  [{from_node}] → [{to_node}] (조건: {condition})")
    else:
        print(f"➡️  [{from_node}] → [{to_node}]")
    print("-" * 50)


async def analyze_user_intent(state: PathSelectionState) -> PathSelectionState:
    """
    사용자 쿼리의 의도를 분석하고 다음 단계를 위한 컨텍스트 제공
    
    분석 항목:
    - 의도 유형: navigation, task_completion, information_seeking, exploration
    - 도메인 선호도: 특정 사이트나 서비스에 대한 언급
    - 복잡도: 단순한 작업인지 복합적인 작업인지
    - 긴급도: 즉시 실행이 필요한 작업인지
    """
    
    # 환경 변수 없으면 LLM 생략
    use_llm = bool(os.getenv("OPENAI_API_KEY"))
    print(f"🔧 LLM 사용 여부: {use_llm}")
    
    if not use_llm:
        print("⚠️  OPENAI_API_KEY가 없어서 휴리스틱 폴백 사용")
        result = {
            "intent_type": "information_seeking",
            "domain_preference": None,
            "complexity": "simple",
            "confidence": 0.6,
            "reasoning": "Heuristic fallback without LLM",
            "keywords": [state["user_query"]]  # 기본적으로 원본 쿼리 사용
        }
    else:
        llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0, 
            max_retries=2,
            request_timeout=10.0  # 10초 타임아웃 설정
        )
        
        prompt = f"""
        당신은 웹 자동화 서비스의 의도 분석 에이전트입니다.
        사용자 쿼리를 분석하여 의도 유형, 도메인 선호도, 작업 복잡도, 신뢰도 점수, 핵심 키워드를 추출해주세요.

        분석할 항목:
        1. 의도 유형 (navigation, task_completion, information_seeking, exploration)
        2. 도메인 선호도 (특정 사이트 언급 여부)
        3. 작업 복잡도 (simple, moderate, complex)
        4. 신뢰도 점수 (0.0-1.0)
        5. 핵심 키워드 (검색에 사용할 핵심 단어들)

        예시:
        
        query: "유튜브에서 좋아요 누르기"
        response: {{
            "intent_type": "task_completion",
            "domain_preference": "youtube.com",
            "complexity": "simple",
            "confidence": 0.85,
            "reasoning": "사용자가 유튜브에서 특정 작업을 수행하려는 의도가 명확함",
            "keywords": ["유튜브", "좋아요", "누르기", "동영상"]
        }}

        query: "날씨가 너무 추워요"
        response: {{
            "intent_type": "information_seeking",
            "domain_preference": null,
            "complexity": "simple",
            "confidence": 0.75,
            "reasoning": "사용자가 날씨 정보를 찾고 있음",
            "keywords": ["날씨", "추위", "온도", "기온"]
        }}

        query: "요즘 나라가 어떻게 굴러가나"
        response: {{
            "intent_type": "navigation",
            "domain_preference": "naver.com",
            "complexity": "simple",
            "confidence": 0.90,
            "reasoning": "최신 국내 정치, 사회 이슈를 보려는 의도로 보임.",
            "keywords": ["시사", "정치", "뉴스", "최근 이슈"]
        }}

        이제 다음 쿼리를 분석해주세요:
        query: "{state['user_query']}"
        response:"""

        try:
            print("🤖 LLM 호출 중...")
            import asyncio
            
            # asyncio.wait_for로 타임아웃 설정 (12초 - LLM 자체 타임아웃 10초 + 여유 2초)
            response = await asyncio.wait_for(
                llm.ainvoke(prompt),
                timeout=12.0
            )
            print(f"📝 LLM 응답: {response.content}")
            result = parse_llm_json(response.content)
        except asyncio.TimeoutError:
            print(f"❌ LLM 호출 타임아웃 (12초)")
            result = {
                "intent_type": "information_seeking",
                "domain_preference": None,
                "complexity": "simple",
                "confidence": 0.5,
                "reasoning": "LLM 타임아웃으로 인한 폴백",
                "keywords": [state["user_query"]]
            }
        except Exception as e:
            print(f"❌ LLM 호출 실패: {e}")
            result = {
                "intent_type": "information_seeking",
                "domain_preference": None,
                "complexity": "simple",
                "confidence": 0.5,
                "reasoning": f"LLM 실패로 인한 폴백: {str(e)}",
                "keywords": [state["user_query"]]  # 기본적으로 원본 쿼리 사용
            }

    output_state = {
        **state,
        "intent_analysis": result,
        "query_embedding": generate_embedding(state["user_query"])
    }
    
    return output_state


async def analyze_vector_similarity(state: PathSelectionState) -> PathSelectionState:
    """
    기존 데이터베이스에서 벡터 유사도 분석하여 분기 결정
    
    분석 과정:
    1. 기존 검색으로 최대 유사도 점수 확인 (limit만큼 검색하여 캐싱)
    2. 임계값과 비교하여 분기 전략 결정
    3. 다음 단계를 위한 컨텍스트 제공
    
    최적화: rank_existing_paths에서 재사용할 수 있도록 검색 결과 캐싱
    """
    
    # 기존 검색으로 결과 확인 (요청된 limit만큼 검색하여 캐싱)
    existing_results = neo4j_service.search_paths_by_query(
        state["user_query"],
        limit=state.get("limit", 3),  # 요청된 개수만큼 검색
        domain_hint=state["domain_hint"]
    )
    
    max_similarity = 0.0
    if existing_results and existing_results["matched_paths"]:
        max_similarity = existing_results["matched_paths"][0].get("relevance_score", 0.0)
        print(f"📊 발견된 경로 수: {len(existing_results['matched_paths'])}")
        print(f"📊 경로 이름: {existing_results['matched_paths'][0].get('taskIntent')}")
        print(f"📊 최대 유사도: {max_similarity:.3f}")
    else:
        print("📊 기존 경로 없음")
    
    # 임계값 설정 (0.43)
    similarity_threshold = 0.43
    
    output_state = {
        **state,
        "max_similarity": max_similarity,
        "similarity_threshold": similarity_threshold,
        "cached_search_results": existing_results  # 검색 결과 캐싱
    }
    
    return output_state


def should_use_rediscovery_agent(state: PathSelectionState) -> str:
    """
    벡터 유사도에 따라 분기 결정
    
    Returns:
    - "high_similarity": 기존 경로 순위화 사용
    - "low_similarity": 다른 Agent로 재탐색 사용
    """
    max_similarity = state["max_similarity"]
    threshold = state["similarity_threshold"]
    
    print(f"🔀 분기 결정: 유사도 {max_similarity:.3f} vs 임계값 {threshold}")
    
    if max_similarity >= threshold:
        decision = "high_similarity"
        print(f"✅ 높은 유사도 → rank_existing_paths")
    else:
        decision = "low_similarity"
        print(f"⚠️  낮은 유사도 → analyze_intent")
    
    return decision


async def rank_existing_paths(state: PathSelectionState) -> PathSelectionState:
    """
    높은 유사도가 확인된 경우 기존 경로들을 순위화
    
    높은 유사도일 때는 의도 분석 없이 기존 경로만 반환
    
    최적화: analyze_vector_similarity에서 캐싱된 검색 결과 재사용
    """
    
    # 캐시된 검색 결과 사용 (중복 Neo4j 쿼리 방지)
    existing_results = state.get("cached_search_results")
    
    if not existing_results:
        print("❌ 캐시된 검색 결과가 없음")
        output_state = {
            **state,
            "selected_paths": [],
            "processing_strategy": "rank_existing_paths",
            "reasoning": "캐시된 검색 결과가 없어서 빈 결과 반환"
        }
        
        return output_state
    
    print(f"📊 캐시된 경로 사용: {len(existing_results['matched_paths'])}개")
    
    # 높은 유사도일 때는 기존 경로를 그대로 사용 (의도 분석 없이)
    selected_paths = existing_results["matched_paths"]
    
    # 각 경로에 기본 점수 정보 추가
    for i, path in enumerate(selected_paths):
        print(f"  {i+1}. {path.get('taskIntent', 'Unknown')} - 점수: {path.get('relevance_score', 0):.3f}")
    
    output_state = {
        **state,
        "selected_paths": selected_paths,
        "processing_strategy": "rank_existing_paths",
        "reasoning": f"높은 유사도({state['max_similarity']:.3f})로 캐시된 경로 사용 (중복 검색 제거)"
    }
    
    print(f"✅ 최종 선택된 경로 수: {len(output_state['selected_paths'])}")
    return output_state


async def rediscover_with_different_agent(state: PathSelectionState) -> PathSelectionState:
    """
    낮은 유사도 상황에서 다른 Agent 전략으로 경로 재탐색 (최적화)
    
    다른 Agent 전략:
    1. 키워드 기반 검색 Agent (단일 Agent로 최적화)
    """
    
    intent_analysis = state["intent_analysis"]
    print(f"🔍 낮은 유사도로 다른 Agent 전략 사용 (최대 유사도: {state['max_similarity']:.3f})")
    print(f"🔑 추출된 키워드: {intent_analysis.get('keywords', [])}")
    
    rediscovered_paths = []
    
    # Agent 1: 키워드 기반 검색 Agent (단일 Agent로 최적화)
    print("🤖 키워드 기반 검색 Agent 실행")
    keyword_agent_paths = await keyword_based_search_agent(state)
    rediscovered_paths.extend(keyword_agent_paths)
    print(f"📊 총 재탐색된 경로: {len(rediscovered_paths)}개")
    
    # 중복 제거 (간단한 방식)
    unique_paths = []
    seen_intents = set()
    for path in rediscovered_paths:
        intent_key = f"{path.get('domain', '')}_{path.get('taskIntent', '')}"
        if intent_key not in seen_intents:
            seen_intents.add(intent_key)
            unique_paths.append(path)
    
    print(f"📊 중복 제거 후: {len(unique_paths)}개")
    
    # 점수 재계산 (간단한 방식)
    scored_paths = []
    for i, path in enumerate(unique_paths):
        # 기본 점수에 약간의 보너스만 추가
        base_score = path.get("relevance_score", 0.0)
        path["rediscovery_score"] = base_score + 0.1  # 간단한 보너스
        scored_paths.append(path)
    
    # 점수로 정렬
    scored_paths.sort(key=lambda x: x["rediscovery_score"], reverse=True)
    
    # 클라이언트가 모르는 필드 제거 후 반환
    forbidden = {"agent_source", "rediscovery_score", "composite_score"}
    cleaned_paths = [
        {k: v for k, v in p.items() if k not in forbidden}
        for p in scored_paths
    ]

    output_state = {
        **state,
        "selected_paths": cleaned_paths[:state.get("limit", 3)],
        "processing_strategy": "rediscover_with_different_agent",
        "reasoning": f"낮은 유사도({state['max_similarity']:.3f})로 키워드 기반 Agent 사용"
    }
    
    print(f"✅ 최종 선택된 경로 수: {len(output_state['selected_paths'])}")
    return output_state


# ============================================================================
# 다중 Agent 구현
# ============================================================================

async def keyword_based_search_agent(state: PathSelectionState) -> List[dict]:
    """키워드 기반 검색 Agent (최적화 - 병렬 검색)"""
    import asyncio
    
    # 키워드 추출 및 확장
    keywords = extract_and_expand_keywords(state["user_query"], state["intent_analysis"])
    
    # 병렬 검색을 위한 비동기 함수
    async def search_keyword(keyword: str) -> List[dict]:
        try:
            # Neo4j 검색을 별도 스레드에서 실행 (blocking -> non-blocking)
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: neo4j_service.search_paths_by_query(
                    keyword,
                    limit=1,  # 각 키워드당 1개만 가져오기
                    domain_hint=None  # 도메인 제한 없이 검색
                )
            )
            
            if results and results["matched_paths"]:
                paths = []
                for path in results["matched_paths"]:
                    path["agent_source"] = "keyword_based"
                    paths.append(path)
                return paths
            return []
        except Exception as e:
            print(f"⚠️ 키워드 검색 실패 ({keyword}): {e}")
            return []
    
    # 최대 2개 키워드를 병렬로 검색
    search_tasks = [search_keyword(keyword) for keyword in keywords[:2]]
    results_lists = await asyncio.gather(*search_tasks)
    
    # 결과 병합
    paths = []
    for result_list in results_lists:
        paths.extend(result_list)
    
    print(f"🔑 키워드 기반 병렬 검색 완료: {len(paths)}개 경로")
    return paths


async def cross_domain_search_agent(state: PathSelectionState) -> List[dict]:
    """도메인 크로스 검색 Agent (최적화)"""
    intent_analysis = state["intent_analysis"]
    paths = []
    
    # 유사한 의도를 가진 다른 도메인 검색
    similar_intent_query = generate_cross_domain_query(intent_analysis)
    
    try:
        results = neo4j_service.search_paths_by_query(
            similar_intent_query,
            limit=2,  # 3개에서 2개로 줄임
            domain_hint=None  # 모든 도메인에서 검색
        )
        
        if results and results["matched_paths"]:
            for path in results["matched_paths"]:
                path["agent_source"] = "cross_domain"
                paths.append(path)
    except Exception as e:
        print(f"⚠️ 크로스 도메인 검색 실패: {e}")
    
    print(f"🌐 크로스 도메인 검색 완료: {len(paths)}개 경로")
    return paths

# ============================================================================
# 유틸리티 함수들
# ============================================================================

def extract_and_expand_keywords(query: str, intent_analysis: dict) -> List[str]:
    """LLM이 추출한 키워드를 사용하고 필요시 확장"""
    # LLM이 추출한 키워드 우선 사용
    llm_keywords = intent_analysis.get("keywords", [])
    
    if llm_keywords and len(llm_keywords) > 0:
        print(f"🔑 LLM 추출 키워드: {llm_keywords}")
        return llm_keywords[:4]  # 최대 4개로 제한
    
    # LLM 키워드가 없으면 원본 쿼리 사용
    print(f"🔑 LLM 키워드 없음, 원본 쿼리 사용: {query}")
    return [query]


def generate_cross_domain_query(intent_analysis: dict) -> str:
    """크로스 도메인 검색을 위한 쿼리 생성 (간단화)"""
    # LLM이 추출한 키워드 우선 사용
    keywords = intent_analysis.get("keywords", [])
    if keywords and len(keywords) > 0:
        # 키워드들을 조합하여 크로스 도메인 쿼리 생성
        return " ".join(keywords[:2])  # 최대 2개 키워드 조합으로 단순화
    
    # 키워드가 없으면 의도 유형 기반 생성
    intent_type = intent_analysis.get("intent_type", "information_seeking")
    return f"{intent_type} 관련 작업"


def deduplicate_paths(paths: List[dict]) -> List[dict]:
    """중복 경로 제거"""
    seen = set()
    unique_paths = []
    
    for path in paths:
        path_key = f"{path.get('domain', '')}_{path.get('taskIntent', '')}"
        if path_key not in seen:
            seen.add(path_key)
            unique_paths.append(path)
    
    return unique_paths


# ============================================================================
# 전역 워크플로우 캐시
# ============================================================================

# 전역 워크플로우 캐시
_langgraph_workflow = None
_workflow_initialized = False

def get_or_build_workflow():
    """워크플로우를 한 번만 빌드하고 캐시"""
    global _langgraph_workflow, _workflow_initialized
    
    if not _workflow_initialized:
        print("LangGraph 워크플로우 초기화 중...")
        start_time = time.time()
        
        _langgraph_workflow = build_path_selection_graph()
        
        init_time = int((time.time() - start_time) * 1000)
        print(f"LangGraph 워크플로우 초기화 완료 ({init_time}ms)")
        _workflow_initialized = True
    
    return _langgraph_workflow


def initialize_langgraph():
    """서버 시작 시 LangGraph 워크플로우 미리 초기화"""
    print("LangGraph 워크플로우 사전 초기화...")
    get_or_build_workflow()
    print("LangGraph 워크플로우 사전 초기화 완료")


# ============================================================================
# LangGraph 워크플로우 빌드 및 구조 출력
# ============================================================================

def build_path_selection_graph():
    """Build conditional LangGraph for path selection"""

    workflow = StateGraph(PathSelectionState)

    # Node: 벡터 유사도 분석 (진입점)
    workflow.add_node("analyze_similarity", analyze_vector_similarity)

    # Node: 의도 분석 (낮은 유사도일 때만 실행)
    workflow.add_node("analyze_intent", analyze_user_intent)

    # Node 3: 기존 경로 순위화 (높은 유사도)
    workflow.add_node("rank_existing_paths", rank_existing_paths)

    # Node 4: 다른 Agent로 경로 재탐색 (낮은 유사도)
    workflow.add_node("rediscover_with_agent", rediscover_with_different_agent)

    # 조건부 분기: 벡터 유사도에 따라 다른 전략 선택
    workflow.add_conditional_edges(
        "analyze_similarity",
        should_use_rediscovery_agent,
        {
            "high_similarity": "rank_existing_paths",
            "low_similarity": "analyze_intent"
        }
    )

    # 낮은 유사도 흐름: 의도 분석 후 재탐색
    workflow.add_edge("analyze_intent", "rediscover_with_agent")

    # 두 경로 모두 최종 결과로 연결
    workflow.add_edge("rank_existing_paths", END)
    workflow.add_edge("rediscover_with_agent", END)

    # 진입점은 유사도 분석
    workflow.set_entry_point("analyze_similarity")

    return workflow.compile()


def print_langgraph_structure():
    """LangGraph 워크플로우 구조를 출력"""
    workflow = get_or_build_workflow()
    
    print("\n" + "="*60)
    print("LangGraph 워크플로우 구조")
    print("="*60)
    
    # 워크플로우 정보 출력
    print(f"Entry Point: analyze_similarity")
    print(f"End Points: END")
    print(f"Total Nodes: 4")
    print(f"Conditional Branches: 1")
    
    print("\n노드 구조:")
    print("1. analyze_similarity - 벡터 유사도 분석")
    print("2. analyze_intent - 사용자 의도 분석 (유사도 < 0.43일 때만)")
    print("3. rank_existing_paths - 기존 경로 순위화 (유사도 >= 0.43)")
    print("4. rediscover_with_agent - 다른 Agent로 재탐색 (유사도 < 0.43)")
    
    print("\n분기 조건:")
    print("- 유사도 >= 0.43: rank_existing_paths")
    print("- 유사도 < 0.43: rediscover_with_agent")
    
    print("\n워크플로우 그래프:")
    print("analyze_similarity → {")
    print("    high_similarity: rank_existing_paths → END")
    print("    low_similarity: analyze_intent → rediscover_with_agent → END")
    print("}")
    
    print("\n" + "="*60)
    
    print(workflow.get_graph().draw_ascii())
    
    return workflow


def get_workflow_info():
    """워크플로우 정보를 딕셔너리로 반환"""
    return {
        "entry_point": "analyze_similarity",
        "end_points": ["END"],
        "total_nodes": 4,
        "conditional_branches": 1,
        "nodes": {
            "analyze_similarity": "벡터 유사도 분석",
            "analyze_intent": "사용자 의도 분석 (유사도 < 0.43)", 
            "rank_existing_paths": "기존 경로 순위화 (유사도 >= 0.43)",
            "rediscover_with_agent": "다른 Agent로 재탐색 (유사도 < 0.43)"
        },
        "threshold": 0.43,
        "branches": {
            "high_similarity": "rank_existing_paths",
            "low_similarity": "rediscover_with_agent"
        }
    }


# ============================================================================
# 메인 서비스 함수
# ============================================================================

async def search_with_langgraph(
    query: str, 
    limit: int = 5,
    domain_hint: Optional[str] = None
) -> dict:
    """
    LangGraph 워크플로우를 사용한 지능적 경로 검색
    
    Args:
        query: 사용자 자연어 쿼리
        limit: 최대 반환 경로 수
        domain_hint: 특정 도메인으로 제한 (선택사항)
    
    Returns:
        dict: 기존 응답 형식과 호환되는 검색 결과
    """
    print("🚀 LangGraph 워크플로우 시작")
    print(f"📝 쿼리: {query}, 제한: {limit}, 도메인 힌트: {domain_hint}")
    
    start_time = time.time()
    
    try:
        # 캐시된 워크플로우 사용 (빌드 시간 절약)
        workflow = get_or_build_workflow()
        
        initial_state = {
            "user_query": query,
            "domain_hint": domain_hint,
            "limit": limit,
            "query_embedding": [],  # 빈 리스트로 초기화
            "intent_analysis": {},  # 빈 딕셔너리로 초기화
            "similarity_threshold": 0.0,
            "max_similarity": 0.0,
            "selected_paths": [],
            "processing_strategy": "",
            "reasoning": "",
            "cached_search_results": None  # 캐시 초기화
        }
        
        print("🔄 워크플로우 실행 중...")
        result = await workflow.ainvoke(initial_state)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        print(f"⏱️ 총 처리 시간: {processing_time}ms")
        print(f"📊 발견된 경로 수: {len(result.get('selected_paths', []))}")
        
        # 기존 응답 형식으로 변환
        response = {
            "query": result["user_query"],
            "total_matched": len(result["selected_paths"]),
            "matched_paths": result["selected_paths"],
            "performance": {
                "search_time": processing_time,
                "reasoning": result["reasoning"],
                "strategy": result["processing_strategy"],
                "max_similarity": result["max_similarity"]
            }
        }
        
        print("✅ LangGraph 워크플로우 완료")
        return response
        
    except Exception as e:
        print(f"❌ LangGraph 워크플로우 실패: {e}")
        import traceback
        traceback.print_exc()
        print("🔄 기존 방식으로 폴백...")
        
        # 기존 검색 방식으로 폴백
        fallback_result = neo4j_service.search_paths_by_query(query, limit, domain_hint)
        if fallback_result:
            fallback_result["performance"]["reasoning"] = f"LangGraph 실패로 폴백: {str(e)}"
            fallback_result["performance"]["strategy"] = "fallback_traditional_search"
        
        print("="*60)
        return fallback_result


def format_langgraph_response(langgraph_result: dict) -> dict:
    """LangGraph 결과를 기존 응답 형식으로 변환"""
    return {
        "query": langgraph_result["user_query"],
        "total_matched": len(langgraph_result["selected_paths"]),
        "matched_paths": langgraph_result["selected_paths"],
        "performance": {
            "search_time": langgraph_result.get("processing_time", 0),
            "reasoning": langgraph_result.get("reasoning", ""),
            "strategy": langgraph_result.get("processing_strategy", "")
        }
    }


# ============================================================================
# 테스트 및 실행을 위한 Main 함수
# ============================================================================

async def test_langgraph_workflow():
    """LangGraph 워크플로우 테스트"""    
    # 테스트 쿼리들
    test_queries = [
        "왜 이렇게 추워",
        "SRT 예매"
    ]
    
    for i, query in enumerate(test_queries, 1):        
        try:
            result = await search_with_langgraph(query, limit=3)
            
            # print(f"✅ LangGraph로 검색 성공!")
            # print(f"📊 총 {result['total_matched']}개 경로 발견")
            # print(f"⏱️ 처리 시간: {result['performance']['search_time']}ms")
            # print(f"🧠 전략: {result['performance']['strategy']}")
            # print(f"💭 추론: {result['performance']['reasoning']}")
            # print(f"📈 최대 유사도: {result['performance']['max_similarity']:.3f}")
            
            if result['matched_paths']:
                # print("\n🔍 발견된 경로들:")
                for j, path in enumerate(result['matched_paths'], 1):
                    print(f"  {j}. {path.get('taskIntent', 'Unknown')}")
                    print(f"     도메인: {path.get('domain', 'Unknown')}")
                    print(f"     기존 유사도: {path.get('relevance_score', 0):.3f}")
                    if 'composite_score' in path:
                        print(f"     복합점수: {path['composite_score']:.3f}")
                    if 'rediscovery_score' in path:
                        print(f"     재탐색 점수: {path['rediscovery_score']:.3f}")
                    if 'agent_source' in path:
                        print(f"     Agent: {path['agent_source']}")
            else:
                print("❌ 경로를 찾지 못했습니다.")
                
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            import traceback
            traceback.print_exc()


async def interactive_test():
    """대화형 테스트"""
    print("🎯 LangGraph 대화형 테스트")
    
    while True:
        try:
            query = input("\n🔍 검색할 쿼리를 입력하세요 (종료: 'quit'): ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 테스트를 종료합니다.")
                break
                
            if not query:
                print("❌ 빈 쿼리는 입력할 수 없습니다.")
                continue
            
            print(f"\n🔍 검색 중: {query}")
            
            result = await search_with_langgraph(query, limit=3)
            
            print(f"✅ 대화형 경로 검색 완료!")
            print(f"📊 총 {result['total_matched']}개 경로 발견")
            print(f"⏱️ 처리 시간: {result['performance']['search_time']}ms")
            print(f"🧠 전략: {result['performance']['strategy']}")
            print(f"💭 추론: {result['performance']['reasoning']}")
            print(f"📈 최대 유사도: {result['performance']['max_similarity']:.3f}")
            
            if result['matched_paths']:
                print("\n🔍 발견된 경로들:")
                for j, path in enumerate(result['matched_paths'], 1):
                    print(f"  {j}. {path.get('taskIntent', 'Unknown')}")
                    print(f"     도메인: {path.get('domain', 'Unknown')}")
                    print(f"     점수: {path.get('relevance_score', 0):.3f}")
                    if 'composite_score' in path:
                        print(f"     복합점수: {path['composite_score']:.3f}")
                    if 'rediscovery_score' in path:
                        print(f"     재탐색점수: {path['rediscovery_score']:.3f}")
                    if 'agent_source' in path:
                        print(f"     Agent: {path['agent_source']}")
            else:
                print("❌ 경로를 찾지 못했습니다.")
                
        except KeyboardInterrupt:
            print("\n👋 테스트를 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {e}")


def show_workflow_structure():
    """워크플로우 구조 출력"""
    print_langgraph_structure()
    
    


if __name__ == "__main__":
    import asyncio
    import sys
    
    print("🎯 LangGraph 서비스 테스트 도구")
    print("="*60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "structure":
            show_workflow_structure()
        elif command == "test":
            asyncio.run(test_langgraph_workflow())
        elif command == "interactive":
            asyncio.run(interactive_test())
        else:
            print("❌ 알 수 없는 명령어입니다.")
            print("사용법:")
            print("  python app/services/langgraph_service.py structure  # 구조 출력")
            print("  python app/services/langgraph_service.py test       # 자동 테스트")
            print("  python app/services/langgraph_service.py interactive # 대화형 테스트")
    else:
        print("사용법:")
        print("  python app/services/langgraph_service.py structure  # 워크플로우 구조 출력")
        print("  python app/services/langgraph_service.py test       # 자동 테스트 실행")
        print("  python app/services/langgraph_service.py interactive # 대화형 테스트")
        print("\n또는 직접 실행:")
        print("  python -c \"import asyncio; from app.services.langgraph_service import test_langgraph_workflow; asyncio.run(test_langgraph_workflow())\"")
