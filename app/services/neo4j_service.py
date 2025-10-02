"""
Neo4j 서비스 - 리팩토링된 버전

새로운 DB 구조 (DB_refactor.md 기준):
- ROOT 노드 (도메인 정보 저장)
- STEP 노드 (기존 PAGE 확장)
- HAS_STEP 관계 (ROOT → 첫 STEP, taskIntent 포함)
- NEXT_STEP 관계 (STEP → STEP 순차 연결)
"""

import os
import json
import hashlib
import time

from datetime import datetime
from urllib.parse import urlparse
from typing import List, Optional
from dotenv import load_dotenv, find_dotenv
from langchain_neo4j import Neo4jGraph
from app.services.embedding_service import generate_embedding
from app.models.step import StepData, PathSubmission

load_dotenv(find_dotenv())

# Neo4j 그래프 객체 초기화
try:
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD"),
    )
    print("Neo4j Service: Database connection successful.")
except Exception as e:
    print(f"Neo4j Service: Database connection failed. Error: {e}")
    graph = None


# ============================================================================
# 유틸리티 함수
# ============================================================================

def extract_domain(url: str) -> str:
    """URL에서 도메인 추출"""
    parsed = urlparse(url)
    return parsed.netloc.replace('www.', '')


def create_step_id(url: str, selectors: List[str], action: str) -> str:
    """STEP 노드의 고유 ID 생성"""
    primary_selector = selectors[0] if selectors else 'no_selector'
    key = f"{url}_{primary_selector}_{action}"
    return hashlib.md5(key.encode()).hexdigest()


# ============================================================================
# 핵심 함수 - 경로 저장 및 검색
# ============================================================================

def save_path_to_neo4j(path_submission: PathSubmission):
    """
    새로운 구조로 경로 저장

    구조:
    (ROOT)-[HAS_STEP {taskIntent}]->(STEP)-[NEXT_STEP]->(STEP)->...

    Args:
        path_submission: PathSubmission 객체 (sessionId, taskIntent, domain, steps)

    Returns:
        dict: {'status': 'success'/'error', ...}
    """
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")

    try:
        domain = path_submission.domain
        task_intent = path_submission.taskIntent

        # 1. ROOT 노드 생성/업데이트
        root_embedding = generate_embedding(f"{domain} {task_intent}")

        create_root_query = """
        MERGE (r:ROOT {domain: $domain})
        ON CREATE SET
            r.baseURL = $baseURL,
            r.displayName = $displayName,
            r.embedding = $embedding,
            r.visitCount = 0,
            r.lastVisited = datetime()
        ON MATCH SET
            r.visitCount = r.visitCount + 1,
            r.lastVisited = datetime()
        RETURN r
        """

        graph.query(create_root_query, {
            'domain': domain,
            'baseURL': f"https://{domain}",
            'displayName': domain.replace('.com', '').replace('.', ' '),
            'embedding': root_embedding
        })

        print(f"✓ ROOT 노드 생성/업데이트: {domain}")

        # 2. 각 STEP 노드 생성 및 관계 연결
        previous_step_id = None
        intent_embedding = generate_embedding(task_intent)

        for order, step_data in enumerate(path_submission.steps):
            # STEP ID 생성
            step_id = create_step_id(step_data.url, step_data.selectors, step_data.action)

            # STEP 임베딩 생성
            embedding_text = f"{step_data.description} {' '.join(step_data.textLabels)}"
            if step_data.contextText:
                embedding_text += f" {step_data.contextText}"
            step_embedding = generate_embedding(embedding_text)

            # STEP 노드 생성/업데이트
            create_step_query = """
            MERGE (s:STEP {stepId: $stepId})
            SET s.url = $url,
                s.domain = $domain,
                s.selectors = $selectors,
                s.anchorPoint = $anchorPoint,
                s.relativePathFromAnchor = $relativePathFromAnchor,
                s.action = $action,
                s.isInput = $isInput,
                s.inputType = $inputType,
                s.inputPlaceholder = $inputPlaceholder,
                s.shouldWait = $shouldWait,
                s.waitMessage = $waitMessage,
                s.maxWaitTime = $maxWaitTime,
                s.description = $description,
                s.textLabels = $textLabels,
                s.contextText = $contextText,
                s.embedding = $embedding,
                s.createdAt = coalesce(s.createdAt, datetime()),
                s.lastUsed = datetime(),
                s.usageCount = coalesce(s.usageCount, 0) + 1,
                s.successRate = $successRate
            RETURN s
            """

            graph.query(create_step_query, {
                'stepId': step_id,
                'url': step_data.url,
                'domain': domain,
                'selectors': step_data.selectors,
                'anchorPoint': step_data.anchorPoint,
                'relativePathFromAnchor': step_data.relativePathFromAnchor,
                'action': step_data.action,
                'isInput': step_data.isInput,
                'inputType': step_data.inputType,
                'inputPlaceholder': step_data.inputPlaceholder,
                'shouldWait': step_data.shouldWait,
                'waitMessage': step_data.waitMessage,
                'maxWaitTime': step_data.maxWaitTime,
                'description': step_data.description,
                'textLabels': step_data.textLabels,
                'contextText': step_data.contextText,
                'embedding': step_embedding,
                'successRate': step_data.successRate
            })

            print(f"  Step {order}: {step_data.action} - {step_data.description}")

            # 3. 첫 번째 STEP: ROOT-[HAS_STEP]->STEP 관계 생성
            if order == 0:
                create_root_step_rel = """
                MATCH (r:ROOT {domain: $domain})
                MATCH (s:STEP {stepId: $stepId})
                MERGE (r)-[rel:HAS_STEP]->(s)
                SET rel.weight = coalesce(rel.weight, 0) + 1,
                    rel.order = $order,
                    rel.taskIntent = $taskIntent,
                    rel.intentEmbedding = $intentEmbedding,
                    rel.createdAt = coalesce(rel.createdAt, datetime()),
                    rel.lastUpdated = datetime()
                """

                graph.query(create_root_step_rel, {
                    'domain': domain,
                    'stepId': step_id,
                    'order': order,
                    'taskIntent': task_intent,
                    'intentEmbedding': intent_embedding
                })

                print(f"  ✓ HAS_STEP 관계 생성: {domain} -> {step_data.description}")

            # 4. STEP-[NEXT_STEP]->STEP 관계 생성
            if previous_step_id:
                create_next_step_rel = """
                MATCH (s1:STEP {stepId: $fromStepId})
                MATCH (s2:STEP {stepId: $toStepId})
                MERGE (s1)-[r:NEXT_STEP]->(s2)
                SET r.weight = coalesce(r.weight, 0) + 1,
                    r.sequenceOrder = $sequenceOrder,
                    r.pathId = $pathId,
                    r.createdAt = coalesce(r.createdAt, datetime()),
                    r.lastUpdated = datetime()
                """

                graph.query(create_next_step_rel, {
                    'fromStepId': previous_step_id,
                    'toStepId': step_id,
                    'sequenceOrder': order,
                    'pathId': path_submission.sessionId
                })

            previous_step_id = step_id

        print(f"\n✅ 경로 저장 완료: {task_intent} ({len(path_submission.steps)} 단계)")

        return {
            'status': 'success',
            'domain': domain,
            'taskIntent': task_intent,
            'steps_saved': len(path_submission.steps)
        }

    except Exception as e:
        print(f"❌ 경로 저장 실패: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'message': str(e)}


def search_paths_by_query(
    query_text: str,
    limit: int = 3,
    domain_hint: Optional[str] = None
):
    """
    자연어 쿼리로 경로 검색

    검색 전략:
    1. taskIntent 임베딩 검색 (HAS_STEP 관계)
    2. Python에서 코사인 유사도 계산
    3. 경로 재구성 및 반환

    Args:
        query_text: 사용자 자연어 쿼리 (예: "날씨 보여줘")
        limit: 최대 반환 경로 수
        domain_hint: 특정 도메인으로 제한 (선택사항)

    Returns:
        dict: {'query', 'total_matched', 'matched_paths', 'performance'}
    """
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")

    start_time = time.time()

    try:
        # 1. 쿼리 임베딩 생성
        query_embedding = generate_embedding(query_text)

        # 2. taskIntent 임베딩 검색
        if domain_hint:
            intent_search_query = """
            MATCH (r:ROOT {domain: $domain})-[rel:HAS_STEP]->(firstStep:STEP)
            WHERE rel.intentEmbedding IS NOT NULL
            RETURN r, rel, firstStep
            """
            all_intents = graph.query(intent_search_query, {'domain': domain_hint})
        else:
            intent_search_query = """
            MATCH (r:ROOT)-[rel:HAS_STEP]->(firstStep:STEP)
            WHERE rel.intentEmbedding IS NOT NULL
            RETURN r, rel, firstStep
            """
            all_intents = graph.query(intent_search_query)

        # 3. Python에서 코사인 유사도 계산
        import numpy as np

        def cosine_similarity(vec1, vec2):
            vec1, vec2 = np.array(vec1), np.array(vec2)
            if vec1.shape != vec2.shape:
                return 0.0
            dot = np.dot(vec1, vec2)
            norm1, norm2 = np.linalg.norm(vec1), np.linalg.norm(vec2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return dot / (norm1 * norm2)

        intent_results = []
        for item in all_intents:
            rel = item['rel']
            intent_embedding = rel.get('intentEmbedding')
            if intent_embedding:
                similarity = cosine_similarity(query_embedding, intent_embedding)
                if similarity > 0.3:  # 임계값
                    intent_results.append({
                        'root': item['r'],
                        'relation': rel,
                        'firstStep': item['firstStep'],
                        'similarity': similarity
                    })

        # 유사도 순 정렬
        intent_results = sorted(intent_results, key=lambda x: x['similarity'], reverse=True)[:limit]

        # 4. 경로 재구성
        matched_paths = []
        for result in intent_results:
            first_step_id = result['firstStep']['stepId']

            # 경로 추적 (NEXT_STEP 관계 따라가기)
            path_query = """
            MATCH path = (start:STEP {stepId: $startStepId})-[:NEXT_STEP*0..20]->(end:STEP)
            WHERE NOT (end)-[:NEXT_STEP]->()
            WITH path, relationships(path) as rels
            RETURN [node in nodes(path) | node] as steps,
                   [rel in rels | rel.sequenceOrder] as orders
            LIMIT 1
            """

            path_data = graph.query(path_query, {'startStepId': first_step_id})

            if path_data:
                steps_list = path_data[0]['steps']

                formatted_steps = []
                for i, step_node in enumerate(steps_list):
                    formatted_steps.append({
                        'order': i,
                        'url': step_node['url'],
                        'action': step_node['action'],
                        'selectors': step_node.get('selectors', []),
                        'description': step_node.get('description', ''),
                        'isInput': step_node.get('isInput', False),
                        'inputType': step_node.get('inputType'),
                        'inputPlaceholder': step_node.get('inputPlaceholder'),
                        'shouldWait': step_node.get('shouldWait', False),
                        'waitMessage': step_node.get('waitMessage'),
                        'textLabels': step_node.get('textLabels', [])
                    })

                matched_paths.append({
                    'domain': result['root']['domain'],
                    'taskIntent': result['relation']['taskIntent'],
                    'relevance_score': round(result['similarity'], 3),
                    'weight': result['relation'].get('weight', 1),
                    'steps': formatted_steps
                })

        search_time_ms = int((time.time() - start_time) * 1000)

        print(f"\n🔍 검색 완료: '{query_text}' → {len(matched_paths)}개 경로 발견 ({search_time_ms}ms)")

        return {
            'query': query_text,
            'total_matched': len(matched_paths),
            'matched_paths': matched_paths,
            'performance': {
                'search_time': search_time_ms
            }
        }

    except Exception as e:
        print(f"❌ 경로 검색 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# 인덱스 및 제약 조건 관리
# ============================================================================

def create_vector_indexes():
    """
    새로운 DB 구조에 필요한 인덱스 생성
    """
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")

    print("인덱스 생성 중...")

    try:
        # 고유성 제약
        graph.query("""
            CREATE CONSTRAINT root_domain_unique IF NOT EXISTS
            FOR (r:ROOT) REQUIRE r.domain IS UNIQUE
        """)
        print("  ✓ ROOT.domain 고유 제약 생성")

        graph.query("""
            CREATE CONSTRAINT step_id_unique IF NOT EXISTS
            FOR (s:STEP) REQUIRE s.stepId IS UNIQUE
        """)
        print("  ✓ STEP.stepId 고유 제약 생성")

        # 일반 인덱스
        graph.query("""
            CREATE INDEX step_domain_idx IF NOT EXISTS
            FOR (s:STEP) ON (s.domain)
        """)
        print("  ✓ STEP.domain 인덱스 생성")

        graph.query("""
            CREATE INDEX step_action_idx IF NOT EXISTS
            FOR (s:STEP) ON (s.action)
        """)
        print("  ✓ STEP.action 인덱스 생성")

        # 벡터 인덱스는 Neo4j 5.x에서 지원
        try:
            graph.query("""
                CREATE VECTOR INDEX root_embedding IF NOT EXISTS
                FOR (r:ROOT) ON (r.embedding)
                OPTIONS {indexConfig: {
                  `vector.dimensions`: 1536,
                  `vector.similarity_function`: 'cosine'
                }}
            """)
            print("  ✓ ROOT.embedding 벡터 인덱스 생성")
        except Exception as e:
            print(f"  ⚠ ROOT 벡터 인덱스 생성 실패 (Neo4j 5.x 이상 필요): {e}")

        try:
            graph.query("""
                CREATE VECTOR INDEX step_embedding IF NOT EXISTS
                FOR (s:STEP) ON (s.embedding)
                OPTIONS {indexConfig: {
                  `vector.dimensions`: 1536,
                  `vector.similarity_function`: 'cosine'
                }}
            """)
            print("  ✓ STEP.embedding 벡터 인덱스 생성")
        except Exception as e:
            print(f"  ⚠ STEP 벡터 인덱스 생성 실패: {e}")

        # 전문 검색 인덱스
        try:
            graph.query("""
                CREATE FULLTEXT INDEX step_text_search IF NOT EXISTS
                FOR (s:STEP) ON EACH [s.description, s.textLabels]
            """)
            print("  ✓ STEP 전문 검색 인덱스 생성")
        except Exception as e:
            print(f"  ⚠ 전문 검색 인덱스 생성 실패: {e}")

        print("\n✅ 인덱스 생성 완료!")
        return True

    except Exception as e:
        print(f"❌ 인덱스 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 그래프 구조 확인 및 통계
# ============================================================================

def check_graph_structure():
    """
    그래프 구조 확인 및 통계 반환
    """
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")

    try:
        stats_query = """
        MATCH (r:ROOT)
        WITH count(r) as rootCount
        MATCH (s:STEP)
        WITH rootCount, count(s) as stepCount
        MATCH ()-[hs:HAS_STEP]->()
        WITH rootCount, stepCount, count(hs) as hasStepCount
        MATCH ()-[ns:NEXT_STEP]->()
        RETURN rootCount, stepCount, hasStepCount, count(ns) as nextStepCount
        """

        result = graph.query(stats_query)

        if result:
            stats = result[0]
            return {
                'ROOT_nodes': stats.get('rootCount', 0),
                'STEP_nodes': stats.get('stepCount', 0),
                'HAS_STEP_relations': stats.get('hasStepCount', 0),
                'NEXT_STEP_relations': stats.get('nextStepCount', 0),
                'structure': 'ROOT -> [HAS_STEP] -> STEP -> [NEXT_STEP] -> STEP'
            }
        else:
            return {
                'ROOT_nodes': 0,
                'STEP_nodes': 0,
                'HAS_STEP_relations': 0,
                'NEXT_STEP_relations': 0,
                'structure': 'Empty graph'
            }

    except Exception as e:
        print(f"그래프 구조 확인 실패: {e}")
        return {'error': str(e)}


def visualize_paths(domain: str):
    """
    특정 도메인의 모든 경로 시각화
    """
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")

    try:
        query = """
        MATCH (r:ROOT {domain: $domain})-[hs:HAS_STEP]->(firstStep:STEP)
        OPTIONAL MATCH path = (firstStep)-[:NEXT_STEP*0..10]->(lastStep:STEP)
        WHERE NOT (lastStep)-[:NEXT_STEP]->()
        RETURN hs.taskIntent as taskIntent,
               hs.weight as weight,
               [node in nodes(path) | node.description] as steps,
               length(path) as pathLength
        ORDER BY hs.weight DESC
        LIMIT 10
        """

        results = graph.query(query, {'domain': domain})

        paths = []
        for result in results:
            paths.append({
                'taskIntent': result['taskIntent'],
                'weight': result['weight'],
                'steps': result['steps'],
                'pathLength': result['pathLength']
            })

        return paths

    except Exception as e:
        print(f"경로 시각화 실패: {e}")
        return []


def find_popular_paths(domain: Optional[str] = None, limit: int = 10):
    """
    인기 있는 경로 찾기 (사용 빈도 기준)
    """
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")

    try:
        if domain:
            query = """
            MATCH (r:ROOT {domain: $domain})-[hs:HAS_STEP]->(s:STEP)
            RETURN r.domain as domain,
                   hs.taskIntent as taskIntent,
                   hs.weight as usageCount,
                   s.description as firstStepDescription
            ORDER BY hs.weight DESC
            LIMIT $limit
            """
            results = graph.query(query, {'domain': domain, 'limit': limit})
        else:
            query = """
            MATCH (r:ROOT)-[hs:HAS_STEP]->(s:STEP)
            RETURN r.domain as domain,
                   hs.taskIntent as taskIntent,
                   hs.weight as usageCount,
                   s.description as firstStepDescription
            ORDER BY hs.weight DESC
            LIMIT $limit
            """
            results = graph.query(query, {'limit': limit})

        popular_paths = []
        for result in results:
            popular_paths.append({
                'domain': result['domain'],
                'taskIntent': result['taskIntent'],
                'usageCount': result['usageCount'],
                'firstStepDescription': result['firstStepDescription']
            })

        return popular_paths

    except Exception as e:
        print(f"인기 경로 조회 실패: {e}")
        return []


def cleanup_old_paths(days: int = 30):
    """
    오래된 경로 정리 (사용되지 않은 지 N일 이상)
    """
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")

    try:
        query = """
        MATCH ()-[ns:NEXT_STEP]->()
        WHERE duration.between(ns.lastUpdated, datetime()).days > $days
        WITH ns, count(*) as oldCount
        DELETE ns
        RETURN oldCount
        """

        result = graph.query(query, {'days': days})

        if result:
            return {'deleted_relations': result[0].get('oldCount', 0)}
        else:
            return {'deleted_relations': 0}

    except Exception as e:
        print(f"경로 정리 실패: {e}")
        return {'error': str(e)}
