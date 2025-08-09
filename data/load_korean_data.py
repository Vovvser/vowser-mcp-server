#!/usr/bin/env python3
"""
한국 사이트 테스트 데이터를 WebSocket 서버로 전송하는 스크립트
"""

import asyncio
import json
import websockets
from korean_test_data import ALL_KOREAN_TEST_CASES
from typing import Dict, Any, List
import time

# WebSocket 서버 URL
WS_URL = "ws://localhost:8000/ws"

# 색상 코드
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

async def send_test_data(test_case: Dict[str, Any]) -> Dict[str, Any]:
    """단일 테스트 케이스를 WebSocket 서버로 전송"""
    try:
        async with websockets.connect(WS_URL) as websocket:
            # save_path 메시지 생성
            message = {
                "type": "save_path",
                "data": test_case
            }
            
            # 메시지 전송
            await websocket.send(json.dumps(message))
            
            # 응답 대기
            response = await websocket.recv()
            return json.loads(response)
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def batch_send_test_data(test_cases: List[Dict[str, Any]], batch_size: int = 5):
    """테스트 데이터를 배치로 전송"""
    total = len(test_cases)
    success_count = 0
    error_count = 0
    results = []
    
    print(f"\n{BLUE}=== 한국 사이트 테스트 데이터 로딩 시작 ==={RESET}")
    print(f"총 {total}개의 테스트 케이스를 전송합니다.\n")
    
    for i in range(0, total, batch_size):
        batch = test_cases[i:i+batch_size]
        batch_end = min(i + batch_size, total)
        
        print(f"{YELLOW}배치 {i//batch_size + 1}: {i+1}-{batch_end}/{total} 처리 중...{RESET}")
        
        # 배치 내 각 테스트 케이스를 병렬로 전송
        tasks = [send_test_data(test_case) for test_case in batch]
        batch_results = await asyncio.gather(*tasks)
        
        # 결과 처리
        for j, (test_case, result) in enumerate(zip(batch, batch_results)):
            case_num = i + j + 1
            session_id = test_case.get("sessionId", "unknown")
            command = test_case.get("startCommand", "unknown")[:50]
            
            if result.get("status") == "success":
                success_count += 1
                print(f"  {GREEN}✓{RESET} [{case_num:3d}] {session_id}: {command}")
                
                # PATH 노드 정보 출력
                if "path_id" in result:
                    print(f"       PATH ID: {result['path_id']}")
                if "nodes_created" in result:
                    print(f"       노드 생성: {result['nodes_created']}개")
                if "relationships_created" in result:
                    print(f"       관계 생성: {result['relationships_created']}개")
            else:
                error_count += 1
                error_msg = result.get("message", "Unknown error")
                print(f"  {RED}✗{RESET} [{case_num:3d}] {session_id}: {error_msg}")
            
            results.append(result)
        
        # 배치 간 짧은 대기
        if batch_end < total:
            await asyncio.sleep(0.5)
        
        print()
    
    return success_count, error_count, results

async def check_graph_stats():
    """그래프 통계 확인"""
    try:
        async with websockets.connect(WS_URL) as websocket:
            message = {
                "type": "check_graph",
                "data": {}
            }
            
            await websocket.send(json.dumps(message))
            response = await websocket.recv()
            return json.loads(response)
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def main():
    """메인 실행 함수"""
    start_time = time.time()
    
    # 시작 전 그래프 상태 확인
    print(f"{BLUE}=== 시작 전 Neo4j 그래프 상태 ==={RESET}")
    initial_stats = await check_graph_stats()
    if initial_stats.get("status") == "success":
        data = initial_stats.get("data", {})
        print(f"총 노드 수: {data.get('total_nodes', 0)}")
        print(f"총 관계 수: {data.get('total_relationships', 0)}")
        print(f"ROOT 노드: {data.get('root_nodes', 0)}")
        print(f"PAGE 노드: {data.get('page_nodes', 0)}")
        print(f"PATH 노드: {data.get('path_nodes', 0)}")
    
    # 테스트 데이터 전송
    success_count, error_count, results = await batch_send_test_data(
        ALL_KOREAN_TEST_CASES, 
        batch_size=3
    )
    
    # 완료 후 그래프 상태 확인
    print(f"\n{BLUE}=== 완료 후 Neo4j 그래프 상태 ==={RESET}")
    final_stats = await check_graph_stats()
    if final_stats.get("status") == "success":
        data = final_stats.get("data", {})
        print(f"총 노드 수: {data.get('total_nodes', 0)}")
        print(f"총 관계 수: {data.get('total_relationships', 0)}")
        print(f"ROOT 노드: {data.get('root_nodes', 0)}")
        print(f"PAGE 노드: {data.get('page_nodes', 0)}")
        print(f"PATH 노드: {data.get('path_nodes', 0)}")
        
        # 증가량 계산
        if initial_stats.get("status") == "success":
            initial_data = initial_stats.get("data", {})
            print(f"\n{YELLOW}=== 증가량 ==={RESET}")
            print(f"노드 증가: +{data.get('total_nodes', 0) - initial_data.get('total_nodes', 0)}")
            print(f"관계 증가: +{data.get('total_relationships', 0) - initial_data.get('total_relationships', 0)}")
            print(f"ROOT 증가: +{data.get('root_nodes', 0) - initial_data.get('root_nodes', 0)}")
            print(f"PAGE 증가: +{data.get('page_nodes', 0) - initial_data.get('page_nodes', 0)}")
            print(f"PATH 증가: +{data.get('path_nodes', 0) - initial_data.get('path_nodes', 0)}")
    
    # 실행 시간
    elapsed_time = time.time() - start_time
    
    # 결과 요약
    print(f"\n{BLUE}=== 실행 결과 요약 ==={RESET}")
    print(f"총 테스트 케이스: {len(ALL_KOREAN_TEST_CASES)}개")
    print(f"{GREEN}성공: {success_count}개{RESET}")
    print(f"{RED}실패: {error_count}개{RESET}")
    print(f"성공률: {(success_count/len(ALL_KOREAN_TEST_CASES)*100):.1f}%")
    print(f"실행 시간: {elapsed_time:.2f}초")
    
    # 도메인별 통계
    print(f"\n{BLUE}=== 도메인별 PATH 생성 ==={RESET}")
    domain_counts = {}
    for test_case in ALL_KOREAN_TEST_CASES:
        if test_case["completePath"]:
            domain = test_case["completePath"][0]["url"].split("//")[1].split("/")[0]
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {domain}: {count}개")

if __name__ == "__main__":
    asyncio.run(main())