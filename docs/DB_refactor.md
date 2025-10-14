# Neo4j 데이터베이스 리팩토링 계획서

## 📋 목차
1. [현재 데이터베이스 구조 분석](#1-현재-데이터베이스-구조-분석)
2. [문제점 및 개선 방향](#2-문제점-및-개선-방향)
3. [새로운 데이터베이스 구조 설계](#3-새로운-데이터베이스-구조-설계)
4. [vowser-mcp-server 코드 수정 사항](#4-vowser-mcp-server-코드-수정-사항)
5. [vowser-client 코드 수정 사항](#5-vowser-client-코드-수정-사항)
6. [마이그레이션 계획](#6-마이그레이션-계획)
7. [테스트 전략](#7-테스트-전략)

---

## 1. 현재 데이터베이스 구조 분석

### 1.1 현재 노드 타입

#### **ROOT 노드**
- **용도**: 도메인 루트 (예: youtube.com, naver.com)
- **속성**:
  - `domain`: 도메인 이름
  - `baseURL`: 기본 URL
  - `lastVisited`: 마지막 방문 시간

#### **PAGE 노드**
- **용도**: 클릭 가능한 UI 요소 및 페이지
- **속성**:
  - `pageId`: 고유 ID (MD5 해시)
  - `url`: 페이지 URL
  - `domain`: 도메인
  - `primarySelector`: CSS 셀렉터
  - `fallbackSelectors`: 대체 셀렉터 배열
  - `anchorPoint`: 앵커 포인트
  - `relativePathFromAnchor`: 앵커로부터의 상대 경로
  - `elementSnapshot`: 요소 스냅샷 (JSON)
  - `textLabels`: 텍스트 라벨 배열
  - `contextText`: 컨텍스트 텍스트 (JSON)
  - `actionType`: 액션 타입 (click, input 등)
  - `embedding`: 벡터 임베딩 (1536 차원)
  - `lastUpdated`: 마지막 업데이트 시간

#### **PATH 노드**
- **용도**: 완전한 탐색 경로
- **속성**:
  - `pathId`: 경로 ID
  - `description`: 경로 설명
  - `nodeSequence`: 노드 시퀀스 배열
  - `startDomain`: 시작 도메인
  - `targetPageId`: 목표 페이지 ID
  - `embedding`: 경로 임베딩
  - `startCommand`: 시작 명령어
  - `startUrl`: 시작 URL
  - `totalWeight`: 총 가중치
  - `usageCount`: 사용 횟수
  - `createdAt`: 생성 시간
  - `lastUsed`: 마지막 사용 시간

#### **PAGE_ANALYSIS, SECTION, ELEMENT 노드**
- **용도**: 페이지 구조 분석 결과 저장
- 현재 사용되고 있지 않은 것으로 보임

### 1.2 현재 관계 타입

- **HAS_PAGE**: ROOT → PAGE (도메인이 페이지를 포함)
- **NAVIGATES_TO**: PAGE → PAGE (같은 도메인 내 페이지 이동)
- **NAVIGATES_TO_CROSS_DOMAIN**: PAGE → PAGE (도메인 간 이동)
- **CONTAINS**: PATH → PAGE (경로가 페이지를 포함)
- **HAS_ANALYSIS**: ROOT → PAGE_ANALYSIS
- **HAS_SECTION**: PAGE_ANALYSIS → SECTION
- **HAS_ELEMENT**: SECTION → ELEMENT

### 1.3 현재 구조의 특징

- ROOT 노드는 도메인 정보만 포함
- 실제 웹 탐색 경로는 PAGE 노드들의 연결로 표현
- PATH 노드는 메타데이터 성격으로 별도 저장
- 벡터 임베딩을 통한 의미 검색 지원

---

## 2. 문제점 및 개선 방향

### 2.1 현재 구조의 문제점

#### **문제 1: 의도 기반 검색의 어려움**
```
사용자 입력: "오늘의 날씨 알려줘"
현재 문제:
- PAGE 노드는 UI 요소 중심으로 설계됨
- "날씨"라는 의도를 직접 표현하는 노드가 없음
- 벡터 검색으로만 의도를 유추해야 함
```

#### **문제 2: 경로 표현의 이중성**
- PAGE 노드 간 관계로 경로 표현
- PATH 노드로 경로 메타데이터 중복 저장
- 두 구조 간 동기화 필요

#### **문제 3: 사용자 액션 정보 부족**
- 입력 필드 타입 (email, password 등) 미지원
- 대기 상태 및 안내 문구 미지원
- 조건부 액션 처리 어려움

### 2.2 개선 방향

1. **의도 중심 구조로 전환**
   - 사용자 의도를 직접 표현하는 노드 추가
   - "날씨 보기", "뉴스 읽기" 등의 태스크를 1급 객체로

2. **단순화된 경로 표현**
   - ROOT → STEP → STEP → ... 의 선형 구조
   - PATH 노드 제거, STEP 노드로 통합

3. **풍부한 액션 정보**
   - 입력 타입, 대기 상태, 안내 문구 등 추가
   - 사용자 경험 향상을 위한 메타데이터

---

## 3. 새로운 데이터베이스 구조 설계

### 3.1 새로운 노드 타입

#### **ROOT 노드**
```cypher
(r:ROOT {
  domain: string,              // 예: "naver.com"
  baseURL: string,             // 예: "https://naver.com"
  displayName: string,         // 예: "네이버"
  keywords: [string],          // ["네이버", "포털", "검색"]
  lastVisited: datetime,
  visitCount: int,
  embedding: [float]           // 도메인 이름 + 키워드 임베딩
})
```

**역할**: 도메인 정보와 메타데이터 저장

#### **STEP 노드** (새로 추가, 기존 PAGE 개념 확장)
```cypher
(s:STEP {
  stepId: string,              // 고유 ID
  url: string,                 // 이동할 URL
  domain: string,              // 도메인

  // 선택자 정보
  selectors: [string],         // [primarySelector, fallbackSelector1, ...]
  anchorPoint: string,         // 앵커 포인트
  relativePathFromAnchor: string,

  // 사용자 액션 정보
  action: string,              // "click" | "input" | "wait"

  // 입력 관련 (action = "input"일 때)
  isInput: boolean,
  inputType: string,           // "email" | "id" | "password" | "search" | "text"
  inputPlaceholder: string,    // 사용자에게 보여줄 입력 안내

  // 대기 관련 (action = "wait"일 때)
  shouldWait: boolean,
  waitMessage: string,         // "카카오 간편인증을 기다리고 있습니다"
  maxWaitTime: int,            // 최대 대기 시간 (초)

  // 시맨틱 정보
  description: string,         // "로그인 버튼 클릭"
  textLabels: [string],        // 요소의 텍스트들
  contextText: string,         // 주변 텍스트

  // 임베딩
  embedding: [float],          // 시맨틱 정보의 임베딩

  // 메타데이터
  createdAt: datetime,
  lastUsed: datetime,
  usageCount: int,
  successRate: float           // 0.0 ~ 1.0
})
```

**핵심 개선점**:
- `action` 필드로 액션 타입 명확히 구분 (navigate 제거 - DOMAIN.baseURL이 시작점 처리)
- `inputType`으로 다양한 입력 필드 지원
- `waitMessage`로 사용자에게 상황 안내
- 셀렉터를 배열로 통합 (primary + fallbacks)
- 페이지 이동은 click 액션의 결과로 자연스럽게 표현

### 3.2 새로운 관계 타입

#### **HAS_STEP** (ROOT → STEP)
```cypher
(r:ROOT)-[rel:HAS_STEP]->(s:STEP)

Properties:
  weight: int,                 // 사용 빈도
  order: int,                  // 도메인 내 단계 순서 (0부터 시작)
  taskIntent: string,          // "날씨 보기", "로그인" 등
  intentEmbedding: [float],    // 태스크 의도의 임베딩
  createdAt: datetime,
  lastUpdated: datetime
```

**핵심**:
- `taskIntent` 필드로 사용자 의도 직접 표현
- "오늘의 날씨 알려줘" → taskIntent = "날씨 보기"와 매칭

#### **NEXT_STEP** (STEP → STEP)
```cypher
(s1:STEP)-[r:NEXT_STEP]->(s2:STEP)

Properties:
  pathId: string,              // 어느 경로의 일부인지
  sequenceOrder: int,          // 경로 내 순서
  weight: int,                 // 이 연결의 사용 빈도
  avgTransitionTime: float,    // 평균 전환 시간 (초)
  createdAt: datetime,
  lastUpdated: datetime
```

**핵심**:
- 순차적 경로 표현
- 여러 경로에서 같은 STEP 재사용 가능

### 3.3 새로운 그래프 구조 예시

```
사용자: "네이버 날씨 보여줘"

(ROOT {domain: "naver.com", baseURL: "https://naver.com"})
  -[HAS_STEP {taskIntent: "날씨 보기", order: 0}]->
    (STEP {
      action: "click",
      url: "https://naver.com",
      selectors: ["#main_weather", ".weather_area"],
      description: "날씨 위젯 클릭",
      textLabels: ["날씨", "오늘의 날씨"]
    })

# 주의: 첫 번째 STEP은 이미 naver.com에 접속한 상태에서 시작
# ROOT.baseURL로 자동 시작하므로 navigate STEP 불필요
```

```
사용자: "네이버 로그인해줘"

(ROOT {domain: "naver.com", baseURL: "https://nid.naver.com/nidlogin.login"})
  -[HAS_STEP {taskIntent: "로그인", order: 0}]->
    (STEP {
      action: "input",
      url: "https://nid.naver.com/nidlogin.login",
      isInput: true,
      inputType: "id",
      selectors: ["#id"],
      inputPlaceholder: "네이버 아이디를 입력하세요",
      description: "아이디 입력"
    })
      -[NEXT_STEP {sequenceOrder: 1}]->
        (STEP {
          action: "input",
          url: "https://nid.naver.com/nidlogin.login",
          isInput: true,
          inputType: "password",
          selectors: ["#pw"],
          inputPlaceholder: "비밀번호를 입력하세요",
          description: "비밀번호 입력"
        })
      -[NEXT_STEP {sequenceOrder: 2}]->
        (STEP {
          action: "click",
          url: "https://nid.naver.com/nidlogin.login",
          selectors: ["#log_in_btn", ".btn_login"],
          description: "로그인 버튼 클릭"
        })
      -[NEXT_STEP {sequenceOrder: 3}]->
        (STEP {
          action: "wait",
          url: "https://nid.naver.com/nidlogin.login",
          shouldWait: true,
          waitMessage: "카카오 간편인증을 기다리고 있습니다",
          maxWaitTime: 30,
          description: "2단계 인증 대기"
        })

# 주의: 로그인 페이지로 바로 시작하려면 ROOT.baseURL을 로그인 페이지로 설정
# 클릭으로 페이지 이동이 발생하면 STEP.url이 자동으로 업데이트됨
```

### 3.4 인덱스 전략

```cypher
-- 고유성 제약
CREATE CONSTRAINT root_domain_unique IF NOT EXISTS
FOR (r:ROOT) REQUIRE r.domain IS UNIQUE;

CREATE CONSTRAINT step_id_unique IF NOT EXISTS
FOR (s:STEP) REQUIRE s.stepId IS UNIQUE;

-- 일반 인덱스
CREATE INDEX step_domain_idx IF NOT EXISTS
FOR (s:STEP) ON (s.domain);

CREATE INDEX step_action_idx IF NOT EXISTS
FOR (s:STEP) ON (s.action);

-- 벡터 인덱스
CREATE VECTOR INDEX root_embedding IF NOT EXISTS
FOR (r:ROOT) ON (r.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};

CREATE VECTOR INDEX step_embedding IF NOT EXISTS
FOR (s:STEP) ON (s.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};

CREATE VECTOR INDEX intent_embedding IF NOT EXISTS
FOR ()-[r:HAS_STEP]-() ON (r.intentEmbedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};

-- 전문 검색 인덱스
CREATE FULLTEXT INDEX step_text_search IF NOT EXISTS
FOR (s:STEP) ON EACH [s.description, s.textLabels];
```

---

## 4. vowser-mcp-server 코드 수정 사항

### 4.1 파일 구조 변경

#### 새로 생성할 파일
```
app/
  models/
    path.py                    # 기존 유지, 일부 수정
    step.py                    # 새로 생성 - STEP 모델
    domain.py                  # 새로 생성 - DOMAIN 모델
  services/
    neo4j_service.py           # 대폭 수정
    embedding_service.py       # 기존 유지
    path_service.py            # 새로 생성 - 경로 저장/검색 전용
```

### 4.2 app/models/step.py (새로 생성)

```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class StepData(BaseModel):
    """단일 STEP 노드 데이터"""
    stepId: Optional[str] = None  # 자동 생성
    url: str
    domain: str

    # 선택자
    selectors: List[str]  # [primary, fallback1, fallback2, ...]
    anchorPoint: Optional[str] = None
    relativePathFromAnchor: Optional[str] = None

    # 액션
    action: str  # "click" | "input" | "wait"

    # 입력 관련
    isInput: bool = False
    inputType: Optional[str] = None  # "email" | "id" | "password" | "search" | "text"
    inputPlaceholder: Optional[str] = None

    # 대기 관련
    shouldWait: bool = False
    waitMessage: Optional[str] = None
    maxWaitTime: Optional[int] = None

    # 시맨틱 정보
    description: str
    textLabels: List[str] = []
    contextText: Optional[str] = None

    # 메타데이터
    successRate: float = 1.0

class PathSubmission(BaseModel):
    """사용자가 제출하는 완전한 경로 데이터"""
    sessionId: str
    taskIntent: str  # "날씨 보기", "로그인" 등
    domain: str
    steps: List[StepData]
```

### 4.3 app/models/root.py (새로 생성)

```python
from pydantic import BaseModel
from typing import List

class RootData(BaseModel):
    """ROOT 노드 데이터"""
    domain: str
    baseURL: str
    displayName: str
    keywords: List[str] = []
```

### 4.4 app/services/neo4j_service.py 주요 수정 함수

#### **함수 1: save_path_to_neo4j 완전 재작성**

**기존 코드 위치**: neo4j_service.py:91-231

**새로운 코드**:
```python
def save_path_to_neo4j(path_submission: PathSubmission):
    """
    새로운 구조로 경로 저장

    구조:
    (ROOT)-[HAS_STEP {taskIntent}]->(STEP)-[NEXT_STEP]->(STEP)->...
    """
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")

    try:
        # 1. ROOT 노드 생성/업데이트
        domain = path_submission.domain
        domain_embedding = generate_embedding(f"{domain} {path_submission.taskIntent}")

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
            d.lastVisited = datetime()
        RETURN d
        """

        graph.query(create_domain_query, {
            'domain': domain,
            'baseURL': f"https://{domain}",
            'displayName': domain.replace('.com', '').replace('.', ' '),
            'embedding': domain_embedding
        })

        # 2. 각 STEP 노드 생성
        previous_step_id = None
        intent_embedding = generate_embedding(path_submission.taskIntent)

        for order, step_data in enumerate(path_submission.steps):
            # STEP ID 생성
            step_id = create_step_id(step_data.url, step_data.selectors, step_data.action)

            # STEP 임베딩 생성
            embedding_text = f"{step_data.description} {' '.join(step_data.textLabels)} {step_data.contextText or ''}"
            step_embedding = generate_embedding(embedding_text)

            # STEP 노드 생성
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

            # 3. ROOT-[HAS_STEP]->첫번째 STEP 관계 생성
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

                graph.query(create_domain_step_rel, {
                    'domain': domain,
                    'stepId': step_id,
                    'order': order,
                    'taskIntent': path_submission.taskIntent,
                    'intentEmbedding': intent_embedding
                })

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

        return {
            'status': 'success',
            'domain': domain,
            'taskIntent': path_submission.taskIntent,
            'steps_saved': len(path_submission.steps)
        }

    except Exception as e:
        print(f"경로 저장 실패: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'message': str(e)}

def create_step_id(url: str, selectors: List[str], action: str) -> str:
    """STEP ID 생성"""
    import hashlib
    key = f"{url}_{selectors[0] if selectors else 'nav'}_{action}"
    return hashlib.md5(key.encode()).hexdigest()
```

#### **함수 2: search_paths_by_query 수정**

**기존 코드 위치**: neo4j_service.py:683-923

**새로운 코드**:
```python
def search_paths_by_query(query_text: str, limit: int = 3, domain_hint: Optional[str] = None):
    """
    자연어 쿼리로 경로 검색 (새 구조)

    검색 전략:
    1. taskIntent 임베딩 검색 (HAS_STEP 관계)
    2. STEP 임베딩 검색
    3. 경로 재구성 및 반환
    """
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")

    import time
    start_time = time.time()

    try:
        # 쿼리 임베딩 생성
        query_embedding = generate_embedding(query_text)

        # 1. taskIntent 임베딩 검색
        # Neo4j 5.x에서는 벡터 검색을 Python에서 수행
        intent_search_query = """
        MATCH (r:ROOT)-[rel:HAS_STEP]->(firstStep:STEP)
        WHERE rel.intentEmbedding IS NOT NULL
        RETURN r, rel, firstStep
        """

        if domain_hint:
            intent_search_query = f"""
            MATCH (r:ROOT {{domain: '{domain_hint}'}})-[rel:HAS_STEP]->(firstStep:STEP)
            WHERE rel.intentEmbedding IS NOT NULL
            RETURN r, rel, firstStep
            """

        all_intents = graph.query(intent_search_query)

        # Python에서 코사인 유사도 계산
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
            rel = item['r']
            intent_embedding = rel.get('intentEmbedding')
            if intent_embedding:
                similarity = cosine_similarity(query_embedding, intent_embedding)
                if similarity > 0.3:  # 임계값
                    intent_results.append({
                        'domain': item['d'],
                        'relation': rel,
                        'firstStep': item['firstStep'],
                        'similarity': similarity
                    })

        # 유사도 순 정렬
        intent_results = sorted(intent_results, key=lambda x: x['similarity'], reverse=True)[:limit]

        # 2. 경로 재구성
        matched_paths = []
        for result in intent_results:
            first_step_id = result['firstStep']['stepId']

            # 경로 추적 (NEXT_STEP 관계 따라가기)
            path_query = """
            MATCH path = (start:STEP {stepId: $startStepId})-[:NEXT_STEP*0..10]->(end:STEP)
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
                    'domain': result['domain']['domain'],
                    'taskIntent': result['relation']['taskIntent'],
                    'relevance_score': round(result['similarity'], 3),
                    'weight': result['relation'].get('weight', 1),
                    'steps': formatted_steps
                })

        search_time_ms = int((time.time() - start_time) * 1000)

        return {
            'query': query_text,
            'total_matched': len(matched_paths),
            'matched_paths': matched_paths,
            'performance': {
                'search_time': search_time_ms
            }
        }

    except Exception as e:
        print(f"경로 검색 실패: {e}")
        import traceback
        traceback.print_exc()
        return None
```

#### **함수 3: 기타 수정 필요 함수**

```python
# 삭제할 함수들
- create_page_id()  # STEP ID 생성으로 대체
- create_path_entity()  # PATH 노드 제거로 불필요
- reconstruct_path_from_sequence()  # 구조 변경으로 불필요

# 수정할 함수들
- check_graph_structure()  # ROOT→DOMAIN, PAGE→STEP으로 변경
- visualize_paths()  # 새 구조에 맞게 Cypher 쿼리 수정
- find_popular_paths()  # HAS_STEP 관계의 weight 기준으로 수정
- cleanup_old_paths()  # STEP 노드 기준으로 수정
```

### 4.5 app/main.py 수정

**수정 위치**: main.py:33-47

**변경 사항**:
```python
# 기존
if message['type'] == 'save_path':
    path_data = PathData(**message['data'])
    path_with_metadata = neo4j_service.add_metadata_to_path(path_data.model_dump())
    result = neo4j_service.save_path_to_neo4j(path_with_metadata)

# 새로운 코드
if message['type'] == 'save_path':
    from app.models.step import PathSubmission
    path_submission = PathSubmission(**message['data'])
    result = neo4j_service.save_path_to_neo4j(path_submission)
```

---

## 5. vowser-client 코드 수정 사항

### 5.1 현재 클라이언트 구조 분석

**vowser-client**는 Kotlin Multiplatform 프로젝트로:
- 자체 그래프 시각화 시스템 보유
- `WebNavigationGraph` 클래스로 로컬 그래프 관리
- Neo4j와 직접 통신하지 않음 (vowser-backend를 통해 간접 통신)

### 5.2 수정이 필요한 파일

#### **파일 1: WebNavigationData.kt**

**위치**: `shared/src/commonMain/kotlin/com/vowser/client/data/WebNavigationData.kt`

**현재 상태**:
- 로컬 시각화용 더미 데이터
- WebNodeType: ROOT, WEBSITE, CATEGORY, CONTENT

**변경 필요 여부**: ⚠️ **선택적**

클라이언트는 백엔드와 독립적인 시각화 구조를 사용 중이므로, Neo4j 구조 변경이 클라이언트에 직접적인 영향을 주지 않습니다. 다만, 백엔드 응답 형식이 변경되면 클라이언트의 데이터 파싱 로직을 수정해야 합니다.

#### **파일 2: ContributionModels.kt**

**위치**: `shared/src/commonMain/kotlin/com/vowser/client/contribution/ContributionModels.kt`

**현재 구조**:
```kotlin
@Serializable
data class ContributionStep(
    val url: String,
    val title: String,
    val action: String,
    val selector: String?,
    val htmlAttributes: Map<String, String>?,
    val timestamp: Long
)
```

**새로운 구조** (Neo4j 구조와 일치):
```kotlin
@Serializable
data class ContributionStep(
    val url: String,
    val domain: String,

    // 선택자
    val selectors: List<String>,  // [primary, fallback1, ...]
    val anchorPoint: String? = null,
    val relativePathFromAnchor: String? = null,

    // 액션
    val action: String,  // "click" | "input" | "wait"

    // 입력 관련
    val isInput: Boolean = false,
    val inputType: String? = null,  // "email" | "id" | "password" | "search" | "text"
    val inputPlaceholder: String? = null,

    // 대기 관련
    val shouldWait: Boolean = false,
    val waitMessage: String? = null,
    val maxWaitTime: Int? = null,

    // 시맨틱 정보
    val description: String,
    val textLabels: List<String> = emptyList(),
    val contextText: String? = null,

    val timestamp: Long = Clock.System.now().toEpochMilliseconds()
)

@Serializable
data class ContributionSession(
    val sessionId: String = uuid4().toString(),
    val taskIntent: String,  // "날씨 보기", "로그인" 등 - 새로 추가
    val domain: String,      // 새로 추가
    val steps: MutableList<ContributionStep> = mutableListOf(),
    val startTime: Long = Clock.System.now().toEpochMilliseconds(),
    var isActive: Boolean = true
)
```

**변경 이유**:
- 서버의 `PathSubmission` 모델과 1:1 매칭
- 새로운 액션 타입 지원 (input, wait)
- taskIntent 필드로 사용자 의도 명시

### 5.3 백엔드 응답 파싱 로직 수정

만약 vowser-client가 백엔드로부터 검색 결과를 받아 표시하는 기능이 있다면, 응답 형식 변경에 맞춰 수정 필요:

**예상 응답 형식**:
```json
{
  "type": "search_path_result",
  "status": "success",
  "data": {
    "query": "날씨 보기",
    "total_matched": 2,
    "matched_paths": [
      {
        "domain": "naver.com",
        "taskIntent": "날씨 보기",
        "relevance_score": 0.95,
        "weight": 10,
        "steps": [
          {
            "order": 0,
            "url": "https://naver.com",
            "action": "click",
            "selectors": ["#main_weather", ".weather_area"],
            "description": "날씨 위젯 클릭",
            "textLabels": ["날씨", "오늘의 날씨"]
          }
        ]
      }
    ]
  }
}
```

---

## 6. 마이그레이션 계획

### 6.1 마이그레이션 전략

**Option A: 클린 마이그레이션 (권장)**
1. 기존 데이터베이스 백업
2. 새 스키마로 데이터베이스 초기화
3. 새 구조로 데이터 수집 시작

**Option B: 데이터 변환 마이그레이션**
1. 기존 PAGE → STEP 변환
2. 기존 PATH → HAS_STEP + NEXT_STEP 관계로 변환
3. ROOT → DOMAIN 변환

### 6.2 마이그레이션 스크립트 (Option B 선택 시)

```python
# app/services/migration_service.py

def migrate_database():
    """
    기존 구조를 새 구조로 마이그레이션
    """
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")

    print("마이그레이션 시작...")

    # 1. ROOT 노드 업데이트 (이미 ROOT이므로 속성만 추가)
    print("1. ROOT 노드 속성 업데이트 중...")
    update_root_nodes = """
    MATCH (r:ROOT)
    SET r = {
        domain: r.domain,
        baseURL: r.baseURL,
        displayName: r.domain,
        visitCount: 0,
        lastVisited: r.lastVisited
    })
    WITH r, d
    MATCH (r)-[rel:HAS_PAGE]->(p:PAGE)
    CREATE (d)-[:TEMP_HAS_PAGE {weight: rel.weight}]->(p)
    RETURN count(d) as migrated_domains
    """
    result = graph.query(migrate_root_to_domain)
    print(f"   → {result[0]['migrated_domains']}개 DOMAIN 생성")

    # 2. PAGE → STEP 변환
    print("2. PAGE 노드를 STEP 노드로 변환 중...")
    migrate_page_to_step = """
    MATCH (p:PAGE)
    CREATE (s:STEP {
        stepId: p.pageId,
        url: p.url,
        domain: p.domain,
        selectors: [p.primarySelector] + p.fallbackSelectors,
        anchorPoint: p.anchorPoint,
        relativePathFromAnchor: p.relativePathFromAnchor,
        action: p.actionType,
        isInput: false,
        shouldWait: false,
        description: p.textLabels[0],
        textLabels: p.textLabels,
        contextText: p.contextText,
        embedding: p.embedding,
        createdAt: datetime(),
        lastUsed: p.lastUpdated,
        usageCount: 1,
        successRate: 1.0
    })
    RETURN count(s) as migrated_steps
    """
    result = graph.query(migrate_page_to_step)
    print(f"   → {result[0]['migrated_steps']}개 STEP 생성")

    # 3. PATH 정보를 HAS_STEP + NEXT_STEP으로 변환
    print("3. PATH 노드를 관계로 변환 중...")
    migrate_path_to_relations = """
    MATCH (path:PATH)
    WITH path, path.nodeSequence as nodeSeq, path.startDomain as domain
    MATCH (r:ROOT {domain: domain})
    WITH path, r, nodeSeq
    UNWIND range(0, size(nodeSeq)-1) as idx
    WITH path, r, nodeSeq, idx,
         nodeSeq[idx] as currentNode,
         CASE WHEN idx < size(nodeSeq)-1 THEN nodeSeq[idx+1] ELSE null END as nextNode

    // 첫 STEP에 HAS_STEP 관계
    OPTIONAL MATCH (firstStep:STEP {stepId: replace(nodeSeq[1], 'page_', '')})
    WHERE idx = 0 AND firstStep IS NOT NULL
    MERGE (d)-[r:HAS_STEP]->(firstStep)
    SET r.weight = coalesce(r.weight, 0) + 1,
        r.order = 0,
        r.taskIntent = path.startCommand,
        r.createdAt = path.createdAt,
        r.lastUpdated = path.lastUsed

    // NEXT_STEP 관계
    WITH path, currentNode, nextNode, idx
    WHERE nextNode IS NOT NULL AND idx > 0
    MATCH (s1:STEP {stepId: replace(currentNode, 'page_', '')})
    MATCH (s2:STEP {stepId: replace(nextNode, 'page_', '')})
    MERGE (s1)-[r:NEXT_STEP]->(s2)
    SET r.weight = coalesce(r.weight, 0) + 1,
        r.sequenceOrder = idx,
        r.pathId = path.pathId

    RETURN count(DISTINCT path) as migrated_paths
    """
    result = graph.query(migrate_path_to_relations)
    print(f"   → {result[0]['migrated_paths']}개 경로 변환")

    # 4. 임시 관계 제거 및 기존 노드 삭제
    print("4. 기존 노드 및 임시 관계 정리 중...")
    cleanup = """
    MATCH ()-[r:TEMP_HAS_PAGE]->() DELETE r;
    MATCH (r:ROOT) DETACH DELETE r;
    MATCH (p:PAGE) DELETE p;
    MATCH (path:PATH) DETACH DELETE path;
    """
    graph.query(cleanup)
    print("   → 정리 완료")

    print("\n마이그레이션 완료!")

    # 5. 통계 확인
    stats = check_graph_structure()
    return stats
```

### 6.3 마이그레이션 실행 방법

```bash
# vowser-mcp-server 디렉토리에서
cd app/services
python migration_service.py
```

---

## 7. 테스트 전략

### 7.1 단위 테스트

#### **테스트 1: STEP 노드 생성**
```python
def test_create_step_node():
    step_data = StepData(
        url="https://naver.com",
        domain="naver.com",
        selectors=["#weather", ".weather-widget"],
        action="click",
        description="날씨 위젯 클릭",
        textLabels=["날씨", "오늘의 날씨"]
    )

    # 저장
    step_id = create_step_node(step_data)

    # 검증
    assert step_id is not None

    # DB에서 조회
    result = graph.query("MATCH (s:STEP {stepId: $id}) RETURN s", {'id': step_id})
    assert len(result) == 1
    assert result[0]['s']['action'] == 'click'
```

#### **테스트 2: 경로 저장**
```python
def test_save_complete_path():
    path = PathSubmission(
        sessionId="test-session-1",
        taskIntent="날씨 보기",
        domain="naver.com",
        steps=[
            StepData(
                url="https://naver.com",
                domain="naver.com",
                selectors=["#main_weather", ".weather_area"],
                action="click",
                description="날씨 위젯 클릭",
                textLabels=["날씨", "오늘의 날씨"]
            )
        ]
    )

    result = save_path_to_neo4j(path)

    assert result['status'] == 'success'
    assert result['steps_saved'] == 1
```

#### **테스트 3: 의도 기반 검색**
```python
def test_intent_based_search():
    # 경로 저장
    save_weather_path()  # "날씨 보기" 경로
    save_news_path()     # "뉴스 읽기" 경로

    # 검색
    result = search_paths_by_query("오늘 날씨 알려줘", limit=3)

    assert result['total_matched'] >= 1
    assert result['matched_paths'][0]['taskIntent'] == '날씨 보기'
    assert result['matched_paths'][0]['relevance_score'] > 0.7
```

### 7.2 통합 테스트

#### **테스트 4: WebSocket 통신 테스트**
```python
async def test_websocket_save_path():
    """
    클라이언트 → 서버 경로 저장 WebSocket 테스트
    """
    async with websockets.connect('ws://localhost:8000/ws') as ws:
        message = {
            'type': 'save_path',
            'data': {
                'sessionId': 'test-1',
                'taskIntent': '로그인',
                'domain': 'naver.com',
                'steps': [
                    {
                        'url': 'https://naver.com/login',
                        'domain': 'naver.com',
                        'selectors': ['#id'],
                        'action': 'input',
                        'isInput': True,
                        'inputType': 'id',
                        'inputPlaceholder': '아이디 입력',
                        'description': '아이디 입력 필드'
                    }
                ]
            }
        }

        await ws.send(json.dumps(message))
        response = await ws.recv()
        data = json.loads(response)

        assert data['status'] == 'success'
        assert data['type'] == 'path_save_result'
```

### 7.3 성능 테스트

#### **테스트 5: 벡터 검색 성능**
```python
def test_vector_search_performance():
    """
    1000개 경로 저장 후 검색 속도 테스트
    """
    # 1000개 더미 경로 생성
    for i in range(1000):
        save_dummy_path(f"태스크 {i}")

    # 검색 시간 측정
    import time
    start = time.time()
    result = search_paths_by_query("날씨 보기", limit=5)
    elapsed = time.time() - start

    assert elapsed < 1.0  # 1초 이내
    assert result['performance']['search_time'] < 1000  # 1000ms 이내
```

### 7.4 테스트 데이터 준비

```python
# test/fixtures/new_test_data.py

WEATHER_PATH = PathSubmission(
    sessionId="weather-1",
    taskIntent="날씨 보기",
    domain="naver.com",
    steps=[
        StepData(
            url="https://naver.com",
            domain="naver.com",
            selectors=["#main_weather", ".weather_area"],
            action="click",
            description="날씨 위젯 클릭",
            textLabels=["날씨", "오늘의 날씨", "기온"]
        )
    ]
)

LOGIN_PATH = PathSubmission(
    sessionId="login-1",
    taskIntent="로그인",
    domain="naver.com",
    steps=[
        StepData(
            url="https://nid.naver.com/nidlogin.login",
            domain="naver.com",
            selectors=["#id"],
            action="input",
            isInput=True,
            inputType="id",
            inputPlaceholder="네이버 아이디를 입력하세요",
            description="아이디 입력"
        ),
        StepData(
            url="https://nid.naver.com/nidlogin.login",
            domain="naver.com",
            selectors=["#pw"],
            action="input",
            isInput=True,
            inputType="password",
            inputPlaceholder="비밀번호를 입력하세요",
            description="비밀번호 입력"
        ),
        StepData(
            url="https://nid.naver.com/nidlogin.login",
            domain="naver.com",
            selectors=[".btn_login"],
            action="click",
            description="로그인 버튼 클릭"
        ),
        StepData(
            url="https://nid.naver.com/nidlogin.login",
            domain="naver.com",
            selectors=[],
            action="wait",
            shouldWait=True,
            waitMessage="카카오 간편인증을 기다리고 있습니다",
            maxWaitTime=30,
            description="2단계 인증 대기"
        )
    ]
)
```

---

## 8. 예상 작업 시간

| 작업 | 예상 시간 | 우선순위 |
|------|-----------|----------|
| DB 스키마 설계 검토 | 2시간 | 높음 |
| models/step.py, domain.py 작성 | 3시간 | 높음 |
| neo4j_service.py 수정 | 8시간 | 높음 |
| main.py 수정 | 1시간 | 높음 |
| 마이그레이션 스크립트 작성 | 4시간 | 중간 |
| vowser-client 모델 수정 | 2시간 | 중간 |
| 테스트 코드 작성 | 6시간 | 높음 |
| 통합 테스트 및 디버깅 | 6시간 | 높음 |
| **총 예상 시간** | **32시간** | |

---

## 9. 롤백 계획

만약 새 구조에 문제가 발생할 경우:

### 9.1 데이터베이스 롤백
```bash
# 백업 복원
neo4j-admin restore --from=/path/to/backup --database=neo4j --force
```

### 9.2 코드 롤백
```bash
git revert <commit-hash>
```

### 9.3 하이브리드 운영
- 새 구조와 기존 구조를 동시에 운영
- 새 엔드포인트 `/ws/v2` 생성
- 점진적 마이그레이션

---

## 10. 요약

### 핵심 변경 사항
1. **ROOT 노드 강화**: 임베딩 추가, baseURL로 시작점 처리, visitCount 추적
2. **PAGE → STEP**: 액션 중심, 입력/대기 지원
3. **PATH 노드 제거**: HAS_STEP + NEXT_STEP 관계로 대체
4. **taskIntent 추가**: 사용자 의도 직접 표현, 검색 정확도 향상
5. **navigate 액션 제거**: 3가지 액션(click/input/wait)만 사용, 페이지 이동은 click의 결과로 표현

### 기대 효과
- ✅ "오늘의 날씨 알려줘" → `taskIntent = "날씨 보기"` 직접 매칭
- ✅ 입력 필드 타입, 대기 메시지 등 UX 개선
- ✅ 단순화된 그래프 구조로 유지보수성 향상
- ✅ 벡터 검색 성능 최적화

### 다음 단계
1. 이 문서 검토 및 피드백
2. 프로토타입 구현 (작은 범위)
3. 성능 테스트
4. 전체 마이그레이션 진행

---

## 11. 🚨 기여 모드 데이터 수집 문제와 해결책

### 11.1 핵심 문제

**현재 기여 모드가 수집하는 데이터:**
```kotlin
// BrowserAutomationService.kt - injectUserInteractionListeners()
ContributionStep(
    url: "https://naver.com/login",
    title: "네이버 로그인",
    action: "click",  // 또는 "type"
    selector: "#id",
    htmlAttributes: {
        "text": "아이디",
        "tag": "input",
        "id": "id",
        "class": "input_text",
        "type": "text",  // ⚠️ HTML type attribute
        "placeholder": "아이디"
    }
)
```

**새 DB 스키마가 요구하는 데이터:**
```python
StepData(
    action: "input",  # "click" | "input" | "wait"
    inputType: "id",  # ⚠️ 시맨틱 타입: "email" | "id" | "password" | "search"
    inputPlaceholder: "네이버 아이디를 입력하세요",
    waitMessage: "카카오 간편인증을 기다리고 있습니다",  # ⚠️ 수집 불가능
    ...
)
```

### 11.2 데이터 수집 갭 분석

| 필드 | 현재 수집 가능 | 문제점 | 해결 방법 |
|------|--------------|--------|-----------|
| `selectors` | ✅ 가능 | selector 1개만 수집 | ✅ **해결 가능** - generateSelector() 로직 확장 |
| `action` | ⚠️ 부분 | "type" → "input" 변환 필요 | ✅ **해결 가능** - 매핑 테이블 |
| `inputType` | ❌ 불가능 | HTML type="text"로는 id/email 구분 불가 | ⚠️ **AI 추론 필요** |
| `inputPlaceholder` | ✅ 가능 | htmlAttributes에 있음 | ✅ **해결됨** |
| `waitMessage` | ❌ 불가능 | 사용자가 무엇을 기다리는지 알 수 없음 | ⚠️ **사용자 입력 필요** |
| `description` | ⚠️ 부분 | textContent만 수집 | ⚠️ **AI 생성 필요** |
| `taskIntent` | ❌ 불가능 | 전체 경로의 목적을 알 수 없음 | ⚠️ **사용자 입력 필요** |

### 11.3 해결책: 하이브리드 접근 (자동 수집 + 사용자 보정 + AI 추론)

#### **전략 A: 2단계 기여 모드 (권장)**

##### **1단계: 자동 경로 기록 (현재 방식)**
사용자가 브라우저를 조작하면 자동으로 기본 데이터 수집:
```kotlin
// 자동 수집
ContributionStep(
    url = "https://naver.com/login",
    action = "type",  // 자동 감지
    selector = "#id",
    htmlAttributes = mapOf(
        "type" to "text",
        "placeholder" to "아이디",
        "text" to "my_id_123"
    )
)
```

##### **2단계: 메타데이터 보정 UI (새로 추가)**
경로 기록 완료 후, 사용자에게 추가 정보 입력 받는 UI 표시:

```
┌──────────────────────────────────────┐
│ 기여 모드 - 경로 정보 확인           │
├──────────────────────────────────────┤
│ 📝 이 경로의 목적은 무엇인가요?     │
│ [로그인                        ]     │
│                                      │
│ 🔄 수집된 단계를 확인해주세요:       │
│                                      │
│ Step 1: 네이버 로그인 페이지 이동    │
│   ✓ 자동 감지됨                      │
│                                      │
│ Step 2: 아이디 입력                  │
│   ⚠️ 이 입력 필드는 무엇인가요?      │
│   ○ 아이디/사용자명                  │
│   ○ 이메일                           │
│   ○ 전화번호                         │
│   ○ 검색어                           │
│   ○ 기타                             │
│                                      │
│ Step 3: 비밀번호 입력                │
│   ✓ 비밀번호로 자동 인식됨           │
│   (type="password" 감지)             │
│                                      │
│ Step 4: 로그인 버튼 클릭             │
│   ⚠️ 이후 추가 인증 과정이 있나요?   │
│   □ 카카오 간편인증 대기             │
│   □ SMS 인증 대기                    │
│   □ OTP 입력 대기                    │
│   □ 없음                             │
│                                      │
│ [← 취소]  [다시 기록]  [제출 →]     │
└──────────────────────────────────────┘
```

##### **구현: ContributionMetadataEnricher**

```kotlin
// shared/src/commonMain/kotlin/com/vowser/client/contribution/ContributionMetadataEnricher.kt

data class InputTypeQuestion(
    val stepIndex: Int,
    val selector: String,
    val placeholder: String?,
    val suggestedType: String?,  // AI가 추론한 타입
    val confidence: Float        // 추론 신뢰도 (0.0 ~ 1.0)
)

data class WaitStepQuestion(
    val afterStepIndex: Int,
    val detectedPatterns: List<String>  // ["간편인증", "카카오", "팝업"] 등
)

data class MetadataEnrichmentQuestions(
    val taskIntent: String? = null,  // 사용자가 입력한 태스크 의도
    val inputTypeQuestions: List<InputTypeQuestion>,
    val waitStepQuestions: List<WaitStepQuestion>,
    val manualDescriptions: Map<Int, String>  // stepIndex → 사용자 지정 설명
)

class ContributionMetadataEnricher {

    /**
     * 1단계: 자동 수집된 데이터를 분석하여 질문 생성
     */
    fun generateQuestions(steps: List<ContributionStep>): MetadataEnrichmentQuestions {
        val inputQuestions = mutableListOf<InputTypeQuestion>()
        val waitQuestions = mutableListOf<WaitStepQuestion>()

        steps.forEachIndexed { index, step ->
            // 입력 필드 타입 추론
            if (step.action == "type") {
                val htmlType = step.htmlAttributes?.get("type")
                val placeholder = step.htmlAttributes?.get("placeholder") ?: ""
                val id = step.htmlAttributes?.get("id") ?: ""
                val name = step.htmlAttributes?.get("name") ?: ""

                // AI 기반 타입 추론
                val (suggestedType, confidence) = inferInputType(
                    htmlType, placeholder, id, name
                )

                // 신뢰도 낮으면 사용자에게 질문
                if (confidence < 0.8) {
                    inputQuestions.add(InputTypeQuestion(
                        stepIndex = index,
                        selector = step.selector ?: "",
                        placeholder = placeholder,
                        suggestedType = suggestedType,
                        confidence = confidence
                    ))
                }
            }

            // 대기 패턴 감지
            if (detectWaitPattern(step, steps.getOrNull(index + 1))) {
                waitQuestions.add(WaitStepQuestion(
                    afterStepIndex = index,
                    detectedPatterns = extractWaitKeywords(step)
                ))
            }
        }

        return MetadataEnrichmentQuestions(
            inputTypeQuestions = inputQuestions,
            waitStepQuestions = waitQuestions,
            manualDescriptions = emptyMap()
        )
    }

    /**
     * 2단계: 사용자 답변을 받아 최종 StepData 생성
     */
    fun enrichSteps(
        originalSteps: List<ContributionStep>,
        answers: MetadataEnrichmentQuestions
    ): List<EnrichedStepData> {
        return originalSteps.mapIndexed { index, step ->
            EnrichedStepData(
                url = step.url,
                domain = extractDomain(step.url),
                selectors = generateMultipleSelectors(step),  // 여러 셀렉터 생성
                action = mapAction(step.action),  // "type" → "input"
                isInput = step.action == "type",
                inputType = getInputType(index, step, answers),
                inputPlaceholder = step.htmlAttributes?.get("placeholder"),
                shouldWait = answers.waitStepQuestions.any { it.afterStepIndex == index },
                waitMessage = getWaitMessage(index, answers),
                description = answers.manualDescriptions[index]
                    ?: generateDescription(step),
                textLabels = extractTextLabels(step),
                contextText = step.htmlAttributes?.get("text")
            )
        }
    }

    /**
     * AI 기반 입력 타입 추론
     */
    private fun inferInputType(
        htmlType: String?,
        placeholder: String,
        id: String,
        name: String
    ): Pair<String, Float> {
        // HTML type이 명확한 경우
        if (htmlType == "password") return "password" to 1.0f
        if (htmlType == "email") return "email" to 1.0f
        if (htmlType == "tel") return "phone" to 1.0f

        // 패턴 매칭
        val text = "$placeholder $id $name".lowercase()

        return when {
            text.contains("email") || text.contains("이메일") || text.contains("메일")
                -> "email" to 0.9f

            text.contains("id") || text.contains("아이디") || text.contains("사용자")
                -> "id" to 0.85f

            text.contains("search") || text.contains("검색")
                -> "search" to 0.9f

            text.contains("password") || text.contains("비밀번호") || text.contains("pw")
                -> "password" to 0.8f

            text.contains("phone") || text.contains("전화") || text.contains("핸드폰")
                -> "phone" to 0.85f

            else -> "text" to 0.3f  // 낮은 신뢰도
        }
    }

    /**
     * 대기 패턴 감지
     */
    private fun detectWaitPattern(current: ContributionStep, next: ContributionStep?): Boolean {
        val text = current.htmlAttributes?.get("text")?.lowercase() ?: ""
        val buttonTexts = listOf("로그인", "인증", "확인", "제출", "login", "submit", "verify")

        // 로그인/인증 버튼 클릭 후 페이지 변화 없음 = 대기 가능성
        if (current.action == "click" && buttonTexts.any { text.contains(it) }) {
            return true
        }

        return false
    }

    /**
     * 대기 키워드 추출
     */
    private fun extractWaitKeywords(step: ContributionStep): List<String> {
        val keywords = mutableListOf<String>()
        val text = step.htmlAttributes?.get("text")?.lowercase() ?: ""

        if (text.contains("카카오")) keywords.add("카카오")
        if (text.contains("naver") || text.contains("네이버")) keywords.add("네이버")
        if (text.contains("간편")) keywords.add("간편인증")
        if (text.contains("sms")) keywords.add("SMS")
        if (text.contains("otp")) keywords.add("OTP")

        return keywords
    }
}

data class EnrichedStepData(
    val url: String,
    val domain: String,
    val selectors: List<String>,
    val action: String,
    val isInput: Boolean,
    val inputType: String?,
    val inputPlaceholder: String?,
    val shouldWait: Boolean,
    val waitMessage: String?,
    val description: String,
    val textLabels: List<String>,
    val contextText: String?
)
```

#### **전략 B: AI 자동 추론 (고급 옵션)**

사용자 개입 없이 LLM으로 메타데이터 자동 생성:

```python
# vowser-mcp-server/app/services/metadata_enrichment_service.py

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

def enrich_contribution_with_ai(contribution_steps: List[dict]) -> dict:
    """
    LLM을 사용해 기여 데이터 메타데이터 자동 추론
    """
    llm = ChatOpenAI(model="gpt-4", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 웹 브라우저 자동화 전문가입니다.
        사용자의 웹 탐색 경로를 분석하여 다음을 추론해주세요:

        1. taskIntent: 전체 경로의 목적 (예: "로그인", "날씨 보기")
        2. 각 입력 필드의 inputType: "id", "email", "password", "search", "text" 중 하나
        3. 대기가 필요한 단계와 waitMessage

        JSON 형식으로 응답하세요."""),
        ("user", """다음 경로를 분석해주세요:

        {steps}

        출력 형식:
        {{
            "taskIntent": "...",
            "enrichedSteps": [
                {{
                    "stepIndex": 0,
                    "inputType": "id",
                    "shouldWait": false,
                    "waitMessage": null,
                    "description": "..."
                }},
                ...
            ]
        }}""")
    ])

    chain = prompt | llm

    result = chain.invoke({
        "steps": json.dumps(contribution_steps, ensure_ascii=False, indent=2)
    })

    return json.loads(result.content)
```

### 11.4 최종 권장 방안: 단계별 도입

#### **Phase 1: 기본 자동화 (즉시 구현 가능)**
```kotlin
// 자동 매핑만 수행
action: "type" → "input"
inputType: HTML type 속성 또는 placeholder 패턴 매칭
inputPlaceholder: htmlAttributes["placeholder"]
selectors: [primary, ...fallbacks]  // 여러 셀렉터 생성
```

**장점**: 코드 수정 최소, 즉시 적용 가능
**단점**: 정확도 70~80%

#### **Phase 2: 사용자 보정 UI 추가 (2주 작업)**
```kotlin
// 기여 모드 완료 후 메타데이터 입력 화면
- taskIntent 입력
- 불확실한 inputType 질문
- 대기 단계 확인
```

**장점**: 정확도 95%+, 사용자 주도 데이터 품질 관리
**단점**: 사용자 추가 작업 필요 (30초~1분)

#### **Phase 3: AI 자동 추론 (선택사항)**
```python
# LLM으로 자동 메타데이터 생성
- GPT-4로 경로 분석
- 높은 정확도 자동 추론
```

**장점**: 완전 자동화
**단점**: API 비용, 응답 지연

### 11.5 DB 스키마 조정 (유연성 추가)

새 DB 스키마를 **점진적 채우기** 가능하도록 수정:

```cypher
(s:STEP {
  // 필수 필드 (자동 수집 가능)
  stepId: string,
  url: string,
  domain: string,
  selectors: [string],  // ✅ 자동 생성 가능
  action: string,       // ✅ 자동 매핑 가능

  // 선택적 필드 (점진적 보강)
  inputType: string?,           // ⚠️ AI 추론 or 사용자 입력
  inputPlaceholder: string?,    // ✅ 자동 수집 가능
  shouldWait: boolean?,         // ⚠️ 패턴 감지 or 사용자 확인
  waitMessage: string?,         // ⚠️ 사용자 입력 필요

  description: string,          // ⚠️ AI 생성 or 자동 생성
  textLabels: [string],         // ✅ 자동 수집 가능

  // 신뢰도 메타데이터 (새로 추가)
  autoGeneratedFields: [string],    // ["inputType", "description"]
  userVerified: boolean,            // 사용자가 검증했는지
  enrichmentVersion: int            // 보강 버전 (추후 재보강)
})
```

### 11.6 구현 우선순위

| 순위 | 작업 | 예상 시간 | 영향도 |
|------|------|-----------|--------|
| 1 | 액션 매핑 (type→input) | 2시간 | 높음 |
| 2 | 다중 셀렉터 생성 로직 | 3시간 | 높음 |
| 3 | 기본 inputType 추론 (패턴 매칭) | 4시간 | 중간 |
| 4 | 메타데이터 보정 UI 설계 | 6시간 | 높음 |
| 5 | 메타데이터 보정 UI 구현 | 12시간 | 높음 |
| 6 | AI 자동 추론 (선택) | 8시간 | 낮음 |
| **합계** | | **35시간** | |

### 11.7 업데이트된 ContributionModels.kt

```kotlin
@Serializable
data class ContributionStep(
    val url: String,
    val action: String,  // "click", "type", "navigate"
    val selector: String?,
    val htmlAttributes: Map<String, String>?,
    val timestamp: Long = Clock.System.now().toEpochMilliseconds()
)

@Serializable
data class ContributionSession(
    val sessionId: String = uuid4().toString(),
    val task: String,  // 사용자가 입력한 태스크 (기존)
    val steps: MutableList<ContributionStep> = mutableListOf(),
    val startTime: Long = Clock.System.now().toEpochMilliseconds(),
    var isActive: Boolean = true,

    // 새로 추가: 메타데이터 보강을 위한 필드
    var enrichmentData: ContributionEnrichmentData? = null
)

@Serializable
data class ContributionEnrichmentData(
    val taskIntent: String,  // "로그인", "날씨 보기" 등
    val inputTypeAnswers: Map<Int, String>,  // stepIndex → inputType
    val waitStepInsertions: List<WaitStepInsertion>,
    val manualDescriptions: Map<Int, String>
)

@Serializable
data class WaitStepInsertion(
    val afterStepIndex: Int,
    val waitMessage: String,
    val maxWaitTime: Int = 30
)
```

### 11.8 최종 데이터 플로우

```
1. 사용자 웹 탐색
   ↓
2. BrowserAutomationService 자동 기록
   ContributionStep { action: "type", htmlAttributes: {...} }
   ↓
3. 세션 종료 후 메타데이터 보정 UI 표시
   "이 입력 필드는 무엇인가요?"
   ↓
4. 사용자 답변 수집
   ContributionEnrichmentData { inputTypeAnswers: {1: "id"} }
   ↓
5. 서버로 전송
   {
     sessionId: "...",
     task: "네이버 로그인",
     steps: [...],
     enrichmentData: {...}
   }
   ↓
6. 서버에서 최종 StepData 생성
   StepData {
     action: "input",
     inputType: "id",
     description: "아이디 입력 필드",
     ...
   }
   ↓
7. Neo4j 저장
   (STEP { inputType: "id", ... })
```

---

## 12. 업데이트된 예상 작업 시간

| 작업 | 기존 | 추가 | 합계 |
|------|------|------|------|
| DB 스키마 설계 검토 | 2시간 | - | 2시간 |
| models/step.py, domain.py 작성 | 3시간 | - | 3시간 |
| neo4j_service.py 수정 | 8시간 | - | 8시간 |
| main.py 수정 | 1시간 | - | 1시간 |
| 마이그레이션 스크립트 작성 | 4시간 | - | 4시간 |
| **기여 모드 메타데이터 보강** | - | **35시간** | **35시간** |
| vowser-client 모델 수정 | 2시간 | 6시간 | 8시간 |
| 테스트 코드 작성 | 6시간 | 4시간 | 10시간 |
| 통합 테스트 및 디버깅 | 6시간 | 6시간 | 12시간 |
| **총 예상 시간** | **32시간** | **51시간** | **83시간** |

---

## 13. 같은 도메인에서 특정 Task 경로 검색하기

### 13.1 문제 상황

하나의 도메인(예: naver.com)에는 여러 태스크 경로가 존재합니다:

```
(DOMAIN {domain: "naver.com"})
  ├─[HAS_STEP {taskIntent: "로그인"}]→ (STEP) → (STEP) → ...
  ├─[HAS_STEP {taskIntent: "날씨 보기"}]→ (STEP) → (STEP) → ...
  ├─[HAS_STEP {taskIntent: "뉴스 읽기"}]→ (STEP) → ...
  └─[HAS_STEP {taskIntent: "웹툰 보기"}]→ (STEP) → ...
```

사용자가 "네이버 날씨 알려줘"라고 하면, **"날씨 보기"** 경로만 가져와야 합니다.

### 13.2 해결책: HAS_STEP 관계의 taskIntent 활용

#### **방법 1: taskIntent 정확 매칭**

```cypher
// 사용자 쿼리: "네이버 날씨"
// → taskIntent = "날씨 보기"로 추출

MATCH (r:ROOT {domain: "naver.com"})-[rel:HAS_STEP {taskIntent: "날씨 보기"}]->(firstStep:STEP)
MATCH path = (firstStep)-[:NEXT_STEP*0..20]->(lastStep:STEP)
WHERE NOT (lastStep)-[:NEXT_STEP]->()
RETURN [node IN nodes(path) | node] AS steps
LIMIT 1
```

**설명**:
- `HAS_STEP` 관계의 `taskIntent` 속성으로 필터링
- 해당 태스크의 첫 번째 STEP부터 시작하는 경로 반환
- `NEXT_STEP*0..20`: 최대 20단계까지 추적

#### **방법 2: 벡터 임베딩 유사도 검색 (자연어 쿼리)**

```cypher
// 사용자 쿼리: "오늘 날씨 어때?"
// → 벡터 임베딩 생성 후 유사도 계산 (Python에서)

// 1. 모든 taskIntent 가져오기
MATCH (r:ROOT {domain: "naver.com"})-[rel:HAS_STEP]->(firstStep:STEP)
WHERE rel.intentEmbedding IS NOT NULL
RETURN rel.taskIntent AS taskIntent,
       rel.intentEmbedding AS embedding,
       firstStep.stepId AS firstStepId,
       rel.weight AS popularity

// 2. Python에서 코사인 유사도 계산
// query_embedding = generate_embedding("오늘 날씨 어때?")
// for each task:
//     similarity = cosine_similarity(query_embedding, task.embedding)
// best_match = max(tasks, key=lambda x: x.similarity)

// 3. 가장 유사한 taskIntent의 경로 가져오기
MATCH (r:ROOT {domain: "naver.com"})-[rel:HAS_STEP]->(firstStep:STEP {stepId: $bestMatchStepId})
MATCH path = (firstStep)-[:NEXT_STEP*0..20]->(lastStep:STEP)
WHERE NOT (lastStep)-[:NEXT_STEP]->()
RETURN [node IN nodes(path) | node] AS steps
```

#### **방법 3: 여러 경로 반환 (사용자 선택)**

동일 도메인에서 여러 관련 경로를 모두 가져와 사용자에게 선택하게 하기:

```cypher
// "네이버"로 검색 → 모든 네이버 경로 반환
MATCH (r:ROOT {domain: "naver.com"})-[rel:HAS_STEP]->(firstStep:STEP)
RETURN rel.taskIntent AS taskIntent,
       rel.weight AS popularity,
       rel.lastUpdated AS lastUsed,
       firstStep.stepId AS firstStepId
ORDER BY r.weight DESC
LIMIT 5
```

**결과**:
```json
[
  {"taskIntent": "로그인", "popularity": 150, "firstStepId": "abc123"},
  {"taskIntent": "날씨 보기", "popularity": 80, "firstStepId": "def456"},
  {"taskIntent": "뉴스 읽기", "popularity": 60, "firstStepId": "ghi789"}
]
```

### 13.3 실제 구현 예시 (Python)

```python
def search_paths_by_domain_and_task(domain: str, user_query: str, limit: int = 3):
    """
    도메인 + 자연어 쿼리로 경로 검색

    예: domain="naver.com", user_query="날씨 보여줘"
    """
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")

    # 1. 쿼리 임베딩 생성
    query_embedding = generate_embedding(user_query)

    # 2. 해당 도메인의 모든 taskIntent 가져오기
    task_search_query = """
    MATCH (r:ROOT {domain: $domain})-[rel:HAS_STEP]->(firstStep:STEP)
    WHERE rel.intentEmbedding IS NOT NULL
    RETURN rel.taskIntent AS taskIntent,
           rel.intentEmbedding AS intentEmbedding,
           rel.weight AS weight,
           firstStep.stepId AS firstStepId
    """

    all_tasks = graph.query(task_search_query, {'domain': domain})

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

    task_results = []
    for task in all_tasks:
        similarity = cosine_similarity(query_embedding, task['intentEmbedding'])
        task_results.append({
            'taskIntent': task['taskIntent'],
            'similarity': similarity,
            'weight': task['weight'],
            'firstStepId': task['firstStepId']
        })

    # 유사도 + 인기도 조합 점수로 정렬
    task_results = sorted(
        task_results,
        key=lambda x: x['similarity'] * 0.7 + min(x['weight'] / 100, 1.0) * 0.3,
        reverse=True
    )[:limit]

    # 4. 각 태스크의 전체 경로 가져오기
    matched_paths = []
    for task in task_results:
        path_query = """
        MATCH path = (start:STEP {stepId: $startStepId})-[:NEXT_STEP*0..20]->(end:STEP)
        WHERE NOT (end)-[:NEXT_STEP]->()
        RETURN [node IN nodes(path) | node] AS steps
        LIMIT 1
        """

        path_data = graph.query(path_query, {'startStepId': task['firstStepId']})

        if path_data:
            matched_paths.append({
                'domain': domain,
                'taskIntent': task['taskIntent'],
                'relevance_score': round(task['similarity'], 3),
                'weight': task['weight'],
                'steps': format_steps(path_data[0]['steps'])
            })

    return {
        'query': user_query,
        'domain': domain,
        'total_matched': len(matched_paths),
        'matched_paths': matched_paths
    }
```

### 13.4 복잡한 케이스: 다단계 도메인 경로

네이버에서 시작해 날씨 사이트로 이동하는 크로스 도메인 경로:

```cypher
// 네이버 → 기상청 날씨 경로
MATCH (d1:DOMAIN {domain: "naver.com"})-[r1:HAS_STEP {taskIntent: "기상청 날씨 보기"}]->(step1:STEP)
MATCH path = (step1)-[:NEXT_STEP|NAVIGATES_TO_CROSS_DOMAIN*0..20]->(lastStep:STEP)
WHERE NOT (lastStep)-[:NEXT_STEP]->()
  AND NOT (lastStep)-[:NAVIGATES_TO_CROSS_DOMAIN]->()
RETURN [node IN nodes(path) | node] AS steps,
       [rel IN relationships(path) | type(rel)] AS relationshipTypes
```

### 13.5 성능 최적화: 인덱스 활용

```cypher
// taskIntent에 인덱스 생성 (전문 검색)
CREATE FULLTEXT INDEX task_intent_search IF NOT EXISTS
FOR ()-[r:HAS_STEP]-() ON EACH [r.taskIntent];

// 사용 예시: 전문 검색으로 빠르게 필터링
CALL db.index.fulltext.queryRelationships('task_intent_search', '날씨')
YIELD relationship, score
MATCH (r:ROOT)-[relationship]->(firstStep:STEP)
RETURN r.domain AS domain,
       relationship.taskIntent AS taskIntent,
       score,
       firstStep.stepId AS firstStepId
ORDER BY score DESC
LIMIT 5
```

### 13.6 실전 예시: 여러 시나리오

#### **시나리오 1: 정확한 taskIntent로 검색**
```cypher
// "네이버 로그인해줘"
MATCH (r:ROOT {domain: "naver.com"})-[rel:HAS_STEP]->(firstStep:STEP)
WHERE rel.taskIntent CONTAINS "로그인"  // 부분 매칭
MATCH path = (firstStep)-[:NEXT_STEP*0..20]->(end:STEP)
WHERE NOT (end)-[:NEXT_STEP]->()
RETURN path
LIMIT 1
```

#### **시나리오 2: 인기도 순으로 정렬**
```cypher
// "네이버에서 뭐 할 수 있어?"
MATCH (r:ROOT {domain: "naver.com"})-[rel:HAS_STEP]->(firstStep:STEP)
RETURN rel.taskIntent AS task,
       rel.weight AS popularity,
       rel.lastUpdated AS recentlyUsed
ORDER BY rel.weight DESC
LIMIT 10
```

#### **시나리오 3: 최근 사용 경로 우선**
```cypher
// "네이버에서 최근에 뭐 했지?"
MATCH (r:ROOT {domain: "naver.com"})-[rel:HAS_STEP]->(firstStep:STEP)
RETURN rel.taskIntent AS task,
       rel.lastUpdated AS lastUsed
ORDER BY rel.lastUpdated DESC
LIMIT 5
```

### 13.7 종합 검색 쿼리 (추천 알고리즘)

```cypher
// 사용자 쿼리: "네이버 날씨"
// 1. taskIntent 벡터 유사도 (Python에서 계산)
// 2. 전문 검색 점수
// 3. 인기도
// 4. 최근 사용 시간

MATCH (r:ROOT {domain: "naver.com"})-[rel:HAS_STEP]->(firstStep:STEP)
WHERE rel.taskIntent CONTAINS "날씨"  // 키워드 필터
WITH rel, firstStep,
     rel.weight AS popularity,
     duration.between(rel.lastUpdated, datetime()).days AS daysSinceLastUse
RETURN rel.taskIntent AS taskIntent,
       firstStep.stepId AS firstStepId,
       popularity,
       daysSinceLastUse,
       // 복합 점수 계산
       (popularity / 10.0) + (1.0 / (daysSinceLastUse + 1)) AS combinedScore
ORDER BY combinedScore DESC
LIMIT 3
```

**점수 계산 로직**:
- 인기도: `popularity / 10.0` (0~10 점수화)
- 최신성: `1.0 / (daysSinceLastUse + 1)` (최근일수록 높은 점수)
- 벡터 유사도: Python에서 별도 계산 후 조합

이렇게 하면 같은 도메인에서도 **가장 관련성 높은 태스크 경로**를 정확하게 찾을 수 있습니다!
