# vowser-mcp-server 리팩토링 계획

## 개요
현재 `app` 디렉토리의 코드베이스를 분석한 결과, 코드 구조 개선과 유지보수성 향상을 위한 리팩토링이 필요합니다.

## 우선순위별 리팩토링 항목

### 🔥 높은 우선순위

#### 1. WebSocket 핸들러 분리 (`app/main.py`)
**현재 문제점:**
- 160줄에 달하는 거대한 if-elif 체인 (라인 33-157)
- 단일 함수에서 모든 메시지 타입 처리
- 코드 가독성 및 테스트 어려움

**개선 방안:**
```python
# 새로운 구조 제안
app/handlers/
├── __init__.py
├── base_handler.py          # 공통 핸들러 인터페이스
├── path_handler.py          # save_path 처리
├── graph_handler.py         # check_graph, visualize_paths
├── search_handler.py        # search_path 처리
├── maintenance_handler.py   # cleanup_paths, create_indexes
└── router.py               # 메시지 라우팅 로직
```

#### 2. Neo4j 서비스 모듈 분할 (`app/services/neo4j_service.py`)
**현재 문제점:**
- 1000줄이 넘는 거대한 단일 파일
- 다양한 책임이 한 파일에 집중 (경로 저장, 검색, 분석, 정리)
- 함수 간 의존성 복잡

**개선 방안:**
```python
app/services/
├── neo4j/
│   ├── __init__.py
│   ├── connection.py        # Neo4j 연결 관리
│   ├── path_service.py      # PATH 엔티티 관련 (라인 595-681, 973-1005)
│   ├── search_service.py    # 검색 관련 (라인 683-924)
│   ├── graph_service.py     # 그래프 분석 (라인 366-496)
│   ├── cleanup_service.py   # 정리 작업 (라인 1007-1123)
│   └── query_builder.py     # 공통 쿼리 빌더
└── neo4j_service.py        # 기존 파일을 팩토리/파사드로 변경
```

### 🟡 중간 우선순위

#### 3. 응답 포맷터 분리
**현재 문제점:**
- `main.py`에서 각 핸들러마다 응답 구조 하드코딩
- JSON 직렬화 로직 중복 (라인 171-176)

**개선 방안:**
```python
app/formatters/
├── __init__.py
├── response_formatter.py   # 공통 응답 포맷터
├── path_formatter.py       # 경로 관련 응답
├── graph_formatter.py      # 그래프 관련 응답
└── search_formatter.py     # 검색 관련 응답
```

#### 4. 중복 코드 제거
**개선 대상:**
- Neo4j 쿼리 실행 패턴 (try-catch, 결과 처리)
- 노드/관계 생성 로직 공통화
- 에러 핸들링 표준화

#### 5. 타입 안정성 강화
**개선 사항:**
- `neo4j_service.py`의 딕셔너리 접근을 Pydantic 모델로 교체
- 네이밍 컨벤션 통일 (snake_case 일관성)
- 타입 힌트 추가

### 🟢 낮은 우선순위

#### 6. 환경설정 중앙화
**현재 문제점:**
- 여러 파일에 분산된 `load_dotenv()` 호출
- Neo4j 연결 설정 중복

**개선 방안:**
```python
app/config/
├── __init__.py
├── settings.py             # 환경변수 관리
├── database.py            # DB 연결 설정
└── constants.py           # 상수 정의
```

#### 7. 성능 최적화
**개선 사항:**
- `search_paths_by_query`의 Python 코사인 유사도를 Neo4j 벡터 검색으로 교체
- 쿼리 배치 처리 로직 추가
- 불필요한 데이터베이스 호출 최소화

## 구체적인 리팩토링 단계

### Phase 1: 핸들러 분리
1. `app/handlers/` 디렉토리 생성
2. 메시지 타입별 핸들러 클래스 구현
3. `main.py`의 WebSocket 엔드포인트를 라우터 패턴으로 변경
4. 기존 테스트 코드 검증

### Phase 2: Neo4j 서비스 분할
1. `app/services/neo4j/` 디렉토리 생성
2. 기능별 서비스 클래스 분리
3. 공통 인터페이스 및 베이스 클래스 구현
4. 의존성 주입 패턴 적용

### Phase 3: 공통 컴포넌트 정리
1. 응답 포맷터 구현
2. 설정 관리 중앙화
3. 에러 핸들링 표준화
4. 타입 안정성 개선

## 리팩토링 시 주의사항

### 호환성 유지
- 기존 WebSocket API 인터페이스 유지
- 현재 테스트 케이스 모두 통과 보장
- 데이터베이스 스키마 변경 없음

### 테스트 전략
- 각 Phase별로 기존 테스트 실행
- `test/test_single.py` 결과 "5/5 성공" 유지
- 리팩토링된 컴포넌트별 단위 테스트 추가

### 성능 영향 최소화
- 리팩토링 과정에서 성능 저하 방지
- 메모리 사용량 모니터링
- WebSocket 응답 시간 유지

## 예상 효과

### 코드 품질 향상
- 단일 책임 원칙 준수
- 코드 가독성 및 유지보수성 개선
- 테스트 용이성 향상

### 개발 생산성 향상
- 기능별 독립적 개발 가능
- 코드 재사용성 증대
- 새로운 기능 추가 용이

### 시스템 안정성 향상
- 타입 안정성 강화
- 에러 처리 일관성
- 성능 최적화 기반 마련