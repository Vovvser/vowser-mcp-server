import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv, find_dotenv
from app.services import neo4j_service
from app.models.path import PathData

load_dotenv(find_dotenv())

app = FastAPI(title="Vowser MCP Server - WebSocket Only")

@app.get("/")
def read_root():
    """서버가 살아있는지 확인하는 루트 경로"""
    return {"Hello": "from Vowser MCP Server!"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    vowser-backend와의 WebSocket 통신 엔드포인트
    """
    await websocket.accept()
    print("WebSocket 연결됨 - vowser-backend와 통신 시작")
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            print(f"수신된 메시지: {message.get('type', 'unknown')}")
            
            try:
                if message['type'] == 'save_path':
                    path_data = PathData(**message['data'])
                    print(f"경로 저장 시작: {path_data.startCommand}")
                    
                    path_with_metadata = neo4j_service.add_metadata_to_path(path_data.model_dump())
                    result = neo4j_service.save_path_to_neo4j(path_with_metadata)
                    
                    response = {
                        "type": "path_save_result",
                        "status": "success",
                        "data": {
                            "message": "Path data processed successfully!",
                            "result": result
                        }
                    }
                
                elif message['type'] == 'check_graph':
                    graph_stats = neo4j_service.check_graph_structure()
                    
                    response = {
                        "type": "graph_check_result",
                        "status": "success",
                        "data": {
                            "graph_statistics": graph_stats
                        }
                    }
                
                elif message['type'] == 'visualize_paths':
                    domain = message['data']['domain']
                    
                    paths = neo4j_service.visualize_paths(domain)
                    
                    response = {
                        "type": "paths_visualization_result",
                        "status": "success",
                        "data": {
                            "domain": domain,
                            "paths": paths
                        }
                    }
                
                elif message['type'] == 'find_popular_paths':
                    domain = message['data'].get('domain')
                    limit = message['data'].get('limit', 10)
                    
                    popular = neo4j_service.find_popular_paths(domain, limit)
                    
                    response = {
                        "type": "popular_paths_result",
                        "status": "success",
                        "data": {
                            "domain": domain,
                            "popular_paths": popular
                        }
                    }
                
                else:
                    response = {
                        "type": "error",
                        "status": "error",
                        "data": {
                            "message": f"Unknown message type: {message.get('type', 'undefined')}"
                        }
                    }
                
            except Exception as e:
                print(f"메시지 처리 실패: {e}")
                response = {
                    "type": "error",
                    "status": "error",
                    "data": {
                        "message": str(e),
                        "original_type": message.get('type', 'unknown')
                    }
                }
            
            await websocket.send_text(json.dumps(response))
            print(f"응답 전송 완료: {response['type']}")
            
    except WebSocketDisconnect:
        print("WebSocket 연결 종료 - vowser-backend 연결 해제")
    except Exception as e:
        print(f"WebSocket 오류: {e}")
        await websocket.close()