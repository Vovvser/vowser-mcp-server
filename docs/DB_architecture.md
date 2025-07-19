# Neo4j 데이터베이스 아키텍처 설계 문서

## 📋 목차
1. [개요](#개요)
2. [데이터 모델링 철학](#데이터-모델링-철학)
3. [노드 타입 상세 설계](#노드-타입-상세-설계)
4. [관계 구조 상세 설계](#관계-구조-상세-설계)
5. [인덱스 및 제약 조건](#인덱스-및-제약-조건)
6. [Section 자동 생성 시스템](#section-자동-생성-시스템)
7. [페이징 처리 아키텍처](#페이징-처리-아키텍처)
8. [데이터 저장 최적화](#데이터-저장-최적화)
9. [쿼리 패턴 및 성능](#쿼리-패턴-및-성능)
10. [확장성 고려사항](#확장성-고려사항)

---

## 개요

### 🎯 목적
웹사이트의 계층적 구조를 그래프 데이터베이스로 모델링하여 손을 사용하기 어려운 사용자들이 효율적으로 웹사이트를 탐색할 수 있도록 지원하는 시스템의 데이터 아키텍처

### 🔧 기술 스택
- **데이터베이스**: Neo4j 5.x
- **쿼리 언어**: Cypher
- **연결 라이브러리**: LangChain-Neo4j
- **프로그래밍 언어**: Python 3.11

### 📊 데이터 모델링 원칙
1. **계층적 구조**: 웹사이트의 자연스러운 계층 구조 반영
2. **관계 중심**: 노드 간의 관계를 통한 탐색 경로 제공
3. **확장성**: 대용량 웹사이트 처리 가능한 구조
4. **접근성**: 사용자 친화적인 탐색 정보 제공
5. **지능형 검색**: textToCypher와 embedding 기반 의미 검색 지원
6. **자연어 질의**: 자연어를 Cypher 쿼리로 변환하는 기능

---

## 데이터 모델링 철학

### 🧠 설계 철학

#### 1. **계층적 웹 구조 반영**
```
웹사이트 실제 구조    →    Neo4j 노드 구조
─────────────────────────────────────────
Domain               →    ROOT
├─ Subdomain         →    SUBROOT
├─ Page (depth=1)    →    DEPTH
│  ├─ Header         →    SECTION
│  ├─ Navigation     →    SECTION
│  ├─ Content        →    SECTION
│  │  ├─ Article     →    ELEMENT
│  │  │  ├─ Title    →    CONTENT
│  │  │  └─ Link     →    CONTENT
│  │  └─ Pagination  →    SECTION (special)
│  └─ Footer         →    SECTION
└─ Page (depth=2)    →    DEPTH
```

#### 2. **관계 중심 탐색**
- 모든 노드는 명확한 관계를 통해 연결
- 탐색 경로 추적 가능
- 역방향 탐색 지원

#### 3. **메타데이터 중심 설계**
- 각 노드에 풍부한 메타데이터 저장
- AI 요약을 통한 접근성 향상
- 사용자 맞춤형 정보 제공

---

## 노드 타입 상세 설계

### 1. ROOT 노드 - 최상위 도메인

#### 🎯 목적
웹사이트의 최상위 도메인을 대표하는 노드

#### 📊 스키마
```cypher
(:ROOT {
  url: String,              // 완전한 URL (https://www.example.com)
  domain: String,           // 도메인만 (example.com)
  title: String,            // 웹사이트 제목
  description: String,      // 웹사이트 설명
  favicon_url: String,      // 파비콘 URL (선택사항)
  language: String,         // 주언어 (ko, en, etc.)
  created_at: DateTime,     // 생성 시간
  updated_at: DateTime,     // 마지막 업데이트 시간
  crawl_status: String,     // "completed", "in_progress", "failed"
  total_pages: Integer,     // 총 크롤링된 페이지 수
  crawl_depth: Integer,     // 크롤링 깊이
  last_crawled: DateTime    // 마지막 크롤링 시간
})
```

#### 🔍 사용 예시
```cypher
// ROOT 노드 생성
CREATE (root:ROOT {
  url: "https://www.naver.com",
  domain: "naver.com",
  title: "NAVER",
  description: "대한민국 최대 포털사이트",
  language: "ko",
  created_at: datetime(),
  updated_at: datetime(),
  crawl_status: "completed",
  total_pages: 156,
  crawl_depth: 3,
  last_crawled: datetime()
})
```

#### 🚀 최적화 고려사항
- `domain` 필드에 유니크 제약 조건 적용
- `url` 필드에 인덱스 생성
- `crawl_status` 필드로 크롤링 상태 관리

---

### 2. SUBROOT 노드 - 서브도메인

#### 🎯 목적
메인 도메인과 다른 서브도메인이나 외부 링크를 관리

#### 📊 스키마
```cypher
(:SUBROOT {
  url: String,              // 서브도메인 URL
  parent_domain: String,    // 부모 도메인
  subdomain: String,        // 서브도메인 부분 (news, blog, etc.)
  title: String,            // 서브도메인 제목
  description: String,      // 서브도메인 설명
  type: String,             // "subdomain", "external", "api"
  is_crawlable: Boolean,    // 크롤링 가능 여부
  created_at: DateTime,
  updated_at: DateTime,
  crawl_status: String,
  total_pages: Integer
})
```

#### 🔍 사용 예시
```cypher
// SUBROOT 노드 생성
CREATE (subroot:SUBROOT {
  url: "https://news.naver.com",
  parent_domain: "naver.com",
  subdomain: "news",
  title: "네이버 뉴스",
  description: "뉴스 전문 서비스",
  type: "subdomain",
  is_crawlable: true,
  created_at: datetime(),
  crawl_status: "completed",
  total_pages: 45
})

// ROOT와 SUBROOT 연결
MATCH (root:ROOT {domain: "naver.com"})
MATCH (subroot:SUBROOT {parent_domain: "naver.com"})
CREATE (root)-[:HAS_SUBROOT]->(subroot)
```

---

### 3. DEPTH 노드 - 페이지 깊이 관리

#### 🎯 목적
크롤링 깊이별 페이지 관리 및 페이징 처리

#### 📊 스키마
```cypher
(:DEPTH {
  level: Integer,           // 깊이 레벨 (1, 2, 3...)
  url: String,              // 페이지 URL
  title: String,            // 페이지 제목
  description: String,      // 페이지 설명
  content_preview: String,  // 콘텐츠 미리보기 (500자 이내)
  page_type: String,        // "index", "article", "list", "detail"
  
  // 페이징 관련 필드
  is_paginated: Boolean,    // 페이징 여부
  page_number: Integer,     // 현재 페이지 번호
  total_pages: Integer,     // 총 페이지 수
  pagination_type: String, // "numbered", "infinite", "load_more"
  
  // 메타데이터
  word_count: Integer,      // 단어 수
  load_time: Float,         // 로딩 시간 (초)
  status_code: Integer,     // HTTP 상태 코드
  content_type: String,     // MIME 타입
  
  // 시간 정보
  created_at: DateTime,
  updated_at: DateTime,
  last_accessed: DateTime
})
```

#### 🔍 사용 예시
```cypher
// DEPTH 노드 생성 (일반 페이지)
CREATE (depth:DEPTH {
  level: 2,
  url: "https://news.naver.com/sports",
  title: "스포츠 뉴스",
  description: "최신 스포츠 소식",
  content_preview: "오늘의 스포츠 뉴스를 확인하세요...",
  page_type: "list",
  is_paginated: true,
  page_number: 1,
  total_pages: 50,
  pagination_type: "numbered",
  word_count: 1500,
  load_time: 2.3,
  status_code: 200,
  content_type: "text/html",
  created_at: datetime(),
  last_accessed: datetime()
})

// 페이징 관계 생성
MATCH (page1:DEPTH {page_number: 1})
MATCH (page2:DEPTH {page_number: 2})
WHERE page1.url CONTAINS "sports" AND page2.url CONTAINS "sports"
CREATE (page1)-[:NEXT_PAGE]->(page2)
CREATE (page2)-[:PREV_PAGE]->(page1)
```

---

### 4. SECTION 노드 - 논리적 섹션 (핵심!)

#### 🎯 목적
웹페이지의 의미있는 구역을 표현하고 자동 그룹핑

#### 📊 스키마
```cypher
(:SECTION {
  id: String,               // UUID
  type: String,             // "header", "nav", "main", "aside", "footer", "paginated_list", "article_list", "search_results"
  title: String,            // 섹션 제목
  description: String,      // 섹션 설명
  text: String,             // 실제 텍스트 내용
  summary: String,          // AI가 생성한 요약
  
  // 위치 정보
  xpath: String,            // XPath 경로
  css_selector: String,     // CSS 선택자
  order: Integer,           // 페이지 내 순서
  
  // 자동 그룹핑 정보
  pattern_type: String,     // "url_pattern", "content_similarity", "dom_structure"
  url_pattern: String,      // URL 패턴 (예: "/news/article-*")
  similarity_score: Float,  // 유사도 점수 (0.0 - 1.0)
  
  // 페이징 관련 (페이징된 섹션인 경우)
  is_paginated: Boolean,
  total_pages: Integer,
  sampled_pages: [Integer], // 샘플링된 페이지 번호들
  pagination_url_pattern: String,
  sampling_strategy: String, // "all", "representative", "smart"
  
  // 콘텐츠 정보
  content_count: Integer,   // 하위 콘텐츠 수
  content_types: [String],  // 포함된 콘텐츠 타입들
  
  // 접근성 정보
  accessibility_level: String, // "easy", "medium", "hard"
  navigation_hint: String,     // 탐색 힌트
  keyboard_accessible: Boolean,
  
  // 메타데이터
  importance_score: Float,  // 중요도 점수
  user_interaction: String, // "high", "medium", "low"
  
  created_at: DateTime,
  updated_at: DateTime
})
```

#### 🔍 사용 예시

##### 일반 섹션 생성
```cypher
// 헤더 섹션
CREATE (header:SECTION {
  id: randomUUID(),
  type: "header",
  title: "사이트 헤더",
  description: "로고, 검색창, 메뉴가 포함된 상단 영역",
  text: "NAVER 검색 메일 카페 블로그",
  summary: "네이버 메인 서비스들에 대한 바로가기 링크 제공",
  xpath: "//header[@id='header']",
  css_selector: "#header",
  order: 1,
  pattern_type: "dom_structure",
  is_paginated: false,
  content_count: 8,
  content_types: ["logo", "search", "menu"],
  accessibility_level: "easy",
  navigation_hint: "Tab 키로 메뉴 간 이동 가능",
  keyboard_accessible: true,
  importance_score: 0.9,
  user_interaction: "high",
  created_at: datetime()
})
```

##### 페이징된 섹션 생성
```cypher
// 페이징된 뉴스 목록 섹션
CREATE (news_list:SECTION {
  id: randomUUID(),
  type: "paginated_list",
  title: "뉴스 목록",
  description: "최신 뉴스 기사들의 목록",
  text: "오늘의 주요 뉴스...",
  summary: "총 100페이지의 뉴스 기사 목록. 정치, 경제, 사회, 문화 등 다양한 분야의 최신 소식을 제공하며, 하루 평균 50개의 새로운 기사가 업데이트됩니다.",
  xpath: "//div[@class='news-list']",
  css_selector: ".news-list",
  order: 3,
  pattern_type: "url_pattern",
  url_pattern: "/news/list?page=*",
  is_paginated: true,
  total_pages: 100,
  sampled_pages: [1, 2, 3, 50, 100],
  pagination_url_pattern: "/news/list?page={page}",
  sampling_strategy: "smart",
  content_count: 20,
  content_types: ["article", "title", "summary", "link"],
  accessibility_level: "medium",
  navigation_hint: "방향키로 기사 간 이동, Enter로 선택",
  keyboard_accessible: true,
  importance_score: 0.8,
  user_interaction: "high",
  created_at: datetime()
})
```

---

### 5. ELEMENT 노드 - HTML 요소

#### 🎯 목적
개별 HTML 요소의 상세 정보 저장

#### 📊 스키마
```cypher
(:ELEMENT {
  id: String,               // UUID
  type: String,             // HTML 태그명 ("div", "article", "p", "img", etc.)
  class_name: String,       // CSS 클래스명
  element_id: String,       // HTML id 속성
  text: String,             // 요소의 텍스트 내용
  summary: String,          // AI 요약
  
  // 위치 정보
  xpath: String,            // XPath
  css_selector: String,     // CSS 선택자
  order: Integer,           // 부모 내 순서
  
  // 속성 정보
  attributes: Map,          // HTML 속성들 (key-value)
  
  // 콘텐츠 정보
  word_count: Integer,      // 단어 수
  has_children: Boolean,    // 하위 요소 존재 여부
  children_count: Integer,  // 하위 요소 수
  
  // 접근성 정보
  has_aria_label: Boolean,  // ARIA 라벨 존재 여부
  aria_role: String,        // ARIA 역할
  tab_index: Integer,       // 탭 인덱스
  
  created_at: DateTime,
  updated_at: DateTime
})
```

#### 🔍 사용 예시
```cypher
// 기사 요소 생성
CREATE (article:ELEMENT {
  id: randomUUID(),
  type: "article",
  class_name: "news-article",
  element_id: "article-12345",
  text: "AI 기술의 발전으로 인한 산업 변화...",
  summary: "AI 기술이 다양한 산업에 미치는 영향에 대한 분석 기사",
  xpath: "//article[@class='news-article'][1]",
  css_selector: ".news-article:first-child",
  order: 1,
  attributes: {
    "data-article-id": "12345",
    "data-category": "technology"
  },
  word_count: 245,
  has_children: true,
  children_count: 5,
  has_aria_label: true,
  aria_role: "article",
  tab_index: 0,
  created_at: datetime()
})
```

---

### 6. CONTENT 노드 - 최종 콘텐츠

#### 🎯 목적
사용자가 실제로 접근할 최종 콘텐츠 정보

#### 📊 스키마
```cypher
(:CONTENT {
  id: String,               // UUID
  type: String,             // "text", "link", "image", "video", "audio", "file"
  text: String,             // 콘텐츠 텍스트
  summary: String,          // AI 요약
  
  // 위치 정보
  xpath: String,
  css_selector: String,
  order: Integer,
  
  // 타입별 속성
  href: String,             // 링크인 경우 URL
  src: String,              // 이미지/비디오인 경우 소스 URL
  alt: String,              // 이미지 alt 텍스트
  title: String,            // 제목 속성
  
  // 메타데이터
  file_size: Integer,       // 파일 크기 (바이트)
  mime_type: String,        // MIME 타입
  
  // 링크 정보 (type이 "link"인 경우)
  link_type: String,        // "internal", "external", "mailto", "tel"
  target_domain: String,    // 대상 도메인
  is_download: Boolean,     // 다운로드 링크 여부
  
  // 접근성 정보
  accessibility_score: Float, // 접근성 점수
  screen_reader_text: String, // 스크린 리더용 텍스트
  
  // 상호작용 정보
  is_clickable: Boolean,    // 클릭 가능 여부
  requires_javascript: Boolean, // 자바스크립트 필요 여부
  
  created_at: DateTime,
  updated_at: DateTime
})
```

#### 🔍 사용 예시

##### 텍스트 콘텐츠
```cypher
CREATE (text_content:CONTENT {
  id: randomUUID(),
  type: "text",
  text: "인공지능 기술 발전의 새로운 전환점",
  summary: "AI 기술 발전에 대한 제목",
  xpath: "//h2[@class='article-title']",
  css_selector: ".article-title",
  order: 1,
  accessibility_score: 0.9,
  screen_reader_text: "기사 제목: 인공지능 기술 발전의 새로운 전환점",
  is_clickable: false,
  requires_javascript: false,
  created_at: datetime()
})
```

##### 링크 콘텐츠
```cypher
CREATE (link_content:CONTENT {
  id: randomUUID(),
  type: "link",
  text: "전체 기사 보기",
  summary: "해당 기사의 전문을 볼 수 있는 링크",
  xpath: "//a[@class='read-more']",
  css_selector: ".read-more",
  order: 2,
  href: "https://news.naver.com/article/detail/12345",
  title: "AI 기술 발전 기사 전문",
  link_type: "internal",
  target_domain: "news.naver.com",
  is_download: false,
  accessibility_score: 0.8,
  screen_reader_text: "링크: 전체 기사 보기, 새 페이지에서 열림",
  is_clickable: true,
  requires_javascript: false,
  created_at: datetime()
})
```

---

## 관계 구조 상세 설계

### 🔗 기본 계층 관계

#### 1. HAS_SUBROOT 관계
```cypher
(ROOT)-[:HAS_SUBROOT]->(SUBROOT)
```
**목적**: 메인 도메인과 서브도메인 연결

**속성**:
```cypher
{
  relationship_type: "subdomain",  // "subdomain", "external_link"
  created_at: DateTime,
  is_active: Boolean,
  crawl_priority: Integer          // 크롤링 우선순위 (1-10)
}
```

#### 2. HAS_DEPTH 관계
```cypher
(ROOT|SUBROOT)-[:HAS_DEPTH]->(DEPTH)
```
**목적**: 도메인과 깊이별 페이지 연결

**속성**:
```cypher
{
  depth_level: Integer,            // 깊이 레벨
  crawl_order: Integer,           // 크롤링 순서
  parent_url: String,             // 부모 페이지 URL
  created_at: DateTime
}
```

#### 3. HAS_SECTION 관계
```cypher
(DEPTH)-[:HAS_SECTION]->(SECTION)
```
**목적**: 페이지와 섹션 연결

**속성**:
```cypher
{
  section_position: String,        // "top", "middle", "bottom"
  visual_order: Integer,          // 시각적 순서
  extraction_confidence: Float,   // 추출 신뢰도
  created_at: DateTime
}
```

#### 4. HAS_ELEMENT 관계
```cypher
(SECTION)-[:HAS_ELEMENT]->(ELEMENT)
```
**목적**: 섹션과 요소 연결

**속성**:
```cypher
{
  element_importance: Float,       // 요소 중요도
  dom_depth: Integer,             // DOM 트리 깊이
  created_at: DateTime
}
```

#### 5. HAS_CONTENT 관계
```cypher
(ELEMENT)-[:HAS_CONTENT]->(CONTENT)
```
**목적**: 요소와 콘텐츠 연결

**속성**:
```cypher
{
  content_priority: Integer,       // 콘텐츠 우선순위
  user_interaction_score: Float,  // 사용자 상호작용 점수
  created_at: DateTime
}
```

### 🔀 탐색 관계

#### 1. LINKS_TO 관계
```cypher
(CONTENT)-[:LINKS_TO]->(ROOT|SUBROOT|DEPTH)
```
**목적**: 콘텐츠 간 링크 연결

**속성**:
```cypher
{
  link_type: String,              // "internal", "external", "anchor"
  link_text: String,              // 링크 텍스트
  confidence: Float,              // 링크 유효성 신뢰도
  last_checked: DateTime,         // 마지막 확인 시간
  status: String,                 // "active", "broken", "redirected"
  http_status: Integer,           // HTTP 상태 코드
  created_at: DateTime
}
```

#### 2. NEXT_DEPTH 관계
```cypher
(DEPTH)-[:NEXT_DEPTH]->(DEPTH)
```
**목적**: 깊이별 페이지 순서 관리

**속성**:
```cypher
{
  sequence_number: Integer,       // 순서 번호
  navigation_hint: String,        // 탐색 힌트
  created_at: DateTime
}
```

#### 3. NEXT_PAGE / PREV_PAGE 관계
```cypher
(DEPTH)-[:NEXT_PAGE]->(DEPTH)
(DEPTH)-[:PREV_PAGE]->(DEPTH)
```
**목적**: 페이징 관계 관리

**속성**:
```cypher
{
  page_diff: Integer,             // 페이지 차이
  pagination_type: String,        // "sequential", "jump"
  created_at: DateTime
}
```

### 🎯 특수 관계

#### 1. SIMILAR_TO 관계
```cypher
(SECTION)-[:SIMILAR_TO]->(SECTION)
```
**목적**: 유사한 섹션 간 연결

**속성**:
```cypher
{
  similarity_score: Float,        // 유사도 점수 (0.0 - 1.0)
  similarity_type: String,        // "content", "structure", "function"
  algorithm_used: String,         // 사용된 유사도 알고리즘
  created_at: DateTime
}
```

#### 2. GROUPED_BY 관계
```cypher
(DEPTH)-[:GROUPED_BY]->(SECTION)
```
**목적**: 자동 그룹핑된 페이지와 섹션 연결

**속성**:
```cypher
{
  group_confidence: Float,        // 그룹핑 신뢰도
  grouping_criteria: String,      // "url_pattern", "content_type", "structure"
  auto_generated: Boolean,        // 자동 생성 여부
  created_at: DateTime
}
```

---

## 인덱스 및 제약 조건

### 🔒 제약 조건 (Constraints)

#### 1. 유니크 제약 조건
```cypher
-- ROOT 노드 도메인 유니크
CREATE CONSTRAINT root_domain_unique IF NOT EXISTS
FOR (r:ROOT) REQUIRE r.domain IS UNIQUE

-- SUBROOT 노드 URL 유니크
CREATE CONSTRAINT subroot_url_unique IF NOT EXISTS
FOR (s:SUBROOT) REQUIRE s.url IS UNIQUE

-- DEPTH 노드 URL 유니크
CREATE CONSTRAINT depth_url_unique IF NOT EXISTS
FOR (d:DEPTH) REQUIRE d.url IS UNIQUE

-- SECTION 노드 ID 유니크
CREATE CONSTRAINT section_id_unique IF NOT EXISTS
FOR (s:SECTION) REQUIRE s.id IS UNIQUE

-- ELEMENT 노드 ID 유니크
CREATE CONSTRAINT element_id_unique IF NOT EXISTS
FOR (e:ELEMENT) REQUIRE e.id IS UNIQUE

-- CONTENT 노드 ID 유니크
CREATE CONSTRAINT content_id_unique IF NOT EXISTS
FOR (c:CONTENT) REQUIRE c.id IS UNIQUE
```

#### 2. 존재 제약 조건
```cypher
-- ROOT 노드 필수 필드
CREATE CONSTRAINT root_url_exists IF NOT EXISTS
FOR (r:ROOT) REQUIRE r.url IS NOT NULL

CREATE CONSTRAINT root_domain_exists IF NOT EXISTS
FOR (r:ROOT) REQUIRE r.domain IS NOT NULL

-- SECTION 노드 필수 필드
CREATE CONSTRAINT section_type_exists IF NOT EXISTS
FOR (s:SECTION) REQUIRE s.type IS NOT NULL

-- CONTENT 노드 필수 필드
CREATE CONSTRAINT content_type_exists IF NOT EXISTS
FOR (c:CONTENT) REQUIRE c.type IS NOT NULL
```

### 📊 인덱스 (Indexes)

#### 1. 기본 인덱스
```cypher
-- 자주 검색되는 필드들
CREATE INDEX root_url_index IF NOT EXISTS
FOR (r:ROOT) ON (r.url)

CREATE INDEX root_domain_index IF NOT EXISTS
FOR (r:ROOT) ON (r.domain)

CREATE INDEX depth_level_index IF NOT EXISTS
FOR (d:DEPTH) ON (d.level)

CREATE INDEX section_type_index IF NOT EXISTS
FOR (s:SECTION) ON (s.type)

CREATE INDEX content_type_index IF NOT EXISTS
FOR (c:CONTENT) ON (c.type)
```

#### 2. 복합 인덱스
```cypher
-- 페이징 관련
CREATE INDEX depth_pagination_index IF NOT EXISTS
FOR (d:DEPTH) ON (d.page_number, d.total_pages)

-- 섹션 중요도 관련
CREATE INDEX section_importance_index IF NOT EXISTS
FOR (s:SECTION) ON (s.importance_score, s.type)

-- 시간 기반 인덱스
CREATE INDEX created_at_index IF NOT EXISTS
FOR (n) ON (n.created_at) WHERE n.created_at IS NOT NULL
```

#### 3. 텍스트 인덱스
```cypher
-- 전문 검색을 위한 텍스트 인덱스
CREATE FULLTEXT INDEX section_text_index IF NOT EXISTS
FOR (s:SECTION) ON EACH [s.title, s.description, s.text, s.summary]

CREATE FULLTEXT INDEX content_text_index IF NOT EXISTS
FOR (c:CONTENT) ON EACH [c.text, c.summary]
```

---

## Section 자동 생성 시스템

### 🧠 자동 생성 알고리즘

#### 1. 패턴 감지 시스템

##### URL 패턴 분석
```python
class URLPatternAnalyzer:
    def __init__(self):
        self.patterns = {
            'article': r'/article/(\d+)',
            'news': r'/news/(\d+)',
            'post': r'/post/(\d+)',
            'page': r'/page/(\d+)',
            'category': r'/category/([^/]+)',
            'tag': r'/tag/([^/]+)',
            'date': r'/(\d{4})/(\d{2})/(\d{2})',
            'user': r'/user/([^/]+)',
            'product': r'/product/([^/]+)'
        }
    
    def analyze_urls(self, urls: List[str]) -> Dict[str, List[str]]:
        """URL 패턴 분석"""
        grouped_urls = {}
        for url in urls:
            pattern = self.identify_pattern(url)
            if pattern:
                if pattern not in grouped_urls:
                    grouped_urls[pattern] = []
                grouped_urls[pattern].append(url)
        return grouped_urls
    
    def identify_pattern(self, url: str) -> Optional[str]:
        """개별 URL의 패턴 식별"""
        for pattern_name, regex in self.patterns.items():
            if re.search(regex, url):
                return pattern_name
        return None
```

##### 구조 유사도 분석
```python
class StructureSimilarityAnalyzer:
    def __init__(self):
        self.similarity_threshold = 0.85
    
    def analyze_structure(self, pages: List[Dict]) -> Dict:
        """페이지 구조 유사도 분석"""
        similarity_matrix = self.calculate_similarity_matrix(pages)
        clusters = self.cluster_similar_pages(similarity_matrix)
        return self.create_section_candidates(clusters)
    
    def calculate_similarity_matrix(self, pages: List[Dict]) -> np.ndarray:
        """페이지 간 유사도 매트릭스 계산"""
        # DOM 구조 비교
        # 콘텐츠 타입 비교
        # 레이아웃 패턴 비교
        pass
    
    def cluster_similar_pages(self, similarity_matrix: np.ndarray) -> List[List[int]]:
        """유사한 페이지들을 클러스터링"""
        # 계층적 클러스터링 또는 DBSCAN 사용
        pass
```

#### 2. Section 생성 조건

##### 조건 1: 임계값 확인
```cypher
// 유사한 페이지 수 확인
MATCH (d:DEPTH)
WHERE d.url CONTAINS '/news/'
WITH count(d) as page_count
WHERE page_count >= 3
RETURN page_count
```

##### 조건 2: 구조 유사도 검증
```cypher
// 구조 유사도 기반 그룹핑
MATCH (d1:DEPTH), (d2:DEPTH)
WHERE d1.url CONTAINS '/news/' AND d2.url CONTAINS '/news/'
  AND d1.structure_hash = d2.structure_hash
WITH count(DISTINCT d1) as similar_pages
WHERE similar_pages >= 3
RETURN similar_pages
```

##### 조건 3: 콘텐츠 타입 일치
```cypher
// 콘텐츠 타입 기반 그룹핑
MATCH (d:DEPTH)
WHERE d.page_type = 'article'
WITH d.content_category as category, count(d) as page_count
WHERE page_count >= 3
RETURN category, page_count
```

#### 3. Section 자동 생성 프로세스

##### 단계 1: 패턴 감지
```cypher
// 1. URL 패턴 분석
MATCH (d:DEPTH)
WHERE d.url =~ '.*/news/article-\\d+.*'
WITH d
ORDER BY d.url
LIMIT 100

// 2. 패턴 검증
WITH collect(d) as articles
WHERE size(articles) >= 3

// 3. Section 생성
CREATE (s:SECTION {
  id: randomUUID(),
  type: "article_list",
  title: "뉴스 기사 섹션",
  description: "뉴스 기사 " + size(articles) + "개 포함",
  pattern_type: "url_pattern",
  url_pattern: "/news/article-*",
  content_count: size(articles),
  is_paginated: false,
  auto_generated: true,
  created_at: datetime()
})

// 4. 관계 생성
WITH s, articles
UNWIND articles as article
CREATE (article)-[:GROUPED_BY]->(s)
```

##### 단계 2: 샘플링 전략
```cypher
// 대표 페이지 선택
MATCH (d:DEPTH)-[:GROUPED_BY]->(s:SECTION)
WHERE s.id = $section_id
WITH d, s
ORDER BY d.importance_score DESC, d.created_at DESC
LIMIT 5

// 샘플 페이지 설정
SET s.sample_pages = collect(d.url)
```

##### 단계 3: 요약 생성
```python
async def generate_section_summary(section_id: str, sample_pages: List[str]) -> str:
    """Section 요약 생성"""
    # 샘플 페이지들의 내용 분석
    content_analysis = await analyze_sample_contents(sample_pages)
    
    # LangChain을 통한 요약 생성
    prompt = f"""
    다음은 {len(sample_pages)}개의 웹페이지 샘플 분석 결과입니다:
    
    공통 주제: {content_analysis['common_topics']}
    콘텐츠 타입: {content_analysis['content_types']}
    업데이트 빈도: {content_analysis['update_frequency']}
    사용자 관심도: {content_analysis['user_interest']}
    
    이 섹션의 특징과 포함된 콘텐츠를 100자 이내로 요약해주세요.
    """
    
    summary = await langchain_service.generate_summary(prompt)
    
    # Section 노드 업데이트
    query = """
    MATCH (s:SECTION {id: $section_id})
    SET s.summary = $summary,
        s.updated_at = datetime()
    """
    
    await neo4j_service.run_query(query, {
        'section_id': section_id,
        'summary': summary
    })
    
    return summary
```

---

## 페이징 처리 아키텍처

### 🔄 페이징 감지 시스템

#### 1. 감지 방법들

##### DOM 기반 감지
```python
class DOMPaginationDetector:
    def __init__(self):
        self.pagination_selectors = [
            '.pagination',
            '.paging',
            '.page-navigation',
            'nav[aria-label*="page"]',
            '[class*="page-number"]',
            '.next-page',
            '.prev-page',
            '[rel="next"]',
            '[rel="prev"]',
            '.page-link'
        ]
    
    def detect_pagination(self, soup: BeautifulSoup) -> Optional[Dict]:
        """DOM 기반 페이징 감지"""
        for selector in self.pagination_selectors:
            elements = soup.select(selector)
            if elements:
                return self.extract_pagination_info(elements[0])
        return None
    
    def extract_pagination_info(self, element) -> Dict:
        """페이징 정보 추출"""
        info = {
            'type': 'dom_based',
            'total_pages': self.extract_total_pages(element),
            'current_page': self.extract_current_page(element),
            'next_page_url': self.extract_next_page_url(element),
            'prev_page_url': self.extract_prev_page_url(element)
        }
        return info
```

##### URL 패턴 감지
```python
class URLPatternDetector:
    def __init__(self):
        self.url_patterns = [
            r'[?&]page=(\d+)',
            r'[?&]p=(\d+)',
            r'/page/(\d+)',
            r'[?&]offset=(\d+)',
            r'[?&]start=(\d+)',
            r'[?&]pageNum=(\d+)',
            r'[?&]pageNumber=(\d+)'
        ]
    
    def detect_pagination(self, current_url: str, links: List[str]) -> Optional[Dict]:
        """URL 패턴 기반 페이징 감지"""
        for pattern in self.url_patterns:
            if self.analyze_pattern(current_url, links, pattern):
                return self.extract_pattern_info(current_url, links, pattern)
        return None
    
    def analyze_pattern(self, current_url: str, links: List[str], pattern: str) -> bool:
        """패턴 분석"""
        current_match = re.search(pattern, current_url)
        if not current_match:
            return False
        
        # 다른 페이지 링크들에서 같은 패턴 확인
        pattern_matches = 0
        for link in links:
            if re.search(pattern, link):
                pattern_matches += 1
        
        return pattern_matches >= 2  # 최소 2개 이상의 패턴 매치
```

#### 2. 페이징 정보 저장

##### 페이징 메타데이터 저장
```cypher
// 페이징된 SECTION 생성
CREATE (s:SECTION {
  id: randomUUID(),
  type: "paginated_list",
  title: "뉴스 목록",
  description: "뉴스 기사 목록 (페이징됨)",
  is_paginated: true,
  
  // 페이징 정보
  total_pages: 100,
  current_page: 1,
  pages_per_section: 20,
  pagination_type: "numbered",
  
  // URL 패턴
  base_url: "https://news.example.com/list",
  pagination_url_pattern: "https://news.example.com/list?page={page}",
  
  // 샘플링 정보
  sampling_strategy: "smart",
  sampled_pages: [1, 2, 3, 25, 50, 75, 100],
  
  created_at: datetime()
})

// 각 페이지를 DEPTH 노드로 생성
UNWIND [1, 2, 3, 25, 50, 75, 100] as page_num
CREATE (d:DEPTH {
  level: 1,
  url: "https://news.example.com/list?page=" + toString(page_num),
  title: "뉴스 목록 - " + toString(page_num) + "페이지",
  page_number: page_num,
  is_paginated: true,
  parent_section_id: s.id,
  created_at: datetime()
})
CREATE (s)-[:HAS_DEPTH]->(d)
```

##### 페이지 간 관계 설정
```cypher
// 순차적 페이지 관계
MATCH (d1:DEPTH {page_number: 1})-[:HAS_DEPTH]-(s:SECTION),
      (d2:DEPTH {page_number: 2})-[:HAS_DEPTH]-(s)
CREATE (d1)-[:NEXT_PAGE {page_diff: 1}]->(d2)
CREATE (d2)-[:PREV_PAGE {page_diff: 1}]->(d1)

// 점프 페이지 관계
MATCH (d1:DEPTH {page_number: 1})-[:HAS_DEPTH]-(s:SECTION),
      (d100:DEPTH {page_number: 100})-[:HAS_DEPTH]-(s)
CREATE (d1)-[:NEXT_PAGE {page_diff: 99, pagination_type: "jump"}]->(d100)
```

### 🎯 적응형 샘플링 전략

#### 1. 샘플링 전략 결정
```python
class SamplingStrategyDecider:
    def __init__(self):
        self.strategies = {
            'all': self.sample_all_pages,
            'representative': self.sample_representative_pages,
            'smart': self.sample_smart_pages,
            'first_n': self.sample_first_n_pages,
            'boundary': self.sample_boundary_pages
        }
    
    def determine_strategy(self, total_pages: int, content_type: str, 
                         user_priority: str = 'balanced') -> str:
        """샘플링 전략 결정"""
        if total_pages <= 5:
            return 'all'
        elif content_type in ['news', 'feed', 'updates'] and user_priority == 'latest':
            return 'first_n'
        elif total_pages <= 20:
            return 'representative'
        elif content_type in ['archive', 'search_results']:
            return 'boundary'
        else:
            return 'smart'
    
    def sample_all_pages(self, total_pages: int) -> List[int]:
        """모든 페이지 샘플링"""
        return list(range(1, total_pages + 1))
    
    def sample_representative_pages(self, total_pages: int) -> List[int]:
        """대표 페이지 샘플링"""
        if total_pages <= 10:
            return [1, 2, 3, total_pages]
        else:
            mid = total_pages // 2
            return [1, 2, 3, mid, total_pages]
    
    def sample_smart_pages(self, total_pages: int) -> List[int]:
        """스마트 샘플링"""
        if total_pages <= 50:
            return [1, 2, 3, 10, 20, total_pages]
        else:
            return [1, 2, 3, 10, 25, 50, total_pages // 2, total_pages]
    
    def sample_first_n_pages(self, total_pages: int, n: int = 5) -> List[int]:
        """처음 N개 페이지 샘플링"""
        return list(range(1, min(n + 1, total_pages + 1)))
    
    def sample_boundary_pages(self, total_pages: int) -> List[int]:
        """경계 페이지 샘플링"""
        if total_pages <= 10:
            return [1, 2, total_pages - 1, total_pages]
        else:
            return [1, 2, 3, total_pages - 2, total_pages - 1, total_pages]
```

#### 2. 샘플링 실행 및 저장
```python
async def execute_sampling_strategy(section_id: str, strategy: str, 
                                   total_pages: int, base_url: str):
    """샘플링 전략 실행"""
    decider = SamplingStrategyDecider()
    sampled_pages = decider.strategies[strategy](total_pages)
    
    # 샘플 페이지 크롤링
    for page_num in sampled_pages:
        page_url = base_url.replace('{page}', str(page_num))
        
        # 페이지 크롤링
        page_content = await crawl_page(page_url)
        
        # DEPTH 노드 생성
        query = """
        MATCH (s:SECTION {id: $section_id})
        CREATE (d:DEPTH {
          level: 1,
          url: $page_url,
          title: $page_title,
          page_number: $page_num,
          is_paginated: true,
          content_preview: $content_preview,
          word_count: $word_count,
          created_at: datetime()
        })
        CREATE (s)-[:HAS_DEPTH {sampling_strategy: $strategy}]->(d)
        """
        
        await neo4j_service.run_query(query, {
            'section_id': section_id,
            'page_url': page_url,
            'page_title': page_content['title'],
            'page_num': page_num,
            'content_preview': page_content['preview'][:500],
            'word_count': page_content['word_count'],
            'strategy': strategy
        })
```

---

## 데이터 저장 최적화

### 🚀 성능 최적화 전략

#### 1. 배치 처리
```python
class BatchProcessor:
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
        self.pending_nodes = []
        self.pending_relationships = []
    
    async def add_node(self, node_data: Dict):
        """노드 배치에 추가"""
        self.pending_nodes.append(node_data)
        if len(self.pending_nodes) >= self.batch_size:
            await self.flush_nodes()
    
    async def add_relationship(self, rel_data: Dict):
        """관계 배치에 추가"""
        self.pending_relationships.append(rel_data)
        if len(self.pending_relationships) >= self.batch_size:
            await self.flush_relationships()
    
    async def flush_nodes(self):
        """노드 배치 처리"""
        if not self.pending_nodes:
            return
        
        # 노드 타입별 분류
        nodes_by_type = {}
        for node in self.pending_nodes:
            node_type = node['type']
            if node_type not in nodes_by_type:
                nodes_by_type[node_type] = []
            nodes_by_type[node_type].append(node)
        
        # 타입별 배치 생성
        for node_type, nodes in nodes_by_type.items():
            query = f"""
            UNWIND $nodes as node
            CREATE (n:{node_type})
            SET n = node.properties
            """
            await neo4j_service.run_query(query, {'nodes': nodes})
        
        self.pending_nodes.clear()
    
    async def flush_relationships(self):
        """관계 배치 처리"""
        if not self.pending_relationships:
            return
        
        # 관계 타입별 처리
        rels_by_type = {}
        for rel in self.pending_relationships:
            rel_type = rel['type']
            if rel_type not in rels_by_type:
                rels_by_type[rel_type] = []
            rels_by_type[rel_type].append(rel)
        
        for rel_type, rels in rels_by_type.items():
            query = f"""
            UNWIND $rels as rel
            MATCH (from {{id: rel.from_id}})
            MATCH (to {{id: rel.to_id}})
            CREATE (from)-[r:{rel_type}]->(to)
            SET r = rel.properties
            """
            await neo4j_service.run_query(query, {'rels': rels})
        
        self.pending_relationships.clear()
```

#### 2. 메모리 효율성
```python
class MemoryOptimizedStorage:
    def __init__(self, max_memory_mb: int = 512):
        self.max_memory_mb = max_memory_mb
        self.current_memory_usage = 0
        self.text_compression = True
        self.image_optimization = True
    
    def optimize_text_content(self, text: str) -> str:
        """텍스트 콘텐츠 최적화"""
        if not text:
            return text
        
        # 중복 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 특수 문자 정리
        text = re.sub(r'[^\w\s\-.,!?()]', '', text)
        
        # 길이 제한
        if len(text) > 5000:
            text = text[:5000] + "..."
        
        return text.strip()
    
    def calculate_storage_size(self, data: Dict) -> int:
        """데이터 저장 크기 계산"""
        import sys
        return sys.getsizeof(str(data))
    
    async def store_with_memory_check(self, data: Dict):
        """메모리 체크 후 저장"""
        data_size = self.calculate_storage_size(data)
        
        if self.current_memory_usage + data_size > self.max_memory_mb * 1024 * 1024:
            # 메모리 정리
            await self.cleanup_memory()
        
        # 데이터 최적화
        optimized_data = self.optimize_data(data)
        
        # 저장
        await self.store_data(optimized_data)
        
        self.current_memory_usage += data_size
    
    def optimize_data(self, data: Dict) -> Dict:
        """데이터 최적화"""
        optimized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                optimized[key] = self.optimize_text_content(value)
            elif isinstance(value, list) and len(value) > 100:
                # 큰 리스트는 샘플링
                optimized[key] = value[:50] + value[-50:]
            else:
                optimized[key] = value
        
        return optimized
```

#### 3. 중복 제거
```cypher
-- 중복 노드 방지를 위한 MERGE 사용
MERGE (r:ROOT {domain: $domain})
ON CREATE SET 
  r.url = $url,
  r.title = $title,
  r.created_at = datetime()
ON MATCH SET 
  r.updated_at = datetime(),
  r.last_crawled = datetime()

-- 중복 관계 방지
MATCH (from {id: $from_id}), (to {id: $to_id})
MERGE (from)-[r:LINKS_TO]->(to)
ON CREATE SET 
  r.created_at = datetime(),
  r.link_text = $link_text
ON MATCH SET 
  r.last_checked = datetime(),
  r.status = $status
```

---

## 지능형 검색 시스템 (textToCypher & Embedding)

### 🤖 textToCypher 시스템

#### 1. 자연어 질의 처리
```python
class TextToCypherProcessor:
    def __init__(self, langchain_service):
        self.langchain = langchain_service
        self.query_templates = {
            'find_content': "MATCH (c:CONTENT) WHERE c.text CONTAINS $search_term RETURN c",
            'find_section': "MATCH (s:SECTION) WHERE s.title CONTAINS $search_term RETURN s",
            'navigation_path': "MATCH path = (root:ROOT)-[:HAS_DEPTH*1..3]->(depth:DEPTH) WHERE root.domain = $domain RETURN path"
        }
    
    async def process_natural_query(self, query: str, domain: str) -> str:
        """자연어 질의를 Cypher 쿼리로 변환"""
        prompt = f"""
        다음 자연어 질의를 Neo4j Cypher 쿼리로 변환하세요:
        
        질의: {query}
        대상 도메인: {domain}
        
        사용 가능한 노드 타입:
        - ROOT: 웹사이트 루트 (domain, title, description)
        - SECTION: 페이지 섹션 (title, summary, type, is_paginated)
        - CONTENT: 최종 콘텐츠 (text, type, href)
        
        관계:
        - HAS_DEPTH, HAS_SECTION, HAS_CONTENT, LINKS_TO
        """
        
        cypher_query = await self.langchain.generate_cypher(prompt)
        return self.validate_and_sanitize_query(cypher_query)
    
    def validate_and_sanitize_query(self, query: str) -> str:
        """쿼리 검증 및 정리"""
        # 보안 검증
        dangerous_keywords = ['DROP', 'DELETE', 'DETACH', 'REMOVE', 'SET', 'CREATE']
        for keyword in dangerous_keywords:
            if keyword in query.upper():
                raise ValueError(f"Dangerous keyword '{keyword}' detected")
        
        # 쿼리 정리
        query = query.strip()
        if not query.upper().startswith('MATCH'):
            raise ValueError("Query must start with MATCH")
        
        return query
```

#### 2. 쿼리 실행 및 결과 처리
```python
class QueryExecutor:
    def __init__(self, neo4j_service, text_to_cypher):
        self.neo4j = neo4j_service
        self.text_to_cypher = text_to_cypher
    
    async def execute_natural_query(self, natural_query: str, domain: str) -> dict:
        """자연어 질의 실행"""
        try:
            # 1. 자연어를 Cypher로 변환
            cypher_query = await self.text_to_cypher.process_natural_query(
                natural_query, domain
            )
            
            # 2. 쿼리 실행
            results = await self.neo4j.run_query(cypher_query, {'domain': domain})
            
            # 3. 결과 후처리
            formatted_results = self.format_results(results)
            
            return {
                'query': natural_query,
                'cypher': cypher_query,
                'results': formatted_results,
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'query': natural_query,
                'error': str(e),
                'status': 'error'
            }
    
    def format_results(self, raw_results: list) -> list:
        """결과 포맷팅"""
        formatted = []
        for result in raw_results:
            if 'c' in result:  # CONTENT 노드
                formatted.append({
                    'type': 'content',
                    'text': result['c']['text'],
                    'content_type': result['c']['type']
                })
            elif 's' in result:  # SECTION 노드
                formatted.append({
                    'type': 'section',
                    'title': result['s']['title'],
                    'summary': result['s']['summary']
                })
        return formatted
```

### 🔍 Embedding 기반 의미 검색

#### 1. 노드 임베딩 필드 추가
```cypher
-- SECTION 노드에 임베딩 필드 추가
ALTER TABLE SECTION ADD COLUMN embedding VECTOR(1536);

-- CONTENT 노드에 임베딩 필드 추가  
ALTER TABLE CONTENT ADD COLUMN embedding VECTOR(1536);

-- 임베딩 벡터 인덱스 생성
CREATE VECTOR INDEX section_embedding_index 
FOR (s:SECTION) ON (s.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};

CREATE VECTOR INDEX content_embedding_index 
FOR (c:CONTENT) ON (c.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};
```

#### 2. 임베딩 생성 시스템
```python
class EmbeddingGenerator:
    def __init__(self, openai_client):
        self.openai = openai_client
        self.model = "text-embedding-3-small"
    
    async def generate_embedding(self, text: str) -> list:
        """텍스트의 임베딩 벡터 생성"""
        response = await self.openai.embeddings.create(
            model=self.model,
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding
    
    async def update_node_embeddings(self, node_type: str, batch_size: int = 100):
        """노드 임베딩 일괄 업데이트"""
        offset = 0
        while True:
            # 노드 배치 조회
            query = f"""
            MATCH (n:{node_type})
            WHERE n.embedding IS NULL
            RETURN n.id as id, n.text as text, n.summary as summary
            ORDER BY n.created_at
            SKIP {offset} LIMIT {batch_size}
            """
            
            results = await self.neo4j.run_query(query)
            if not results:
                break
            
            # 임베딩 생성 및 업데이트
            for result in results:
                text_content = result['text'] or result['summary'] or ""
                if text_content:
                    embedding = await self.generate_embedding(text_content)
                    
                    update_query = f"""
                    MATCH (n:{node_type} {{id: $id}})
                    SET n.embedding = $embedding
                    """
                    
                    await self.neo4j.run_query(update_query, {
                        'id': result['id'],
                        'embedding': embedding
                    })
            
            offset += batch_size
```

#### 3. 의미 기반 검색 쿼리
```cypher
-- 의미 검색 쿼리 (섹션)
CALL db.index.vector.queryNodes('section_embedding_index', 10, $query_embedding)
YIELD node as s, score
MATCH (s)-[:HAS_ELEMENT]->(e:ELEMENT)-[:HAS_CONTENT]->(c:CONTENT)
RETURN s.title, s.summary, score, collect(c.text)[0..3] as sample_content
ORDER BY score DESC
LIMIT 5;

-- 의미 검색 쿼리 (콘텐츠)
CALL db.index.vector.queryNodes('content_embedding_index', 10, $query_embedding)
YIELD node as c, score
MATCH (s:SECTION)-[:HAS_ELEMENT]->(e:ELEMENT)-[:HAS_CONTENT]->(c)
RETURN c.text, c.type, s.title as section_title, score
ORDER BY score DESC
LIMIT 10;
```

#### 4. 하이브리드 검색 시스템
```python
class HybridSearchSystem:
    def __init__(self, neo4j_service, embedding_generator):
        self.neo4j = neo4j_service
        self.embedding_gen = embedding_generator
    
    async def hybrid_search(self, query: str, domain: str, top_k: int = 10) -> dict:
        """하이브리드 검색: 키워드 + 임베딩 검색"""
        # 1. 검색 쿼리 임베딩 생성
        query_embedding = await self.embedding_gen.generate_embedding(query)
        
        # 2. 키워드 검색
        keyword_results = await self.keyword_search(query, domain)
        
        # 3. 임베딩 검색
        embedding_results = await self.embedding_search(query_embedding, domain)
        
        # 4. 결과 통합 및 재정렬
        combined_results = self.combine_results(keyword_results, embedding_results)
        
        return {
            'query': query,
            'keyword_results': keyword_results,
            'embedding_results': embedding_results,
            'combined_results': combined_results
        }
    
    async def keyword_search(self, query: str, domain: str) -> list:
        """키워드 기반 검색"""
        cypher_query = """
        MATCH (root:ROOT {domain: $domain})-[:HAS_DEPTH*1..3]->(depth:DEPTH)
              -[:HAS_SECTION]->(s:SECTION)
              -[:HAS_ELEMENT]->(e:ELEMENT)
              -[:HAS_CONTENT]->(c:CONTENT)
        WHERE c.text CONTAINS $query OR s.title CONTAINS $query
        RETURN s.title, s.summary, c.text, 'keyword' as search_type
        ORDER BY s.importance_score DESC
        LIMIT 10
        """
        
        return await self.neo4j.run_query(cypher_query, {
            'domain': domain,
            'query': query
        })
    
    async def embedding_search(self, query_embedding: list, domain: str) -> list:
        """임베딩 기반 검색"""
        cypher_query = """
        MATCH (root:ROOT {domain: $domain})-[:HAS_DEPTH*1..3]->(depth:DEPTH)
              -[:HAS_SECTION]->(s:SECTION)
        WHERE s.embedding IS NOT NULL
        CALL db.index.vector.queryNodes('section_embedding_index', 10, $query_embedding)
        YIELD node as similar_section, score
        WHERE similar_section = s
        RETURN s.title, s.summary, score, 'embedding' as search_type
        ORDER BY score DESC
        LIMIT 10
        """
        
        return await self.neo4j.run_query(cypher_query, {
            'domain': domain,
            'query_embedding': query_embedding
        })
    
    def combine_results(self, keyword_results: list, embedding_results: list) -> list:
        """검색 결과 통합"""
        # 결과 정규화 및 점수 계산
        combined = []
        
        # 키워드 결과 (정확도 높음)
        for result in keyword_results:
            combined.append({
                'title': result['s.title'],
                'summary': result['s.summary'],
                'score': 1.0,  # 키워드 매치는 높은 점수
                'type': 'keyword'
            })
        
        # 임베딩 결과 (의미적 유사성)
        for result in embedding_results:
            combined.append({
                'title': result['s.title'],
                'summary': result['s.summary'],
                'score': result['score'] * 0.8,  # 임베딩 점수 조정
                'type': 'embedding'
            })
        
        # 중복 제거 및 점수 기준 정렬
        unique_results = self.deduplicate_by_title(combined)
        return sorted(unique_results, key=lambda x: x['score'], reverse=True)
    
    def deduplicate_by_title(self, results: list) -> list:
        """제목 기준 중복 제거"""
        seen_titles = set()
        unique_results = []
        
        for result in results:
            if result['title'] not in seen_titles:
                seen_titles.add(result['title'])
                unique_results.append(result)
        
        return unique_results
```

---

## 쿼리 패턴 및 성능

### 🔍 자주 사용되는 쿼리 패턴

#### 1. 웹사이트 구조 조회
```cypher
-- 전체 웹사이트 구조 조회
MATCH path = (root:ROOT)-[:HAS_DEPTH*1..3]->(depth:DEPTH)
             -[:HAS_SECTION]->(section:SECTION)
WHERE root.domain = $domain
RETURN path
ORDER BY depth.level, section.order
LIMIT 100
```

#### 2. 페이징된 섹션 검색
```cypher
-- 페이징된 섹션 찾기
MATCH (s:SECTION)
WHERE s.is_paginated = true 
  AND s.total_pages > $min_pages
  AND s.summary CONTAINS $search_term
RETURN s.title, s.summary, s.total_pages, s.sampled_pages
ORDER BY s.importance_score DESC
LIMIT 10
```

#### 3. 콘텐츠 탐색 경로
```cypher
-- 특정 콘텐츠까지의 경로 찾기
MATCH path = (root:ROOT)-[:HAS_DEPTH*1..3]->(depth:DEPTH)
             -[:HAS_SECTION]->(section:SECTION)
             -[:HAS_ELEMENT]->(element:ELEMENT)
             -[:HAS_CONTENT]->(content:CONTENT)
WHERE root.domain = $domain
  AND content.text CONTAINS $search_term
RETURN path, length(path) as path_length
ORDER BY path_length, content.accessibility_score DESC
LIMIT 5
```

#### 4. 유사 콘텐츠 찾기
```cypher
-- 유사한 섹션 찾기
MATCH (s1:SECTION)-[:SIMILAR_TO]->(s2:SECTION)
WHERE s1.id = $section_id
  AND s2.similarity_score > $threshold
RETURN s2.title, s2.description, s2.similarity_score
ORDER BY s2.similarity_score DESC
```

### ⚡ 성능 최적화 쿼리

#### 1. 인덱스 활용 쿼리
```cypher
-- 인덱스를 활용한 빠른 검색
USING INDEX root:ROOT(domain)
MATCH (root:ROOT)
WHERE root.domain = $domain
RETURN root
```

#### 2. 제한된 깊이 탐색
```cypher
-- 깊이 제한으로 성능 향상
MATCH path = (root:ROOT)-[:HAS_DEPTH*1..2]->(depth:DEPTH)
WHERE root.domain = $domain
WITH path, depth
ORDER BY depth.importance_score DESC
LIMIT 50
RETURN path
```

#### 3. 집계 쿼리 최적화
```cypher
-- 효율적인 통계 쿼리
MATCH (root:ROOT {domain: $domain})
       -[:HAS_DEPTH]->(depth:DEPTH)
       -[:HAS_SECTION]->(section:SECTION)
RETURN 
  count(DISTINCT depth) as total_pages,
  count(DISTINCT section) as total_sections,
  count(DISTINCT section) FILTER (WHERE section.is_paginated = true) as paginated_sections,
  avg(section.importance_score) as avg_importance
```

---

## 확장성 고려사항

### 🌐 수평적 확장

#### 1. 샤딩 전략
```python
class Neo4jShardManager:
    def __init__(self, shard_configs: List[Dict]):
        self.shards = {}
        for config in shard_configs:
            self.shards[config['name']] = Neo4jConnection(config)
    
    def get_shard_for_domain(self, domain: str) -> str:
        """도메인 기반 샤드 선택"""
        # 도메인 해시 기반 샤딩
        hash_value = hash(domain) % len(self.shards)
        return list(self.shards.keys())[hash_value]
    
    async def distributed_query(self, query: str, params: Dict) -> List[Dict]:
        """분산 쿼리 실행"""
        tasks = []
        for shard_name, connection in self.shards.items():
            task = asyncio.create_task(
                connection.run_query(query, params)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return self.merge_results(results)
```

#### 2. 캐싱 전략
```python
class CacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_ttl = {
            'section_summary': 3600,    # 1시간
            'page_structure': 1800,     # 30분
            'search_results': 300,      # 5분
            'navigation_path': 900      # 15분
        }
    
    async def get_cached_section(self, section_id: str) -> Optional[Dict]:
        """캐시된 섹션 정보 조회"""
        cache_key = f"section:{section_id}"
        cached_data = await self.redis.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        return None
    
    async def cache_section(self, section_id: str, data: Dict):
        """섹션 정보 캐싱"""
        cache_key = f"section:{section_id}"
        await self.redis.setex(
            cache_key,
            self.cache_ttl['section_summary'],
            json.dumps(data)
        )
```

### 📈 성능 모니터링

#### 1. 쿼리 성능 추적
```python
class QueryPerformanceMonitor:
    def __init__(self):
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # 1초
    
    async def execute_with_monitoring(self, query: str, params: Dict):
        """성능 모니터링과 함께 쿼리 실행"""
        start_time = time.time()
        
        try:
            result = await neo4j_service.run_query(query, params)
            execution_time = time.time() - start_time
            
            # 통계 업데이트
            self.update_stats(query, execution_time)
            
            # 느린 쿼리 로깅
            if execution_time > self.slow_query_threshold:
                logger.warning(f"Slow query detected: {execution_time:.2f}s")
                logger.warning(f"Query: {query}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query failed after {execution_time:.2f}s: {str(e)}")
            raise
    
    def update_stats(self, query: str, execution_time: float):
        """쿼리 통계 업데이트"""
        query_hash = hash(query)
        
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = {
                'count': 0,
                'total_time': 0.0,
                'avg_time': 0.0,
                'max_time': 0.0,
                'min_time': float('inf')
            }
        
        stats = self.query_stats[query_hash]
        stats['count'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['count']
        stats['max_time'] = max(stats['max_time'], execution_time)
        stats['min_time'] = min(stats['min_time'], execution_time)
```

### 🔄 데이터 정합성

#### 1. 트랜잭션 관리
```python
class TransactionManager:
    def __init__(self, neo4j_service):
        self.neo4j = neo4j_service
    
    async def atomic_section_creation(self, section_data: Dict, 
                                    related_pages: List[Dict]):
        """섹션 생성의 원자적 처리"""
        async with self.neo4j.transaction() as tx:
            try:
                # 1. 섹션 생성
                section_query = """
                CREATE (s:SECTION {
                  id: $id,
                  title: $title,
                  type: $type,
                  created_at: datetime()
                })
                RETURN s
                """
                section_result = await tx.run(section_query, section_data)
                
                # 2. 관련 페이지들과 연결
                for page_data in related_pages:
                    relation_query = """
                    MATCH (s:SECTION {id: $section_id})
                    MATCH (d:DEPTH {id: $page_id})
                    CREATE (d)-[:GROUPED_BY]->(s)
                    """
                    await tx.run(relation_query, {
                        'section_id': section_data['id'],
                        'page_id': page_data['id']
                    })
                
                # 3. 통계 업데이트
                stats_query = """
                MATCH (s:SECTION {id: $section_id})
                       <-[:GROUPED_BY]-(d:DEPTH)
                SET s.content_count = count(d)
                """
                await tx.run(stats_query, {'section_id': section_data['id']})
                
                await tx.commit()
                
            except Exception as e:
                await tx.rollback()
                raise e
```

---

## 🎯 마무리

이 문서는 Vowser MCP 서버의 Neo4j 데이터베이스 아키텍처에 대한 종합적인 설계 문서입니다. 

### 📋 주요 특징 요약

1. **계층적 노드 구조**: ROOT → SUBROOT → DEPTH → SECTION → ELEMENT → CONTENT
2. **자동 섹션 생성**: 유사한 페이지들을 자동으로 그룹핑
3. **페이징 최적화**: 대용량 콘텐츠의 효율적 처리
4. **접근성 중심**: 사용자 친화적인 탐색 정보 제공
5. **확장성**: 대규모 웹사이트 처리 가능한 아키텍처

### 🚀 구현 순서 권장사항

1. **기본 노드 구조 구현** (ROOT, DEPTH, SECTION)
2. **단순 관계 설정** (HAS_DEPTH, HAS_SECTION)
3. **Section 자동 생성 로직** 구현
4. **페이징 처리** 시스템 구현
5. **성능 최적화** 적용
6. **확장성 고려사항** 반영

이 아키텍처를 기반으로 주피터 노트북에서 프로토타입을 구현한 후, FastAPI로 서비스화하는 것을 권장합니다.