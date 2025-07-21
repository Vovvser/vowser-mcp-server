웹 크롤러 및 그래프 DB 구축 프로젝트 To-Do List
📝 1단계: 프로젝트 환경 설정 및 기본 크롤러 구현
[ ] Python 가상 환경 설정

[ ] 필수 라이브러리 설치 (playwright, beautifulsoup4, langchain, neo4j, python-dotenv)

[ ] Playwright용 브라우저 드라이버 설치 (playwright install)

[ ] Neo4j 데이터베이스 준비 (로컬 설치 또는 AuraDB 클라우드)

[ ] .env 파일에 LLM API 키 및 Neo4j 접속 정보 저장

[ ] (핵심) Playwright와 BeautifulSoup을 사용하여 단일 페이지의 모든 링크를 수집하는 기본 크롤러 함수 작성

[ ] 수집된 URL에서 중복 및 불필요한 파라미터 제거하는 전처리 로직 구현

🚀 2단계: 고급 크롤링 및 데이터 구조화
[ ] (중요) 동적 콘텐츠 로딩 대응: 특정 요소가 나타날 때까지 대기하거나, '더 보기' 버튼, 무한 스크롤 처리 로직 추가

[ ] 페이지네이션(Pagination) 처리: '다음' 버튼 등을 감지하고 클릭하여 여러 페이지를 순회하는 기능 구현

[ ] 크롤링 깊이(Depth)를 설정하여 무한정 크롤링되는 것을 방지

[ ] 크롤링 결과를 {'root_url': '...', 'child_urls': ['...', '...']} 와 같은 딕셔너리 형태로 구조화

[ ] 예외 처리 강화: 타임아웃, 404 에러 등 네트워크 오류 발생 시 로그를 남기고 다음 작업으로 넘어가도록 처리

🧠 3단계: LLM을 이용한 스마트 샘플링 및 섹션 분류
[ ] (핵심/가장 중요) 수집된 child_urls 리스트를 LLM에 전달하여 의미있는 '섹션(Section)'으로 그룹화하고, 각 섹션의 이름을 생성하도록 프롬프트 설계

프롬프트 예시: "다음 URL 리스트는 'naver.com'에서 수집되었습니다. 각 URL의 성격을 분석하여 '뉴스', '쇼핑', '블로그' 등과 같은 카테고리(섹션)로 묶고, 각 섹션의 이름을 제안해주세요. 결과는 JSON 형식으로..."

[ ] LangChain을 사용하여 LLM API 연동 및 프롬프트 실행 함수 구현

[ ] LLM이 반환한 JSON 결과를 파싱하여 {'root_url': '...', 'sections': {'뉴스': ['url1', 'url2'], '쇼핑': ['url3']}} 와 같은 최종 데이터 구조 생성

[ ] (스마트 샘플링) 각 섹션에 URL이 너무 많을 경우, 대표적인 URL 몇 개(예: 3~5개)만 남기는 샘플링 로직 구현 (예: random.sample)

🔗 4단계: Neo4j 데이터베이스 연동 및 저장
[ ] Python-Neo4j 드라이버를 사용하여 데이터베이스 연결 모듈 작성

[ ] 데이터 모델 정의:

Node Labels: Root, Section, Content

Node Properties:

Root: url (string)

Section: name (string)

Content: url (string)

Relationships: (Root)-[:HAS_SECTION]->(Section), (Section)-[:CONTAINS]->(Content)

[ ] (핵심) 3단계에서 생성된 최종 데이터 구조를 바탕으로 Cypher 쿼리를 생성하여 Neo4j에 노드와 관계를 저장하는 함수 구현

[ ] 데이터 중복 생성을 방지하기 위해 MERGE 쿼리 사용

✨ 5단계: 시각화 및 검증
[ ] Neo4j Browser에 접속하여 저장된 데이터가 의도한 트리 구조로 잘 생성되었는지 Cypher 쿼리로 확인

쿼리 예시: MATCH (r:Root {url: 'https://www.naver.com'})-[*]->(n) RETURN r, n

[ ] (선택) pyvis 라이브러리를 사용하여 Python 코드 내에서 직접 네트워크 그래프 시각화 구현

[ ] (선택) Flask 또는 FastAPI 같은 웹 프레임워크와 D3.js, vis.js 등을 연동하여 웹 기반의 인터랙티브 시각화 페이지 구축