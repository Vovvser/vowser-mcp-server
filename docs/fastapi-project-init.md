# FastAPI 프로젝트 기본 설정 가이드 (Best Practices)

## 1. 프로젝트 구조 생성

```bash
# 도메인 중심 디렉토리 구조 (추천)
mkdir -p {src,tests,docs,logs}
mkdir -p src/{crawling,graph,shared}
mkdir -p src/crawling/{router,service,schemas,dependencies}
mkdir -p src/graph/{router,service,schemas,dependencies}  
mkdir -p src/shared/{config,database,exceptions,logging}
mkdir -p tests/{unit,integration}

# 기존 기술 레이어 구조 (확장성 제한)
# mkdir -p src/{api,core,models,services,utils}
# mkdir -p src/api/{endpoints,middleware}
```

## 2. 필수 패키지 설치

```bash
# 핵심 FastAPI 패키지
uv add fastapi
uv add "uvicorn[standard]"

# 데이터베이스 및 Neo4j
uv add neo4j
uv add langchain-neo4j

# 웹 크롤링
uv add playwright
uv add beautifulsoup4
uv add aiohttp

# 환경 변수 및 설정
uv add python-dotenv
uv add pydantic-settings

# 로깅 및 모니터링 (추가)
uv add structlog
uv add python-json-logger

# 개발 도구
uv add --dev pytest
uv add --dev pytest-asyncio
uv add --dev httpx  # 비동기 테스트 클라이언트
uv add --dev black
uv add --dev flake8
uv add --dev ruff    # 빠른 린터
```

## 3. 기본 설정 파일 생성

### 3.1 FastAPI 애플리케이션 설정 (`src/main.py`)

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from src.shared.config import settings
from src.shared.exceptions import AppException
from src.crawling.router import router as crawl_router
from src.graph.router import router as graph_router

# 로거 설정
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vowser MCP Server",
    description="Neo4j GraphRAG-based MCP server for website structuring",
    version="1.0.0",
    # 프로덕션에서 문서 숨기기
    openapi_url="/openapi.json" if settings.DEBUG else None
)

# CORS 설정 (보안 강화)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 전역 예외 핸들러 (보안 강화)
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.message}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception for {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal Server Error"}
    )

# 라우터 등록
app.include_router(crawl_router, prefix="/api/v1", tags=["crawling"])
app.include_router(graph_router, prefix="/api/v1", tags=["graph"])

@app.get("/")
async def root():
    return {"message": "Vowser MCP Server is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 3.2 설정 관리 (`src/shared/config.py`)

```python
from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import List
import logging
import sys

class Settings(BaseSettings):
    # 애플리케이션 설정
    APP_NAME: str = "Vowser MCP Server"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Neo4j 설정
    NEO4J_URL: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str
    
    # 크롤링 설정
    MAX_DEPTH: int = 3
    MAX_PAGES: int = 100
    CRAWL_DELAY: float = 1.0
    
    # CORS 설정 (보안 강화)
    CORS_ORIGINS: List[str] = []
    CORS_ORIGINS_REGEX: str | None = None
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    
    @model_validator(mode='after')
    def validate_settings(self):
        # 프로덕션 환경에서 와일드카드 CORS 금지
        if self.ENVIRONMENT == "production":
            if "*" in self.CORS_ORIGINS:
                raise ValueError("Wildcard CORS not allowed in production")
        
        # 개발 환경에서 기본 CORS 설정
        if not self.CORS_ORIGINS and self.ENVIRONMENT == "development":
            self.CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
            
        return self
    
    class Config:
        env_file = ".env"

def setup_logging(log_level: str = "INFO"):
    """로깅 설정"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

settings = Settings()
setup_logging(settings.LOG_LEVEL)
```

### 3.3 Neo4j 연결 설정 (`src/shared/database.py`)

```python
from langchain_neo4j import Neo4jGraph
from functools import lru_cache
from src.shared.config import settings
import logging

logger = logging.getLogger(__name__)

# 의존성 주입 패턴 (권장)
@lru_cache()
def get_neo4j_graph() -> Neo4jGraph:
    """Neo4j 그래프 인스턴스 반환 (싱글톤 패턴)"""
    try:
        graph = Neo4jGraph(
            url=settings.NEO4J_URL,
            username=settings.NEO4J_USERNAME,
            password=settings.NEO4J_PASSWORD
        )
        logger.info("Neo4j 연결 성공")
        return graph
    except Exception as e:
        logger.error(f"Neo4j 연결 실패: {str(e)}")
        raise ConnectionError(f"Neo4j 연결 실패: {str(e)}")

# 세션 기반 의존성 (필요시 사용)
def get_neo4j_session():
    """Neo4j 세션 반환 (트랜잭션 관리용)"""
    graph = get_neo4j_graph()
    try:
        yield graph
    finally:
        # 필요시 세션 정리 로직 추가
        pass

# 기존 클래스 방식 (레거시, 권장하지 않음)
class Neo4jConnection:
    def __init__(self):
        self.graph = None
    
    def connect(self):
        """Neo4j 데이터베이스 연결"""
        try:
            self.graph = Neo4jGraph(
                url=settings.NEO4J_URL,
                username=settings.NEO4J_USERNAME,
                password=settings.NEO4J_PASSWORD
            )
            return self.graph
        except Exception as e:
            raise ConnectionError(f"Neo4j 연결 실패: {str(e)}")
    
    def disconnect(self):
        """연결 해제"""
        if self.graph:
            self.graph.close()
```

## 4. API 엔드포인트 구조

### 3.4 공통 예외 처리 (`src/shared/exceptions.py`)

```python
class AppException(Exception):
    """애플리케이션 기본 예외 클래스"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class CrawlingException(AppException):
    """크롤링 관련 예외"""
    pass

class GraphException(AppException):
    """그래프 관련 예외"""
    pass

class ValidationException(AppException):
    """입력 검증 예외"""
    def __init__(self, message: str):
        super().__init__(message, 400)
```

### 3.5 공통 응답 모델 (`src/shared/schemas.py`)

```python
from pydantic import BaseModel
from typing import TypeVar, Generic, Optional, Any

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """표준 API 응답 형식"""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    errors: Optional[list[str]] = None
```

## 4. API 엔드포인트 구조

### 4.1 크롤링 엔드포인트 (`src/crawling/router.py`)

```python
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, HttpUrl, Field, field_validator
from langchain_neo4j import Neo4jGraph
from src.shared.database import get_neo4j_graph
from src.shared.schemas import ApiResponse
from src.shared.exceptions import CrawlingException
from src.crawling.service import CrawlingService
import uuid

router = APIRouter()

class CrawlRequest(BaseModel):
    url: HttpUrl  # 보안 강화: URL 타입 검증
    max_depth: int = Field(default=3, ge=1, le=10)
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        # SSRF 방지
        if v.scheme not in ['http', 'https']:
            raise ValueError('Only HTTP/HTTPS URLs are allowed')
        return v

class CrawlResponse(BaseModel):
    job_id: str
    status: str
    message: str

@router.post("/crawl", response_model=ApiResponse[CrawlResponse])
async def start_crawling(
    request: CrawlRequest, 
    background_tasks: BackgroundTasks,
    graph: Neo4jGraph = Depends(get_neo4j_graph)
):
    """웹사이트 크롤링 시작"""
    job_id = str(uuid.uuid4())
    crawling_service = CrawlingService(graph)
    
    # BackgroundTasks 사용으로 비동기 처리
    background_tasks.add_task(
        crawling_service.process_crawling,
        job_id=job_id,
        url=str(request.url),
        max_depth=request.max_depth
    )
    
    response_data = CrawlResponse(
        job_id=job_id,
        status="queued",
        message="크롤링이 대기열에 추가되었습니다"
    )
    
    return ApiResponse(data=response_data)
```

### 4.2 그래프 조회 엔드포인트 (`src/graph/router.py`)

```python
from fastapi import APIRouter, Depends, HTTPException
from langchain_neo4j import Neo4jGraph
from src.shared.database import get_neo4j_graph
from src.shared.schemas import ApiResponse
from src.shared.exceptions import GraphException
from src.graph.service import GraphService

router = APIRouter()

@router.get("/graph/{job_id}", response_model=ApiResponse[dict])
async def get_graph_structure(
    job_id: str,
    graph: Neo4jGraph = Depends(get_neo4j_graph)
):
    """크롤링 결과 그래프 구조 조회"""
    graph_service = GraphService(graph)
    result = await graph_service.get_graph_by_job_id(job_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="그래프를 찾을 수 없습니다")
    
    return ApiResponse(data=result)
```

## 5. 서비스 레이어 구조

### 5.1 크롤링 서비스 (`src/crawling/service.py`)

```python
import logging
from playwright.async_api import async_playwright
from langchain_neo4j import Neo4jGraph
from src.shared.exceptions import CrawlingException

logger = logging.getLogger(__name__)

class CrawlingService:
    def __init__(self, graph: Neo4jGraph):
        self.graph = graph
    
    async def process_crawling(self, job_id: str, url: str, max_depth: int = 3):
        """백그라운드에서 실행되는 크롤링 작업"""
        try:
            logger.info(f"크롤링 시작: job_id={job_id}, url={url}")
            await self._crawl_website(url, max_depth, job_id)
            logger.info(f"크롤링 완료: job_id={job_id}")
        except Exception as e:
            logger.error(f"크롤링 실패: job_id={job_id}, error={str(e)}")
            raise CrawlingException(f"크롤링 실패: {str(e)}")
    
    async def _crawl_website(self, url: str, max_depth: int, job_id: str):
        """실제 크롤링 로직"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # 크롤링 로직 구현
                await self._crawl_page(page, url, 0, max_depth, job_id)
            finally:
                await browser.close()
    
    async def _crawl_page(self, page, url: str, depth: int, max_depth: int, job_id: str):
        """개별 페이지 크롤링"""
        if depth > max_depth:
            return
        
        try:
            # 페이지 로드
            await page.goto(url, wait_until="networkidle")
            
            # 기본 페이지 정보 추출
            title = await page.title()
            
            # Neo4j에 데이터 저장
            await self._save_page_data(job_id, url, title, depth)
            
            # 추가 크롤링 로직 구현 예정
            
        except Exception as e:
            logger.error(f"페이지 크롤링 실패: url={url}, error={str(e)}")
    
    async def _save_page_data(self, job_id: str, url: str, title: str, depth: int):
        """페이지 데이터를 Neo4j에 저장"""
        query = """
        MERGE (p:Page {url: $url})
        SET p.title = $title,
            p.depth = $depth,
            p.job_id = $job_id,
            p.created_at = datetime()
        """
        await self.graph.query(query, {
            "url": url,
            "title": title,
            "depth": depth,
            "job_id": job_id
        })
```

## 6. 실행 스크립트

### 6.1 개발 서버 실행 (`run_dev.py`)

```python
import uvicorn
from src.main import app

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"]
    )
```

### 6.2 프로덕션 실행 스크립트 (`run_prod.py`)

```python
import uvicorn
from src.main import app

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        workers=4
    )
```

## 7. 환경 변수 설정

### 7.1 개발 환경 (`.env.development`)

```env
# 환경 설정
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# 애플리케이션 설정
APP_NAME=Vowser MCP Server

# Neo4j 설정
NEO4J_URL=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# CORS 설정 (개발용)
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# 크롤링 설정
MAX_DEPTH=3
MAX_PAGES=100
CRAWL_DELAY=1.0
```

### 7.2 프로덕션 환경 (`.env.production`)

```env
# 환경 설정
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# 애플리케이션 설정
APP_NAME=Vowser MCP Server

# Neo4j 설정
NEO4J_URL=bolt://your-neo4j-server:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password

# CORS 설정 (프로덕션용)
CORS_ORIGINS=["https://your-frontend-domain.com"]

# 크롤링 설정
MAX_DEPTH=5
MAX_PAGES=1000
CRAWL_DELAY=2.0
```

## 8. 실행 명령어

```bash
# 개발 서버 실행
python run_dev.py

# 또는 직접 uvicorn 실행
uvicorn src.main:app --reload --port 8000

# 프로덕션 실행
python run_prod.py
```

## 9. 테스트 설정

### 9.1 테스트 의존성 설치

```bash
# 테스트 클라이언트 설치 (이미 설치됨)
# uv add --dev httpx pytest-asyncio

# 테스트 설정 파일 생성
touch tests/conftest.py
touch tests/unit/test_crawling_service.py
```

### 9.2 테스트 클라이언트 설정 (`tests/conftest.py`)

```python
import pytest
import asyncio
from httpx import AsyncClient
from src.main import app

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def client():
    """비동기 테스트 클라이언트"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def mock_neo4j_graph():
    """Mock Neo4j 그래프 (테스트용)"""
    class MockGraph:
        async def query(self, query, params=None):
            return []
    
    return MockGraph()
```

### 9.3 테스트 실행

```bash
# 전체 테스트
pytest

# 특정 테스트
pytest tests/unit/test_crawling_service.py -v

# 커버리지 포함
pytest --cov=src tests/

# 비동기 테스트
pytest tests/unit/test_crawling_service.py::test_crawl_endpoint -v
```

## 10. 보안 및 성능 최적화

### 10.1 보안 체크리스트

- ✅ **CORS 설정**: 환경별 명시적 도메인 설정
- ✅ **입력 검증**: HttpUrl 타입 + SSRF 방지
- ✅ **에러 처리**: 내부 정보 노출 방지
- ✅ **환경 변수**: 민감 정보 분리
- ✅ **로깅**: 구조화된 로그 시스템

### 10.2 성능 최적화

- ✅ **비동기 처리**: BackgroundTasks 활용
- ✅ **의존성 주입**: 효율적인 리소스 관리
- ✅ **캐싱**: @lru_cache 활용
- ✅ **연결 풀**: Neo4j 연결 최적화

## 11. 배포 준비

### 11.1 Docker 설정 (선택사항)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# UV 설치
RUN pip install uv

# 의존성 설치
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev

# 애플리케이션 복사
COPY src/ ./src/
COPY run_prod.py ./

# 포트 노출
EXPOSE 8000

# 실행
CMD ["python", "run_prod.py"]
```

### 11.2 환경별 배포 스크립트

```bash
# 개발 환경
export ENV_FILE=.env.development
python run_dev.py

# 프로덕션 환경
export ENV_FILE=.env.production
python run_prod.py
```

## 12. 다음 단계

1. **실제 구현**: 제시된 구조대로 파일 생성
2. **테스트 작성**: 각 컴포넌트별 단위 테스트
3. **문서화**: API 문서 자동 생성
4. **모니터링**: 로그 수집 및 알림 시스템
5. **CI/CD**: 자동 배포 파이프라인 구축