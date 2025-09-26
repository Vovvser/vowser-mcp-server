import json
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv, find_dotenv
from app.services import neo4j_service
from app.models.path import PathData, SearchPathRequest
from app.models.contribution import ContributionPathData

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

                elif message['type'] == 'search_path':
                    # 자연어 경로 검색
                    try:
                        search_request = SearchPathRequest(**message['data'])
                        print(f"[MAIN DEBUG] 경로 검색 요청: {search_request.query}")

                        search_result = neo4j_service.search_paths_by_query(
                            search_request.query,
                            search_request.limit,
                            search_request.domain_hint
                        )
                        print(f"[MAIN DEBUG] 검색 결과: {search_result}")
                    except Exception as e:
                        print(f"[MAIN DEBUG] search_path 오류: {e}")
                        import traceback
                        traceback.print_exc()
                        search_result = None

                    if search_result:
                        # 검색된 경로들의 사용 추적
                        for path in search_result.get('matched_paths', []):
                            if path.get('pathId') and path['pathId'] != 'unknown':
                                neo4j_service.update_path_usage(path['pathId'])

                        response = {
                            "type": "search_path_result",
                            "status": "success",
                            "data": search_result
                        }
                    else:
                        response = {
                            "type": "search_path_result",
                            "status": "error",
                            "data": {
                                "message": "경로 검색 실패",
                                "query": search_request.query
                            }
                        }

                elif message['type'] == 'cleanup_paths':
                    # 시간 기반 경로 정리
                    cleanup_result = neo4j_service.cleanup_old_paths()

                    response = {
                        "type": "cleanup_result",
                        "status": "success",
                        "data": cleanup_result or {"message": "정리 실패"}
                    }

                elif message['type'] == 'save_contribution_path':
                    # 기여모드 경로 저장 (디버깅을 위해 DB 저장 없이 로그만 출력)
                    try:
                        contribution_data = ContributionPathData(**message['data'])
                        print(f"\n=== 기여모드 데이터 수신 ===")
                        print(f"SessionId: {contribution_data.sessionId}")
                        print(f"Task: {contribution_data.task}")
                        print(f"IsPartial: {contribution_data.isPartial}")
                        print(f"IsComplete: {contribution_data.isComplete}")
                        print(f"TotalSteps: {contribution_data.totalSteps}")
                        print(f"Steps Count: {len(contribution_data.steps)}")

                        for i, step in enumerate(contribution_data.steps):
                            print(f"\n--- Step {i+1} ---")
                            print(f"URL: {step.url}")
                            print(f"Title: {step.title}")
                            print(f"Action: {step.action}")
                            print(f"Selector: {step.selector}")
                            print(f"HTML Attributes: {step.htmlAttributes}")
                            print(f"Timestamp: {step.timestamp}")

                        print(f"\n=== Raw Data ===")
                        print(f"Full message data: {message['data']}")
                        print(f"=== 기여모드 데이터 분석 완료 ===\n")

                        response = {
                            "type": "contribution_save_result",
                            "status": "success",
                            "data": {
                                "message": "기여모드 데이터 로그 출력 완료 (DB 저장 안함)",
                                "sessionId": contribution_data.sessionId,
                                "task": contribution_data.task,
                                "stepsCount": len(contribution_data.steps),
                                "isComplete": contribution_data.isComplete
                            }
                        }
                    except Exception as e:
                        print(f"기여모드 데이터 처리 실패: {e}")
                        response = {
                            "type": "contribution_save_result",
                            "status": "error",
                            "data": {
                                "message": f"기여모드 데이터 처리 실패: {str(e)}",
                                "sessionId": message.get('data', {}).get('sessionId', 'unknown'),
                                "savedSteps": 0
                            }
                        }

                elif message['type'] == 'create_indexes':
                    # 벡터 인덱스 생성
                    index_result = neo4j_service.create_vector_indexes()

                    response = {
                        "type": "index_creation_result",
                        "status": "success" if index_result else "error",
                        "data": {
                            "message": "인덱스 생성 완료" if index_result else "인덱스 생성 실패"
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

            # DateTime 객체를 직렬화 가능하도록 변환하는 커스텀 인코더
            def json_serializer(obj):
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                elif hasattr(obj, 'to_native'):
                    return obj.to_native().isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

            await websocket.send_text(json.dumps(response, default=json_serializer, ensure_ascii=False))
            print(f"응답 전송 완료: {response['type']}")

    except WebSocketDisconnect:
        print("WebSocket 연결 종료 - vowser-backend 연결 해제")
    except Exception as e:
        print(f"WebSocket 오류: {e}")
        await websocket.close()