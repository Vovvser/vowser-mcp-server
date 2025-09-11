# Vowser MCP Server

FastAPI-based WebSocket server that serves as an MCP (Model Context Protocol) server for web crawling and path analysis. The server integrates with Neo4j for graph-based storage of web navigation paths and uses LangChain for AI-powered content analysis.

## Features

- **WebSocket Communication**: Real-time bidirectional communication via WebSocket
- **Neo4j Graph Database**: Stores web navigation paths as graph structures
- **AI-Powered Analysis**: LangChain integration for semantic content analysis
- **Path Search**: Natural language search for navigation paths using vector embeddings
- **Popular Path Tracking**: Usage-based path recommendations with weighted relationships

## Quick Start

### Environment Setup

```bash
# Install dependencies (recommended)
uv sync

# Alternative: pip install
pip install -r requirements.txt
```

### Configuration

Create a `.env` file:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
GOOGLE_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_key
```

### Running the Server

```bash
# Start the FastAPI server
uvicorn app.main:app --port 8000 --reload

# Alternative: using Python module
python -m uvicorn app.main:app --port 8000 --reload
```

### Testing

```bash
# Run comprehensive WebSocket tests
cd test/
python test_single.py

# Expected output: "전체 결과: 5/5 성공"
```

## API Documentation

### WebSocket Connection

- **URL**: `ws://localhost:8000/ws`
- **Protocol**: JSON-based message exchange

### Supported Message Types

#### 1. Save Navigation Path

```json
{
  "type": "save_path",
  "data": {
    "sessionId": "session-123",
    "startCommand": "유튜브에서 음악 찾기",
    "completePath": [...]
  }
}
```

#### 2. Search Paths

```json
{
  "type": "search_path",
  "data": {
    "query": "유튜브에서 좋아요 한 음악 재생목록 여는 방법",
    "limit": 3,
    "domain_hint": "youtube.com"
  }
}
```

#### 3. Check Graph Structure

```json
{
  "type": "check_graph",
  "data": {}
}
```

#### 4. Find Popular Paths

```json
{
  "type": "find_popular_paths",
  "data": {
    "domain": "youtube.com",
    "limit": 10
  }
}
```

#### 5. Visualize Paths

```json
{
  "type": "visualize_paths",
  "data": {
    "domain": "youtube.com"
  }
}
```

## Architecture

```
[vowser-client] <=> [vowser-backend] <=> [vowser-mcp-server]
```

The MCP server serves as the "brain" of the system, handling:

- Web navigation path storage and analysis
- AI-powered semantic search
- Graph-based path recommendations
- Usage pattern analysis

### Core Components

- **FastAPI WebSocket Server** (`app/main.py`): Single `/ws` endpoint for real-time communication
- **Neo4j Graph Database** (`app/services/neo4j_service.py`): Graph structures for navigation paths
- **AI Services** (`app/services/`): LangChain integration for content analysis and embeddings
- **Data Models** (`app/models/path.py`): Pydantic models for data validation

### Graph Schema

- **ROOT**: Domain-level nodes (e.g., youtube.com)
- **PAGE**: Interactive elements with selectors and embeddings
- **PATH**: Complete navigation sequences with semantic search capability
- **Relationships**: HAS_PAGE, NAVIGATES_TO, NAVIGATES_TO_CROSS_DOMAIN, CONTAINS

## Development

### Project Structure

```
vowser-mcp-server/
├── app/                    # Main application
│   ├── main.py            # FastAPI WebSocket server
│   ├── models/            # Pydantic models
│   └── services/          # Business logic
├── docs/                  # Documentation
├── test/                  # Test files
└── requirements.txt       # Dependencies
```

### Testing Strategy

- `test_single.py`: Comprehensive WebSocket message testing
- All tests should pass with "5/5 성공" result
- Integration tests for Neo4j functionality

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Related Projects

- **vowser-backend**: Kotlin/Spring Boot central API gateway
- **vowser-client**: Kotlin Multiplatform user-facing application

For more detailed information, see [CLAUDE.md](CLAUDE.md).

## To-do List (임시)

### 🚀 시니어 AI 엔지니어 관점에서의 개발 로드맵

#### 📊 현재 프로젝트 상태 분석

**현재 아키텍처:**

- **FastAPI WebSocket 서버**: 8개 메시지 타입 지원하는 기본 API
- **Neo4j 그래프 DB**: 웹 탐색 경로를 그래프로 저장
- **LangChain 통합**: OpenAI/Gemini 모델로 임베딩 및 콘텐츠 분석
- **기본 MCP 구현**: 웹 크롤링과 경로 분석 기능

**기술적 한계:**

- LangGraph 미연결 (단일 LLM 호출만 가능)
- 복잡한 워크플로우 오케스트레이션 부재
- 에이전트 간 협업 메커니즘 없음
- 상태 관리 및 지속성 부족

#### 🎯 LangGraph 통합 전략

##### Phase 1: Core LangGraph Integration (2-3주)

**1.1 의존성 추가 및 기본 설정**

- `pyproject.toml`에 LangGraph 추가: `langgraph>=0.2.74`
- LangGraph 체크포인터 설정 (Neo4j 기반)
- 기본 상태 관리 구조 구축

**1.2 Multi-Agent 아키텍처 설계**

```python
# 예상 에이전트 구조
- WebCrawlerAgent: 웹 페이지 분석 전담
- PathAnalysisAgent: 네비게이션 경로 최적화
- UserInterfaceAgent: 사용자 인터랙션 처리
- KnowledgeGraphAgent: Neo4j 데이터 관리
```

**1.3 워크플로우 오케스트레이션**

- 각 WebSocket 메시지 타입을 LangGraph 워크플로우로 변환
- 병렬 처리가 가능한 작업들 식별 및 구현

##### Phase 2: Advanced Workflow Implementation (3-4주)

**2.1 Smart Path Discovery Workflow**

```python
@entrypoint()
def smart_path_discovery(query, domain_hint):
    # 1. 자연어 쿼리 분석
    query_analysis = analyze_user_intent(query).result()

    # 2. 병렬로 실행
    semantic_search = search_semantic_paths(query_analysis)
    graph_traversal = find_graph_patterns(query_analysis)

    # 3. 결과 통합 및 랭킹
    return rank_and_merge_results(
        semantic_search.result(),
        graph_traversal.result()
    ).result()
```

**2.2 Adaptive Web Analysis Workflow**

```python
@task
def analyze_page_structure(url):
    # AI 기반 페이지 구조 분석

@task
def extract_interactive_elements(html_content):
    # 상호작용 가능 요소 추출

@task
def generate_navigation_graph(page_data):
    # Neo4j 그래프 생성
```

**2.3 Human-in-the-Loop Integration**

- 사용자 피드백 루프 구현
- 경로 추천 품질 개선 메커니즘

##### Phase 3: Production-Ready Features (2-3주)

**3.1 Error Recovery & Resilience**

- LangGraph 체크포인터를 활용한 상태 복구
- 실패한 워크플로우 재시작 메커니즘

**3.2 Performance Optimization**

- 병렬 처리 최적화
- Neo4j 쿼리 성능 튜닝
- 캐싱 전략 구현

**3.3 Monitoring & Observability**

- LangSmith 통합으로 에이전트 실행 추적
- 메트릭 수집 및 대시보드 구축

#### 🛠️ 구체적인 구현 계획

##### 즉시 시작할 작업들:

**1. LangGraph 기본 통합** (`app/services/langgraph_service.py`)

```python
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import create_react_agent

class WebNavigationState(TypedDict):
    messages: list
    current_url: str
    target_action: str
    discovered_paths: list
    user_context: dict
```

**2. 기존 WebSocket 핸들러 리팩토링**

```python
# app/main.py에서
elif message['type'] == 'search_path':
    # 기존: neo4j_service.search_paths_by_query()
    # 신규: langgraph_workflow.smart_search_workflow()
```

**3. 새로운 워크플로우 엔드포인트 추가**

- `intelligent_path_discovery`: 멀티 에이전트 협업
- `adaptive_web_analysis`: 동적 페이지 분석
- `contextual_navigation`: 사용자 맥락 기반 추천

##### 아키텍처 개선 포인트:

**현재:** 단일 요청-응답 → **목표:** 지속적 대화형 워크플로우  
**현재:** 정적 경로 매칭 → **목표:** 동적 의도 파악 및 적응  
**현재:** 단일 LLM 호출 → **목표:** 전문화된 에이전트 협업

#### 📈 예상 성과

**단기 (2개월):**

- 50% 더 정확한 경로 추천
- 병렬 처리로 30% 응답 시간 단축
- 복잡한 다단계 탐색 시나리오 지원

**중장기 (6개월):**

- 완전 자율적인 웹 탐색 에이전트
- 실시간 사용자 의도 학습
- 크로스 도메인 지능형 경로 발견

이 로드맵을 통해 현재의 MVP를 **엔터프라이즈급 AI 에이전트 플랫폼**으로 발전시킬 수 있습니다.
