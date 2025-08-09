# Data Directory

테스트 데이터 생성 및 관리를 위한 디렉토리입니다.

## 📁 파일 구조

```
data/
├── __init__.py                # Python 패키지 초기화
├── korean_test_data.py        # 한국 사이트 테스트 데이터 정의
├── korean_test_data.json      # JSON 형식 테스트 데이터 (미사용)
├── load_korean_data.py        # Neo4j로 데이터 로드 스크립트
└── korean_data_load_report.md # 데이터 로드 결과 보고서
```

## 🚀 사용법

### 1. 서버 시작
```bash
cd /Users/ken/IdeaProjects/vowser-mcp-server
python3 -m uvicorn app.main:app --port 8000
```

### 2. 데이터 로드
```bash
cd data
python3 load_korean_data.py
```

## 📊 테스트 데이터 내용

### 포함된 사이트 (15개 도메인)
- **엔터테인먼트**: 네이버웹툰, 유튜브, 멜론, 왓챠
- **쇼핑**: 쿠팡, SSG닷컴, 무신사, 당근마켓  
- **정보**: 네이버, 네이버지도, 나무위키
- **음식배달**: 배달의민족

### 데이터 구조
각 테스트 케이스는 다음 정보를 포함:
- `sessionId`: 고유 세션 ID
- `startCommand`: 사용자 의도를 나타내는 자연어 명령
- `completePath`: 클릭 경로 (3-6단계)
  - `locationData`: CSS selector, anchor point 등 위치 정보
  - `semanticData`: 텍스트 레이블, 컨텍스트 등 의미 정보

## 🔧 새 테스트 데이터 추가

`korean_test_data.py`에서 새로운 케이스를 추가할 수 있습니다:

```python
NEW_SITE_CASES = [
    {
        "sessionId": "new_site_001",
        "startCommand": "새 사이트에서 작업 수행",
        "completePath": [
            # 경로 단계들...
        ]
    }
]

# ALL_KOREAN_TEST_CASES에 추가
ALL_KOREAN_TEST_CASES = (
    EXISTING_CASES +
    NEW_SITE_CASES
)
```

## 📈 Neo4j 통계 확인

데이터 로드 후 자동으로 통계가 출력됩니다:
- 총 노드/관계 수
- ROOT/PAGE/PATH 노드 개수
- 도메인별 경로 수
- 성공/실패 통계