import asyncio
import websockets
import json

from fixtures.test_data import MINIMAL_TEST_CASE, TEST_CASE_1

async def test_single_message(message_type, data):
    """단일 메시지 테스트"""
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"연결 성공 - 테스트: {message_type}")
            
            message = {
                "type": message_type,
                "data": data
            }
            
            await websocket.send(json.dumps(message))
            print(f"요청 전송: {message_type}")
            
            response = await websocket.recv()
            result = json.loads(response)
            
            print(f"응답: {result['type']} ({result['status']})")
            
            if result['status'] == 'success':
                print("성공!")
                return True
            else:
                print(f"실패: {result['data']['message']}")
                return False
            
    except Exception as e:
        print(f"연결 오류: {e}")
        return False

async def run_all_tests():
    """모든 테스트 개별 실행"""
    print("개별 WebSocket 테스트 시작\n")
    
    tests = [
        ("check_graph", {}),
        ("visualize_paths", {
            "domain": "example.com"
        }),
        ("find_popular_paths", {
            "domain": "example.com",
            "limit": 5
        }),
        ("save_path", MINIMAL_TEST_CASE),
        ("save_path", TEST_CASE_1)
    ]
    
    results = []
    for test_type, test_data in tests:
        print(f"\n{'='*50}")
        success = await test_single_message(test_type, test_data)
        results.append((test_type, success))
        await asyncio.sleep(1)  # 테스트 간 간격
    
    print(f"\n{'='*50}")
    print("테스트 결과 요약:")
    for test_type, success in results:
        status = "성공" if success else "실패"
        print(f"  {test_type}: {status}")
    
    success_count = sum(1 for _, success in results if success)
    print(f"\n전체 결과: {success_count}/{len(results)} 성공")
    
    if success_count == len(results):
        print("모든 테스트 통과!")
    else:
        print("일부 테스트 실패 - 문제 해결 필요")

if __name__ == "__main__":
    asyncio.run(run_all_tests())