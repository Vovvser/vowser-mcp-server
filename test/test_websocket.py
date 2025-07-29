import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    
    try:
        print("WebSocket 연결 시도...")
        async with websockets.connect(uri) as websocket:
            print("WebSocket 연결 성공!")
            
            # 테스트 1: 페이지 분석
            print("\n테스트 1: 페이지 분석")
            analyze_message = {
                "type": "analyze_page",
                "data": {
                    "url": "https://example.com",
                    "save_to_db": True
                }
            }
            
            await websocket.send(json.dumps(analyze_message))
            print("분석 요청 전송")
            
            response = await websocket.recv()
            result = json.loads(response)
            print(f"응답 받음: {result['type']}")
            print(f"   상태: {result['status']}")
            
            # 테스트 2: 분석 기록 조회
            print("\n테스트 2: 분석 기록 조회")
            history_message = {
                "type": "get_analysis_history",
                "data": {
                    "limit": 5
                }
            }
            
            await websocket.send(json.dumps(history_message))
            print("기록 조회 요청 전송")
            
            response = await websocket.recv()
            result = json.loads(response)
            print(f"응답 받음: {result['type']}")
            print(f"   상태: {result['status']}")
            
            # 테스트 3: 대시보드 조회
            print("\n테스트 3: 대시보드 조회")
            dashboard_message = {
                "type": "get_analytics_dashboard",
                "data": {}
            }
            
            await websocket.send(json.dumps(dashboard_message))
            print("대시보드 요청 전송")
            
            response = await websocket.recv()
            result = json.loads(response)
            print(f"응답 받음: {result['type']}")
            print(f"   상태: {result['status']}")
            
            # 테스트 4: 잘못된 메시지 타입
            print("\n테스트 4: 에러 처리")
            error_message = {
                "type": "unknown_type",
                "data": {}
            }
            
            await websocket.send(json.dumps(error_message))
            print("잘못된 요청 전송")
            
            response = await websocket.recv()
            result = json.loads(response)
            print(f"응답 받음: {result['type']}")
            print(f"   상태: {result['status']}")
            print(f"   메시지: {result['data']['message']}")
            
            print("\n모든 테스트 완료!")
            
    except Exception as e:
        print(f"연결 실패: {e}")
        print("서버가 실행 중인지 확인하세요: python -m uvicorn app.main:app --reload")

if __name__ == "__main__":
    asyncio.run(test_websocket())