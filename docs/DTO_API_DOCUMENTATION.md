# DTO 및 API 문서 - DB 리팩토링

## 📋 목차
1. [개요](#개요)
2. [그래프 구조](#그래프-구조)
3. [MCP Server DTO](#mcp-server-dto)
4. [WebSocket API](#websocket-api)
5. [Client DTO (권장 구조)](#client-dto-권장-구조)
6. [Backend 연동 가이드](#backend-연동-가이드)
7. [예제 코드](#예제-코드)

---

## 개요

이 문서는 **DB 리팩토링 작업** (DB_refactor.md 기준)에 따른 새로운 DTO 구조와 API 사용법을 설명합니다.

### 핵심 변경사항
- **ROOT 노드 강화**: 임베딩 추가, baseURL로 시작점 처리, visitCount 추적
- **PAGE → STEP**: 액션 중심 단계 노드 (click/input/wait 지원)
- **PATH 노드 제거**: HAS_STEP + NEXT_STEP 관계로 대체
- **taskIntent 추가**: 사용자 의도를 직접 표현

---

## 그래프 구조

### Neo4j 그래프 관계도

```
┌─────────────────────────────────────────────────────────────────┐
│                    ROOT 노드 (도메인 정보)                         │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ ROOT {                                                    │   │
│  │   domain: "naver.com"                                     │   │
│  │   baseURL: "https://naver.com"                            │   │
│  │   displayName: "네이버"                                    │   │
│  │   embedding: [1536차원 벡터]                               │   │
│  │   visitCount: 42                                          │   │
│  │ }                                                         │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HAS_STEP
                              │ {taskIntent: "뉴스 읽기",
                              │  intentEmbedding: [벡터],
                              │  weight: 15}
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   첫 번째 STEP 노드                               │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ STEP {                                                    │   │
│  │   stepId: "abc123..."                                     │   │
│  │   action: "click"                                         │   │
│  │   selectors: ["#news_cast", ".news_area"]                 │   │
│  │   description: "뉴스 영역 클릭"                             │   │
│  │   textLabels: ["뉴스", "뉴스캐스트"]                        │   │
│  │   embedding: [1536차원 벡터]                               │   │
│  │ }                                                         │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ NEXT_STEP
                              │ {sequenceOrder: 1, weight: 10}
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   두 번째 STEP 노드                               │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ STEP {                                                    │   │
│  │   stepId: "def456..."                                     │   │
│  │   action: "click"                                         │   │
│  │   selectors: [".news_headline"]                           │   │
│  │   description: "뉴스 기사 클릭"                             │   │
│  │   textLabels: ["속보", "뉴스 제목"]                         │   │
│  │ }                                                         │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 노드 및 관계 설명

#### ROOT 노드
- **역할**: 도메인(웹사이트)의 메타데이터 저장
- **속성**: domain, baseURL, embedding, visitCount 등
- **1개 ROOT → 여러 HAS_STEP 관계**: 한 도메인에서 여러 다른 태스크(날씨 보기, 뉴스 읽기 등) 가능

#### HAS_STEP 관계 (ROOT → STEP)
- **역할**: 특정 태스크의 첫 번째 단계를 연결
- **속성**:
  - `taskIntent`: "뉴스 읽기", "날씨 보기" 등 사용자 의도
  - `intentEmbedding`: taskIntent의 벡터 임베딩 (검색용)
  - `weight`: 사용 빈도

#### STEP 노드
- **역할**: 사용자의 개별 액션(클릭, 입력, 대기) 표현
- **속성**: action, selectors, description, embedding 등
- **재사용 가능**: 같은 STEP이 여러 경로에서 공유될 수 있음

#### NEXT_STEP 관계 (STEP → STEP)
- **역할**: 순차적인 단계 연결
- **속성**:
  - `sequenceOrder`: 경로 내 순서 (0, 1, 2, ...)
  - `weight`: 이 연결의 사용 빈도

---

## MCP Server DTO

### 1. RootData (app/models/root.py)

```python
class RootData(BaseModel):
    """
    ROOT 노드 데이터
    도메인 정보와 메타데이터를 담는 모델
    """
    domain: str              # 예: "naver.com"
    baseURL: str             # 예: "https://naver.com"
    displayName: str         # 예: "네이버"
    keywords: List[str] = [] # 예: ["네이버", "포털", "검색"]
```

**사용처**: 서버 내부에서 자동 생성됨. 클라이언트가 직접 전송하지 않음.

---

### 2. StepData (app/models/step.py)

```python
class StepData(BaseModel):
    """
    단일 STEP 노드 데이터 (기존 PAGE 노드 확장)
    """
    # 자동 생성 필드
    stepId: Optional[str] = None  # 서버에서 자동 생성 (MD5 해시)

    # 필수 필드
    url: str
    domain: str
    action: str  # "click" | "input" | "wait"
    description: str  # "로그인 버튼 클릭", "아이디 입력"

    # 선택자 정보
    selectors: List[str] = []  # [primary, fallback1, fallback2, ...]
    anchorPoint: Optional[str] = None
    relativePathFromAnchor: Optional[str] = None

    # 입력 관련 (action = "input"일 때)
    isInput: bool = False
    inputType: Optional[str] = None  # "email" | "id" | "password" | "search" | "text"
    inputPlaceholder: Optional[str] = None  # "네이버 아이디를 입력하세요"

    # 대기 관련 (action = "wait"일 때)
    shouldWait: bool = False
    waitMessage: Optional[str] = None  # "카카오 간편인증을 기다리고 있습니다"
    maxWaitTime: Optional[int] = None  # 최대 대기 시간 (초)

    # 시맨틱 정보
    textLabels: List[str] = []  # ["로그인", "Login"]
    contextText: Optional[str] = None  # 주변 텍스트

    # 메타데이터
    successRate: float = 1.0  # 0.0 ~ 1.0
```

**예시: 클릭 액션**
```json
{
  "url": "https://naver.com",
  "domain": "naver.com",
  "action": "click",
  "selectors": ["#main_weather", ".weather_area"],
  "description": "날씨 위젯 클릭",
  "textLabels": ["날씨", "오늘의 날씨"],
  "isInput": false,
  "shouldWait": false
}
```

**예시: 입력 액션**
```json
{
  "url": "https://naver.com",
  "domain": "naver.com",
  "action": "input",
  "selectors": ["#query", ".search_input"],
  "description": "검색어 입력",
  "isInput": true,
  "inputType": "search",
  "inputPlaceholder": "검색어를 입력하세요",
  "textLabels": ["검색", "Search"],
  "shouldWait": false
}
```

**예시: 대기 액션**
```json
{
  "url": "https://nid.naver.com/nidlogin.login",
  "domain": "naver.com",
  "action": "wait",
  "selectors": [],
  "description": "2단계 인증 대기",
  "isInput": false,
  "shouldWait": true,
  "waitMessage": "카카오 간편인증을 기다리고 있습니다",
  "maxWaitTime": 30
}
```

---

### 3. PathSubmission (app/models/step.py)

```python
class PathSubmission(BaseModel):
    """
    사용자가 제출하는 완전한 경로 데이터
    """
    sessionId: str        # 세션 고유 ID (UUID)
    taskIntent: str       # "날씨 보기", "로그인", "뉴스 읽기" 등
    domain: str           # 시작 도메인 (예: "naver.com")
    steps: List[StepData] # 순차적 단계 목록
```

**예시: 네이버 뉴스 읽기 경로**
```json
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "taskIntent": "뉴스 읽기",
  "domain": "naver.com",
  "steps": [
    {
      "url": "https://naver.com",
      "domain": "naver.com",
      "action": "click",
      "selectors": ["#news_cast", ".news_area"],
      "description": "뉴스 영역 클릭",
      "textLabels": ["뉴스", "뉴스캐스트"]
    },
    {
      "url": "https://news.naver.com",
      "domain": "naver.com",
      "action": "click",
      "selectors": [".news_headline", ".news_tit"],
      "description": "뉴스 기사 클릭",
      "textLabels": ["속보", "뉴스 제목"]
    }
  ]
}
```

---

## WebSocket API

### 엔드포인트
```
ws://localhost:8000/ws
```

### 메시지 구조
```json
{
  "type": "message_type",
  "data": { /* 메시지별 데이터 */ }
}
```

---

### 1. 경로 저장 (리팩토링)

**요청 타입**: `save_new_path`

**요청 데이터**: `PathSubmission` 객체

```json
{
  "type": "save_new_path",
  "data": {
    "sessionId": "550e8400-e29b-41d4-a716-446655440000",
    "taskIntent": "날씨 보기",
    "domain": "naver.com",
    "steps": [
      {
        "url": "https://naver.com",
        "domain": "naver.com",
        "action": "click",
        "selectors": ["#main_weather", ".weather_area"],
        "description": "날씨 위젯 클릭",
        "textLabels": ["날씨", "오늘의 날씨"]
      }
    ]
  }
}
```

**응답**:
```json
{
  "type": "path_save_result",
  "status": "success",
  "data": {
    "message": "Refactored path data processed successfully!",
    "result": {
      "status": "success",
      "domain": "naver.com",
      "taskIntent": "날씨 보기",
      "steps_saved": 1
    }
  }
}
```

---

### 2. 경로 검색 (리팩토링)

**요청 타입**: `search_new_path`

**요청 데이터**: `SearchPathRequest` 객체

```json
{
  "type": "search_new_path",
  "data": {
    "query": "네이버 날씨 보여줘",
    "limit": 3,
    "domain_hint": "naver.com"  // 선택사항
  }
}
```

**응답**:
```json
{
  "type": "search_path_result",
  "status": "success",
  "data": {
    "query": "네이버 날씨 보여줘",
    "total_matched": 1,
    "matched_paths": [
      {
        "domain": "naver.com",
        "taskIntent": "날씨 보기",
        "relevance_score": 0.92,
        "weight": 15,
        "steps": [
          {
            "order": 0,
            "url": "https://naver.com",
            "action": "click",
            "selectors": ["#main_weather", ".weather_area"],
            "description": "날씨 위젯 클릭",
            "isInput": false,
            "shouldWait": false,
            "textLabels": ["날씨", "오늘의 날씨"]
          }
        ]
      }
    ],
    "performance": {
      "search_time": 145
    }
  }
}
```

---


## Client DTO (권장 구조)

### vowser-client에서 사용할 모델 (Kotlin)

```kotlin
// shared/src/commonMain/kotlin/com/vowser/client/models/PathModels.kt

@Serializable
data class StepData(
    val url: String,
    val domain: String,
    val action: String,  // "click" | "input" | "wait"
    val selectors: List<String> = emptyList(),
    val anchorPoint: String? = null,
    val relativePathFromAnchor: String? = null,

    // 입력 관련
    val isInput: Boolean = false,
    val inputType: String? = null,
    val inputPlaceholder: String? = null,

    // 대기 관련
    val shouldWait: Boolean = false,
    val waitMessage: String? = null,
    val maxWaitTime: Int? = null,

    // 시맨틱 정보
    val description: String,
    val textLabels: List<String> = emptyList(),
    val contextText: String? = null,

    val successRate: Float = 1.0f
)

@Serializable
data class PathSubmission(
    val sessionId: String = uuid4().toString(),
    val taskIntent: String,
    val domain: String,
    val steps: List<StepData>
)

// 서버 응답 모델
@Serializable
data class PathSearchResult(
    val query: String,
    val totalMatched: Int,
    val matchedPaths: List<MatchedPath>,
    val performance: Performance
)

@Serializable
data class MatchedPath(
    val domain: String,
    val taskIntent: String,
    val relevanceScore: Float,
    val weight: Int,
    val steps: List<StepResponse>
)

@Serializable
data class StepResponse(
    val order: Int,
    val url: String,
    val action: String,
    val selectors: List<String>,
    val description: String,
    val isInput: Boolean,
    val inputType: String?,
    val inputPlaceholder: String?,
    val shouldWait: Boolean,
    val waitMessage: String?,
    val textLabels: List<String>
)

@Serializable
data class Performance(
    val searchTime: Int  // ms
)
```

---

## Backend 연동 가이드

### 1. 경로 저장 플로우

```
Client (기여모드)
  → 사용자 웹 탐색 기록
  → PathSubmission 객체 생성
  → WebSocket 전송 (save_new_path)
  → MCP Server
     → Neo4j 저장 (DOMAIN, STEP, HAS_STEP, NEXT_STEP)
  → 응답 수신
```

### 2. 경로 검색 플로우

```
Client (자동화 모드)
  → 사용자 자연어 입력 ("네이버 날씨 보여줘")
  → SearchPathRequest 생성
  → WebSocket 전송 (search_new_path)
  → MCP Server
     → 임베딩 생성
     → taskIntent 유사도 계산
     → 경로 재구성
  → 응답 수신 (MatchedPath 리스트)
  → 브라우저 자동화 실행
```

### 3. 기여모드에서 데이터 수집 시 주의사항

#### ⚠️ 새롭게 필요한 데이터

리팩토링된 DB 구조에서는 **기존에 수집하지 않던 데이터**를 추가로 수집해야 합니다:

**1. taskIntent (필수 - 새로 추가)**
- **설명**: 전체 경로의 목적 ("뉴스 읽기", "날씨 보기", "검색하기" 등)
- **수집 방법**:
  - 기여모드 시작 시 사용자에게 입력 받기
  - 또는 기여모드 종료 후 "이 경로의 목적은 무엇인가요?" UI 창 표시
- **UI 필요**: ✅ **새로운 입력 창 필요** (기존에는 수집하지 않았음)

**2. inputType (선택적 - 기존 데이터로 추론 가능하지만 정확도 낮음)**
- **설명**: 입력 필드의 의미적 타입 ("id", "email", "password", "search", "text")
- **수집 방법**:
  - HTML type 속성으로 일부 추론 가능 (password, email)
  - 나머지는 패턴 매칭 또는 사용자 확인 필요
- **UI 필요**: ⚠️ **선택적** (정확도 향상을 위해 사용자 확인 UI 권장)

**3. waitMessage (선택적 - 대기 단계가 있을 경우)**
- **설명**: 대기 중 사용자에게 표시할 메시지 ("카카오 간편인증 대기 중...")
- **수집 방법**: 대기 단계 감지 시 사용자에게 입력 받기
- **UI 필요**: ⚠️ **선택적** (대기 단계가 있을 때만)

#### 현재 기여모드 수집 데이터
```kotlin
ContributionStep(
    url: "...",
    action: "type",  // ⚠️ "type" → "input"으로 변환 필요
    selector: "#id",
    htmlAttributes: {...}
    // ❌ taskIntent 없음 (새로 수집 필요!)
    // ❌ inputType 없음 (추론 또는 사용자 확인 필요)
)
```

#### 권장 UI 플로우

**옵션 1: 기여모드 시작 시 taskIntent 입력**
```
┌────────────────────────────────────┐
│  기여 모드 시작                     │
├────────────────────────────────────┤
│  이 경로의 목적을 입력하세요:       │
│  ┌──────────────────────────────┐  │
│  │ 뉴스 읽기                    │  │
│  └──────────────────────────────┘  │
│                                    │
│  예시: 로그인, 날씨 보기, 뉴스 읽기 │
│                                    │
│  [취소]  [시작]                    │
└────────────────────────────────────┘
```

**옵션 2: 기여모드 종료 후 메타데이터 보정 (권장)**
```
┌────────────────────────────────────┐
│  기여 완료 - 정보 확인              │
├────────────────────────────────────┤
│  📝 이 경로의 목적은?               │
│  ┌──────────────────────────────┐  │
│  │ 뉴스 읽기                    │  │
│  └──────────────────────────────┘  │
│                                    │
│  🔍 수집된 단계:                   │
│  1. 뉴스 영역 클릭                  │
│  2. 뉴스 기사 클릭                  │
│                                    │
│  ⚠️ 입력 필드가 감지되지 않았습니다  │
│                                    │
│  [취소]  [다시 기록]  [제출]        │
└────────────────────────────────────┘
```

#### 변환 로직 (기존 데이터 → 새 구조)
```kotlin
fun convertToStepData(contributionStep: ContributionStep): StepData {
    return StepData(
        url = contributionStep.url,
        domain = extractDomain(contributionStep.url),
        action = when (contributionStep.action) {
            "type" -> "input"
            "click" -> "click"
            else -> contributionStep.action
        },
        selectors = listOf(contributionStep.selector ?: ""),
        description = generateDescription(contributionStep),
        isInput = contributionStep.action == "type",
        inputType = inferInputType(contributionStep.htmlAttributes),
        inputPlaceholder = contributionStep.htmlAttributes?.get("placeholder"),
        textLabels = extractTextLabels(contributionStep)
    )
}

fun inferInputType(htmlAttributes: Map<String, String>?): String? {
    val htmlType = htmlAttributes?.get("type") ?: ""
    val placeholder = htmlAttributes?.get("placeholder") ?: ""
    val id = htmlAttributes?.get("id") ?: ""

    return when {
        htmlType == "password" -> "password"
        htmlType == "email" -> "email"
        placeholder.contains("아이디") || id.contains("id") -> "id"
        placeholder.contains("검색") || id.contains("search") -> "search"
        else -> "text"
    }
}
```

---

## 예제 코드

### Python (MCP Server 테스트)

```python
import asyncio
import websockets
import json
from uuid import uuid4

async def test_save_path():
    uri = "ws://localhost:8000/ws"

    path_data = {
        "sessionId": str(uuid4()),
        "taskIntent": "날씨 보기",
        "domain": "naver.com",
        "steps": [
            {
                "url": "https://naver.com",
                "domain": "naver.com",
                "action": "click",
                "selectors": ["#main_weather", ".weather_area"],
                "description": "날씨 위젯 클릭",
                "textLabels": ["날씨", "오늘의 날씨"]
            }
        ]
    }

    message = {
        "type": "save_new_path",
        "data": path_data
    }

    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        print(json.dumps(json.loads(response), indent=2, ensure_ascii=False))

asyncio.run(test_save_path())
```

### Python (경로 검색 테스트)

```python
async def test_search_path():
    uri = "ws://localhost:8000/ws"

    message = {
        "type": "search_new_path",
        "data": {
            "query": "네이버 날씨 보여줘",
            "limit": 3
        }
    }

    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        result = json.loads(response)

        print(f"검색어: {result['data']['query']}")
        print(f"매칭된 경로: {result['data']['total_matched']}개")

        for path in result['data']['matched_paths']:
            print(f"\n- {path['taskIntent']} (유사도: {path['relevance_score']})")
            for step in path['steps']:
                print(f"  {step['order']}. {step['action']}: {step['description']}")

asyncio.run(test_search_path())
```

### Kotlin (Client 사용 예시)

```kotlin
// PathSubmission 생성 및 전송
suspend fun submitPath(steps: List<StepData>, taskIntent: String, domain: String) {
    val pathSubmission = PathSubmission(
        sessionId = uuid4().toString(),
        taskIntent = taskIntent,
        domain = domain,
        steps = steps
    )

    val message = WebSocketMessage(
        type = "save_new_path",
        data = Json.encodeToJsonElement(pathSubmission)
    )

    webSocketClient.send(Json.encodeToString(message))
}

// 경로 검색
suspend fun searchPath(query: String): PathSearchResult? {
    val message = WebSocketMessage(
        type = "search_new_path",
        data = buildJsonObject {
            put("query", query)
            put("limit", 3)
        }
    )

    webSocketClient.send(Json.encodeToString(message))
    val response = webSocketClient.receive()

    return Json.decodeFromString<PathSearchResult>(response)
}
```

---

## 마이그레이션 체크리스트

### MCP Server
- [x] `app/models/root.py` 생성
- [x] `app/models/step.py` 생성
- [x] `app/services/path_service_refactored.py` 생성
- [x] `app/main.py` 업데이트 (새 메시지 타입 추가)
- [ ] Neo4j 데이터베이스 생성 (새 DB 또는 기존 DB 초기화)
- [ ] 인덱스 생성 실행 (`create_indexes_refactored`)

### Client (vowser-client)
- [ ] `StepData` 모델 추가
- [ ] `PathSubmission` 모델 추가
- [ ] `PathSearchResult` 모델 추가
- [ ] 기여모드 → StepData 변환 로직 구현
- [ ] WebSocket 메시지 타입 업데이트

### Backend (vowser-backend)
- [ ] 새 DTO 모델 추가 (필요 시)
- [ ] MCP Server 응답 파싱 로직 업데이트

---

## 문의 및 지원

- **DB 구조 상세**: `DB_refactor.md` 참조
- **WebSocket API 전체**: `docs/WEBSOCKET_API.md` 참조 (기존)
- **문제 발생 시**: GitHub Issues 또는 팀 채널로 문의
