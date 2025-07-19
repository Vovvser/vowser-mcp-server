# TaskList - vowser-mcp-server

## Phase 1: MVP 핵심 기능 구현

### 1. Core Infrastructure Setup
- [ ] FastAPI 프로젝트 기본 설정
- [v] Neo4j 데이터베이스 연결 설정
- [v] 환경 변수 관리 (.env 파일)
- [ ] 기본 디렉토리 구조 생성

### 2. 기본 크롤링 시스템
- [ ] Playwright 설정 및 브라우저 초기화
- [ ] 단일 페이지 크롤링 함수 구현
- [ ] BeautifulSoup으로 HTML 파싱 (제목, 링크 추출)
- [ ] **깊이 제한 크롤링 (depth=3) 구현**
- [ ] URL 정규화 함수 구현
- [ ] 상대/절대 링크 처리 로직

### 3. Neo4j 데이터 모델링 및 저장
- [ ] 기본 노드 스키마 정의 (Page, Section)
- [ ] **Section 노드 자동 생성 로직**
  - [ ] 동일 카테고리 페이지 그룹핑 감지
  - [ ] Section 노드 생성 (예: "뉴스 섹션")
  - [ ] 하위 페이지들을 Section과 연결
  - [ ] Section 요약 정보 저장
- [ ] Page 노드 CRUD 함수 구현
- [ ] LINKS_TO 관계 생성 로직
- [ ] 중복 노드 방지 (MERGE 사용)

### 4. REST API 엔드포인트
- [ ] POST /crawl 엔드포인트 구현
- [ ] GET /graph/{job_id} 엔드포인트 구현
- [ ] 동기식 처리 로직 (FastAPI BackgroundTasks)
- [ ] 기본 에러 처리 및 응답 형식

### 5. Section 자동 인식 시스템
- [ ] **페이지 유사도 분석 알고리즘**
  - [ ] URL 패턴 분석 (예: `/news/article-1`, `/news/article-2`)
  - [ ] 페이지 구조 유사도 계산
  - [ ] 콘텐츠 카테고리 분석
- [ ] **Section 생성 조건 정의**
  - [ ] 유사한 페이지 3개 이상 발견 시 Section 생성
  - [ ] Section 제목 자동 생성 (URL 패턴 또는 공통 제목에서 추출)
  - [ ] Section 설명 자동 생성 ("뉴스 article 여러 개 포함")
- [ ] **Section-Page 관계 관리**
  - [ ] HAS_CONTENT 관계 생성
  - [ ] Section 내 페이지 샘플링 (대표 페이지 3-4개만 저장)

### 6. 테스트 및 검증
- [ ] 단일 페이지 크롤링 테스트
- [ ] 다중 페이지 크롤링 테스트 (depth=3)
- [ ] Section 자동 생성 테스트
- [ ] Neo4j 데이터 저장 검증
- [ ] API 엔드포인트 테스트

## Phase 1 기술적 결정사항

### Neo4j 데이터 모델
```cypher
// Page 노드
(:Page {
  url: String,
  title: String,
  content_preview: String,
  depth: Integer,
  created_at: DateTime
})

// Section 노드 (자동 생성)
(:Section {
  id: String,
  title: String,          // 예: "뉴스 섹션"
  description: String,    // 예: "뉴스 기사 12개 포함"
  url_pattern: String,    // 예: "/news/*"
  page_count: Integer,    // 해당 섹션의 총 페이지 수
  sample_pages: [String], // 대표 페이지 URL 목록
  created_at: DateTime
})

// 관계
(Page)-[:LINKS_TO]->(Page)
(Section)-[:HAS_CONTENT]->(Page)
```

### Section 자동 생성 로직
1. **패턴 감지**: 크롤링 중 유사한 URL 패턴 발견 시 (예: `/news/article-*`)
2. **임계값 확인**: 동일 패턴 페이지 3개 이상 발견 시 Section 생성
3. **샘플링**: 해당 섹션의 모든 페이지 대신 대표 페이지 3-4개만 저장
4. **메타데이터**: Section 노드에 전체 페이지 수와 설명 저장

### 제한사항 및 고려사항
- **깊이 제한**: depth=3으로 제한하여 무한 크롤링 방지
- **동기식 처리**: Celery 없이 FastAPI 내에서 동기 처리
- **에러 처리**: 페이지 로딩 실패, 타임아웃 등 기본 에러 처리
- **메모리 관리**: 크롤링 중 메모리 사용량 모니터링

## 예상 소요 시간
- **경험자**: 1-2주
- **신규 학습자**: 2-3주

## 다음 단계 (Phase 2)
- Celery 백그라운드 처리 도입
- WebSocket 실시간 진행 상황
- 기본 Bot 감지 우회
- LangChain 요약 기능