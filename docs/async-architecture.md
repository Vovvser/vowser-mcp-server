# 비동기 처리 아키텍처: asyncio vs Celery

## 개요

vowser-mcp-server는 웹 크롤링과 구조화 작업의 성능 최적화를 위해 **이중 비동기 전략**을 사용합니다:

- **asyncio**: I/O 집약적인 웹 크롤링 작업의 동시 처리
- **Celery**: 장시간 실행되는 백그라운드 태스크 관리

## 1. asyncio - 메인 비동기 처리

### 1.1 용도
- 웹 페이지 동시 로드 (Playwright)
- HTML 파싱 작업 (BeautifulSoup)  
- Neo4j 데이터베이스 쿼리
- LangChain API 호출
- FastAPI 엔드포인트 처리

### 1.2 주요 사용 시나리오

#### 다중 페이지 크롤링
```python
import asyncio
from playwright.async_api import async_playwright

async def crawl_single_page(url: str) -> dict:
    """단일 페이지 크롤링"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        
        # 페이지 구조 분석
        content = await page.content()
        title = await page.title()
        
        await browser.close()
        return {"url": url, "title": title, "content": content}

async def crawl_multiple_pages(urls: list[str]) -> list[dict]:
    """여러 페이지 동시 크롤링"""
    tasks = [crawl_single_page(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results

# 사용 예시
urls = [
    "https://example.com/page1",
    "https://example.com/page2", 
    "https://example.com/page3"
]
results = await crawl_multiple_pages(urls)
```

#### Neo4j 데이터베이스 비동기 처리
```python
from langchain_neo4j import Neo4jGraph
import asyncio

class AsyncNeo4jService:
    def __init__(self):
        self.graph = Neo4jGraph(
            url=os.getenv("NEO4J_URL"),
            username=os.getenv("NEO4J_USERNAME"),
            password=os.getenv("NEO4J_PASSWORD")
        )
    
    async def save_multiple_sections(self, sections: list[dict]) -> list[dict]:
        """여러 섹션 동시 저장"""
        tasks = [self.save_section(section) for section in sections]
        results = await asyncio.gather(*tasks)
        return results
    
    async def save_section(self, section: dict) -> dict:
        """단일 섹션 저장"""
        query = """
        CREATE (s:SECTION {
            id: $id,
            type: $type,
            text: $text,
            summary: $summary,
            created_at: datetime()
        })
        RETURN s
        """
        # 비동기 실행으로 변환
        result = await asyncio.to_thread(
            self.graph.query, 
            query, 
            params=section
        )
        return result
```

#### LangChain 요약 생성
```python
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
import asyncio

class AsyncLangChainService:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.7)
    
    async def generate_summaries(self, texts: list[str]) -> list[str]:
        """여러 텍스트 동시 요약"""
        tasks = [self.generate_summary(text) for text in texts]
        summaries = await asyncio.gather(*tasks)
        return summaries
    
    async def generate_summary(self, text: str) -> str:
        """단일 텍스트 요약"""
        message = HumanMessage(content=f"다음 텍스트를 요약해주세요: {text}")
        response = await self.llm.agenerate([[message]])
        return response.generations[0][0].text
```

### 1.3 FastAPI 통합
```python
from fastapi import FastAPI, BackgroundTasks
import asyncio

app = FastAPI()

@app.post("/api/v1/crawl")
async def start_crawl(url: str, depth: int = 3):
    """크롤링 작업 시작"""
    try:
        # 비동기 크롤링 실행
        result = await crawl_website_async(url, depth)
        return {
            "status": "completed",
            "url": url,
            "pages_crawled": len(result),
            "data": result
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def crawl_website_async(url: str, depth: int) -> list[dict]:
    """웹사이트 비동기 크롤링"""
    pages_to_crawl = await discover_pages(url, depth)
    results = await crawl_multiple_pages(pages_to_crawl)
    
    # 병렬 처리: 파싱 + 요약 + 저장
    parsing_tasks = [parse_page(result) for result in results]
    summary_tasks = [generate_summary(result['content']) for result in results]
    
    parsed_results = await asyncio.gather(*parsing_tasks)
    summaries = await asyncio.gather(*summary_tasks)
    
    # 결과 결합
    final_results = []
    for i, result in enumerate(results):
        final_results.append({
            **result,
            "parsed": parsed_results[i],
            "summary": summaries[i]
        })
    
    return final_results
```

## 2. Celery - 백그라운드 태스크 큐

### 2.1 용도
- 대용량 웹사이트 크롤링 (수백 페이지)
- 페이징 처리 (100+ 페이지 게시판)
- 장시간 실행 크롤링 작업
- 작업 큐 관리 및 재시도

### 2.2 Celery 설정
```python
# celery_app.py
from celery import Celery
import os

# Celery 인스턴스 생성
celery_app = Celery(
    "vowser-mcp-server",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=["tasks.crawling"]
)

# 설정
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "tasks.crawling.crawl_large_website": {"queue": "crawling"},
        "tasks.crawling.process_pagination": {"queue": "pagination"}
    }
)
```

### 2.3 Celery 태스크 정의
```python
# tasks/crawling.py
from celery import current_task
from celery_app import celery_app
import asyncio
from typing import Dict, List

@celery_app.task(bind=True, max_retries=3)
def crawl_large_website(self, url: str, options: Dict) -> Dict:
    """대용량 웹사이트 크롤링 태스크"""
    try:
        # 진행 상황 업데이트
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Starting crawl"}
        )
        
        # 비동기 크롤링 실행
        result = asyncio.run(crawl_website_with_progress(url, options))
        
        return {
            "status": "completed",
            "url": url,
            "pages_crawled": result["pages_crawled"],
            "total_nodes": result["total_nodes"],
            "execution_time": result["execution_time"]
        }
    
    except Exception as e:
        # 재시도 로직
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            "status": "failed",
            "error": str(e),
            "retries": self.request.retries
        }

@celery_app.task
def process_pagination(section_data: Dict) -> Dict:
    """페이징 처리 태스크"""
    total_pages = section_data["total_pages"]
    url_pattern = section_data["url_pattern"]
    
    # 크롤링 전략 결정
    if total_pages <= 5:
        strategy = "all"
        pages_to_crawl = list(range(1, total_pages + 1))
    elif total_pages <= 20:
        strategy = "representative"
        pages_to_crawl = [1, 2, 3, total_pages]
    else:
        strategy = "sampling"
        pages_to_crawl = [1, 2, 3, 10, 20, total_pages]
    
    # 비동기 페이지 크롤링
    result = asyncio.run(crawl_paginated_pages(url_pattern, pages_to_crawl))
    
    return {
        "strategy": strategy,
        "pages_crawled": pages_to_crawl,
        "total_pages": total_pages,
        "results": result
    }

async def crawl_website_with_progress(url: str, options: Dict) -> Dict:
    """진행 상황 업데이트를 포함한 크롤링"""
    start_time = time.time()
    
    # 1. 페이지 발견
    current_task.update_state(
        state="PROGRESS",
        meta={"current": 10, "total": 100, "status": "Discovering pages"}
    )
    pages = await discover_pages(url, options.get("depth", 3))
    
    # 2. 페이지 크롤링
    current_task.update_state(
        state="PROGRESS", 
        meta={"current": 30, "total": 100, "status": "Crawling pages"}
    )
    crawl_results = await crawl_multiple_pages(pages)
    
    # 3. 구조 분석
    current_task.update_state(
        state="PROGRESS",
        meta={"current": 60, "total": 100, "status": "Analyzing structure"}
    )
    structured_data = await analyze_structure(crawl_results)
    
    # 4. 데이터베이스 저장
    current_task.update_state(
        state="PROGRESS",
        meta={"current": 90, "total": 100, "status": "Saving to database"}
    )
    save_result = await save_to_neo4j(structured_data)
    
    execution_time = time.time() - start_time
    
    return {
        "pages_crawled": len(crawl_results),
        "total_nodes": save_result["node_count"],
        "execution_time": execution_time
    }
```

### 2.4 FastAPI와 Celery 통합
```python
# main.py
from fastapi import FastAPI, BackgroundTasks
from celery.result import AsyncResult
from tasks.crawling import crawl_large_website, process_pagination
import uuid

app = FastAPI()

@app.post("/api/v1/crawl")
async def start_crawl(url: str, depth: int = 3, background: bool = False):
    """크롤링 작업 시작"""
    
    if background:
        # 백그라운드 태스크로 실행
        task = crawl_large_website.delay(url, {"depth": depth})
        return {
            "task_id": task.id,
            "status": "queued",
            "message": "크롤링 작업이 백그라운드에서 시작되었습니다."
        }
    else:
        # 즉시 실행 (소규모 크롤링)
        result = await crawl_website_async(url, depth)
        return {
            "status": "completed",
            "data": result
        }

@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(task_id: str):
    """태스크 상태 조회"""
    result = AsyncResult(task_id)
    
    if result.state == "PENDING":
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "작업이 대기 중입니다."
        }
    elif result.state == "PROGRESS":
        return {
            "task_id": task_id,
            "status": "in_progress",
            "progress": result.info.get("current", 0),
            "total": result.info.get("total", 100),
            "message": result.info.get("status", "")
        }
    elif result.state == "SUCCESS":
        return {
            "task_id": task_id,
            "status": "completed",
            "result": result.result
        }
    else:
        return {
            "task_id": task_id,
            "status": "failed", 
            "error": str(result.info)
        }

@app.post("/api/v1/pagination")
async def process_paginated_content(section_data: dict):
    """페이징 처리 태스크 시작"""
    task = process_pagination.delay(section_data)
    return {
        "task_id": task.id,
        "status": "queued",
        "message": "페이징 처리 작업이 시작되었습니다."
    }
```

## 3. 이중 비동기 전략의 장점

### 3.1 성능 최적화
- **asyncio**: CPU 대기 시간 최소화 (I/O 바운드 작업)
- **Celery**: 메모리 사용량 제어 (장시간 작업)

### 3.2 확장성
- **수평적 확장**: Celery 워커 증설
- **수직적 확장**: asyncio 동시 처리 수 증가

### 3.3 신뢰성
- **오류 처리**: Celery 재시도 메커니즘
- **모니터링**: 각 작업의 진행 상황 추적

## 4. 사용 시나리오별 선택 가이드

### 4.1 asyncio 사용 시나리오
- **빠른 응답 필요**: 실시간 API 요청
- **소규모 크롤링**: 10페이지 미만
- **I/O 집약적**: 네트워크 요청, 파일 읽기

### 4.2 Celery 사용 시나리오
- **대용량 크롤링**: 100페이지 이상
- **장시간 실행**: 1시간 이상 예상
- **백그라운드 처리**: 사용자 대기 불필요

### 4.3 조합 사용 시나리오
```python
# 대용량 크롤링에서 asyncio + Celery 조합
@celery_app.task
def crawl_large_site(url: str) -> dict:
    """Celery 태스크에서 asyncio 사용"""
    
    # 비동기 크롤링 실행
    result = asyncio.run(crawl_with_async_optimization(url))
    return result

async def crawl_with_async_optimization(url: str) -> dict:
    """비동기 최적화된 크롤링"""
    
    # 1. 페이지 발견 (비동기)
    pages = await discover_pages(url)
    
    # 2. 배치 처리 (메모리 효율성)
    batch_size = 10
    all_results = []
    
    for i in range(0, len(pages), batch_size):
        batch = pages[i:i+batch_size]
        batch_results = await crawl_multiple_pages(batch)
        all_results.extend(batch_results)
        
        # 메모리 정리
        del batch_results
    
    return {"total_pages": len(all_results), "results": all_results}
```

## 5. 모니터링 및 디버깅

### 5.1 asyncio 모니터링
```python
import asyncio
import time
import logging

logger = logging.getLogger(__name__)

async def monitor_async_tasks():
    """비동기 작업 모니터링"""
    while True:
        tasks = [t for t in asyncio.all_tasks() if not t.done()]
        logger.info(f"Active async tasks: {len(tasks)}")
        
        for task in tasks:
            logger.debug(f"Task: {task.get_name()}, State: {task._state}")
        
        await asyncio.sleep(10)

# 사용 예시
async def main():
    monitor_task = asyncio.create_task(monitor_async_tasks())
    crawl_task = asyncio.create_task(crawl_website_async("https://example.com"))
    
    await asyncio.gather(monitor_task, crawl_task)
```

### 5.2 Celery 모니터링
```python
# celery_monitor.py
from celery import Celery
from celery.events.state import State

def monitor_celery_tasks():
    """Celery 작업 모니터링"""
    app = Celery("vowser-mcp-server")
    state = State()
    
    def announce_failed_tasks(event):
        state.event(event)
        task = state.tasks.get(event['uuid'])
        print(f"TASK FAILED: {task.name}[{task.uuid}] {task.info()}")
    
    def announce_succeeded_tasks(event):
        state.event(event)
        task = state.tasks.get(event['uuid'])
        print(f"TASK SUCCESS: {task.name}[{task.uuid}] {task.info()}")
    
    with app.connection() as connection:
        recv = app.events.Receiver(connection, handlers={
            'task-failed': announce_failed_tasks,
            'task-succeeded': announce_succeeded_tasks,
        })
        recv.capture(limit=None, timeout=None, wakeup=True)
```

## 6. 성능 최적화 팁

### 6.1 asyncio 최적화
```python
# 연결 풀 사용
import aiohttp
import asyncio

class OptimizedCrawler:
    def __init__(self):
        self.session = None
        self.connector = aiohttp.TCPConnector(
            limit=100,  # 총 연결 수 제한
            limit_per_host=10,  # 호스트당 연결 수 제한
            ttl_dns_cache=300,  # DNS 캐시 TTL
            use_dns_cache=True,
        )
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            connector=self.connector,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    async def crawl_url(self, url: str) -> dict:
        async with self.session.get(url) as response:
            content = await response.text()
            return {"url": url, "content": content}

# 사용 예시
async def optimized_crawling(urls: list[str]) -> list[dict]:
    async with OptimizedCrawler() as crawler:
        tasks = [crawler.crawl_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
```

### 6.2 Celery 최적화
```python
# celery_config.py
from celery import Celery

# 최적화된 Celery 설정
celery_app = Celery("vowser-mcp-server")

celery_app.conf.update(
    # 워커 최적화
    worker_prefetch_multiplier=1,  # 메모리 사용량 제어
    worker_max_tasks_per_child=100,  # 메모리 누수 방지
    
    # 태스크 최적화
    task_acks_late=True,  # 태스크 완료 후 ACK
    task_reject_on_worker_lost=True,  # 워커 손실 시 태스크 거부
    
    # 결과 백엔드 최적화
    result_expires=3600,  # 결과 만료 시간
    result_backend_transport_options={
        'master_name': 'mymaster',
        'retry_on_timeout': True,
    },
    
    # 브로커 최적화
    broker_transport_options={
        'visibility_timeout': 3600,
        'fanout_prefix': True,
        'fanout_patterns': True
    }
)
```

이 문서는 vowser-mcp-server의 비동기 처리 아키텍처에 대한 종합적인 가이드입니다. 프로젝트의 요구사항에 따라 asyncio와 Celery를 효과적으로 활용하여 고성능 웹 크롤링 시스템을 구축할 수 있습니다.