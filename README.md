# Advanced Web Crawler

범용적인 웹 크롤러로, 다양한 웹사이트를 크롤링하고 구조화할 수 있습니다.

## 주요 기능

- **범용 웹 크롤링**: 모든 웹사이트에 적용 가능한 설정 기반 크롤러
- **동적 콘텐츠 처리**: JavaScript 렌더링, 스크롤, 더보기 버튼 처리
- **설정 파일 지원**: JSON 기반 설정으로 사이트별 커스터마이징
- **LLM 기반 카테고리화**: Gemini를 사용한 자동 URL 분류
- **깊이 제한 크롤링**: 효율적인 리소스 관리

## 설치

```bash
# 의존성 설치
pip install -r requirements.txt

# 또는 poetry 사용
poetry install
```

## 사용법

### 기본 사용법

```bash
# 기본 설정으로 크롤링
python prototype_advanced.py https://example.com

# 깊이와 페이지 수 지정
python prototype_advanced.py https://example.com -d 3 -p 100
```

### 설정 파일 사용

```bash
# 네이버 크롤링
python prototype_advanced.py https://www.naver.com -c configs/naver.json

# 구글 크롤링
python prototype_advanced.py https://www.google.com -c configs/google.json

# 커스텀 설정
python prototype_advanced.py https://mysite.com -c myconfig.json
```

### 명령줄 옵션

- `url`: 크롤링할 대상 URL (필수)
- `-c, --config`: 설정 파일 경로 (JSON)
- `-d, --depth`: 최대 크롤링 깊이 (기본값: 2)
- `-p, --pages`: 최대 크롤링 페이지 수 (기본값: 50)

## 설정 파일 구조

```json
{
  "allowed_domains": ["example.com"],
  "start_urls": ["https://example.com"],
  "max_depth": 2,
  "max_pages": 50,
  "dynamic_content": {
    "scroll_count": 3,
    "scroll_delay": 1500,
    "expandable_selectors": [
      "button[class*=\"more\"]",
      ".load-more"
    ]
  },
  "url_extraction": {
    "include_external": false,
    "patterns": [],
    "exclude_patterns": ["login", "logout"]
  },
  "categorization": {
    "rules": [
      {"pattern": "blog", "category": "Blog"},
      {"pattern": "news", "category": "News"}
    ],
    "llm_prompt_template": null
  }
}
```

### 설정 옵션 설명

- **allowed_domains**: 크롤링할 도메인 목록
- **start_urls**: 시작 URL 목록
- **max_depth**: 최대 크롤링 깊이
- **max_pages**: 최대 크롤링 페이지 수
- **dynamic_content**: 동적 콘텐츠 처리 설정
  - **scroll_count**: 스크롤 횟수
  - **scroll_delay**: 스크롤 간격 (ms)
  - **expandable_selectors**: 클릭할 확장 버튼 셀렉터
- **url_extraction**: URL 추출 설정
  - **include_external**: 외부 링크 포함 여부
  - **patterns**: 포함할 URL 패턴
  - **exclude_patterns**: 제외할 URL 패턴
- **categorization**: 카테고리화 설정
  - **rules**: URL 패턴 기반 카테고리 규칙
  - **llm_prompt_template**: 커스텀 LLM 프롬프트

## 예제 설정 파일

`configs/` 디렉토리에서 다양한 예제를 확인할 수 있습니다:

- `naver.json`: 네이버 크롤링 설정
- `google.json`: 구글 크롤링 설정
- `example.json`: 일반적인 설정 템플릿

## 환경 변수

`.env` 파일에 다음 설정이 필요합니다:

```
GOOGLE_API_KEY=your_gemini_api_key
```

## 출력

크롤링 결과는 `{domain}_crawl_results.json` 파일로 저장됩니다.

## 주의사항

- robots.txt를 준수하세요
- 서버에 부담을 주지 않도록 적절한 딜레이를 설정하세요
- 개인정보나 민감한 데이터를 크롤링하지 마세요
