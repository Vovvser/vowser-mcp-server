import json
import asyncio
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv, find_dotenv
from app.services import neo4j_service
from app.models.path import PathData, SearchPathRequest
from app.models.contribution import ContributionPathData
from app.models.step import PathSubmission

load_dotenv(find_dotenv())

app = FastAPI(title="Vowser MCP Server - WebSocket Only")

async def increment_has_step_weight(search_result: dict):
    """
    백그라운드에서 첫 번째 경로의 HAS_STEP 가중치를 +1 증가
    """
    try:
        matched_paths = search_result.get("matched_paths", [])
        if not matched_paths:
            return
            
        top_path = matched_paths[0]
        domain = top_path.get("domain")
        task_intent = top_path.get("taskIntent")
        
        if not domain or not task_intent:
            print("HAS_STEP 업데이트 건너뜀: domain 또는 taskIntent 누락")
            return
            
        if not neo4j_service.graph:
            print("Neo4j graph 연결 없음: HAS_STEP 업데이트 건너뜀")
            return
            
        # Neo4j 쿼리 실행
        neo4j_service.graph.query(
            """
            MATCH (r:ROOT {domain: $domain})-[rel:HAS_STEP {taskIntent: $taskIntent}]->(:STEP)
            SET rel.weight = coalesce(rel.weight, 0) + 1,
                rel.lastUpdated = datetime()
            RETURN rel.weight as newWeight
            """,
            {"domain": domain, "taskIntent": task_intent}
        )
        
        print(f"HAS_STEP 가중치 증가: domain={domain}, taskIntent={task_intent}")
        
    except Exception as e:
        print(f"HAS_STEP weight 증가 실패: {e}")

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행되는 이벤트"""
    print("Vowser MCP Server 시작 중...")
    
    # LangGraph 워크플로우 사전 초기화
    try:
        from app.services.langgraph_service import initialize_langgraph
        initialize_langgraph()
    except Exception as e:
        print(f"LangGraph 초기화 실패 (폴백 모드로 동작): {e}")
    
    print("서버 시작 완료")

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
                    # DEPRECATED: 기존 save_path (PathData 구조) - 새 구조로 마이그레이션 필요
                    response = {
                        "type": "path_save_result",
                        "status": "error",
                        "data": {
                            "message": "DEPRECATED: save_path is no longer supported. Please migrate to save_new_path with PathSubmission structure.",
                            "migration_guide": "See docs/DTO_API_DOCUMENTATION.md for new structure"
                        }
                    }

                elif message['type'] == 'save_new_path':
                    # 새로운 save_path (PathSubmission 구조)
                    path_submission = PathSubmission(**message['data'])
                    print(f"새 구조 경로 저장 시작: {path_submission.taskIntent}")

                    result = neo4j_service.save_path_to_neo4j(path_submission)

                    response = {
                        "type": "path_save_result",
                        "status": "success" if result['status'] == 'success' else "error",
                        "data": {
                            "message": "New path structure processed successfully!",
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
                    # DEPRECATED: 기존 search_path - 새 구조로 마이그레이션 필요
                    response = {
                        "type": "search_path_result",
                        "status": "error",
                        "data": {
                            "message": "DEPRECATED: search_path is no longer supported. Please use search_new_path.",
                            "migration_guide": "See docs/DTO_API_DOCUMENTATION.md"
                        }
                    }
                    '''
                elif message['type'] == 'search_new_path':
                    # 자연어 경로 검색 (새 구조)
                    try:
                        search_request = SearchPathRequest(**message['data'])
                        print(f"[NEW] 경로 검색 요청: {search_request.query}")

                        search_result = neo4j_service.search_paths_by_query(
                            search_request.query,
                            search_request.limit,
                            search_request.domain_hint
                        )
                        print(f"[NEW] 검색 결과: {search_result}")
                    except Exception as e:
                        print(f"[NEW] search_path 오류: {e}")
                        import traceback
                        traceback.print_exc()
                        search_result = None

                    if search_result:
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
                                "query": search_request.query if 'search_request' in locals() else "unknown"
                            }
                        }
                    '''
                
                elif message['type'] == 'search_new_path':
                    # LangGraph를 사용한 지능적 경로 검색
                    try:
                        search_request = SearchPathRequest(**message['data'])
                        print(f"[SMART] LangGraph 경로 검색 요청: {search_request.query}")

                        from app.services.langgraph_service import search_with_langgraph
                        
                        search_result = await search_with_langgraph(
                            query=search_request.query,
                            limit=search_request.limit,
                            domain_hint=search_request.domain_hint
                        )
                        print(f"[SMART] LangGraph 검색 결과: {search_result}")
                        
                        response = {
                            "type": "search_path_result",
                            "status": "success",
                            "data": search_result
                        }
                        
                        # 응답 후 백그라운드에서 HAS_STEP 가중치 증가
                        asyncio.create_task(increment_has_step_weight(search_result))
                    except Exception as e:
                        print(f"[SMART] LangGraph search_path 오류: {e}")
                        import traceback
                        traceback.print_exc()
                        
                        # LangGraph 실패 시 기존 방식으로 폴백
                        try:
                            search_request = SearchPathRequest(**message['data'])
                            fallback_result = neo4j_service.search_paths_by_query(
                                search_request.query,
                                search_request.limit,
                                search_request.domain_hint
                            )
                            response = {
                                "type": "search_path_result",
                                "status": "success",
                                "data": fallback_result
                            }
                            print(f"[SMART] 폴백 검색 성공")
                        except Exception as fallback_error:
                            print(f"[SMART] 폴백 검색도 실패: {fallback_error}")
                            response = {
                                "type": "search_path_result",
                                "status": "error",
                                "data": {
                                    "message": "LangGraph 및 폴백 검색 모두 실패",
                                    "query": message['data'].get('query', 'unknown'),
                                    "error": str(e)
                                }
                            }

                elif message['type'] == 'get_langgraph_structure':
                    # LangGraph 워크플로우 구조 정보 반환
                    try:
                        from app.services.langgraph_service import get_workflow_info, print_langgraph_structure
                        
                        # 콘솔에 구조 출력
                        print_langgraph_structure()
                        
                        # 클라이언트에 구조 정보 반환
                        workflow_info = get_workflow_info()
                        
                        response = {
                            "type": "langgraph_structure_result",
                            "status": "success",
                            "data": workflow_info
                        }
                    except Exception as e:
                        print(f"LangGraph 구조 정보 조회 실패: {e}")
                        response = {
                            "type": "langgraph_structure_result",
                            "status": "error",
                            "data": {
                                "message": f"LangGraph 구조 정보 조회 실패: {str(e)}"
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
                    # DEPRECATED: 기존 create_indexes - 새 구조로 마이그레이션 필요
                    response = {
                        "type": "index_creation_result",
                        "status": "error",
                        "data": {
                            "message": "DEPRECATED: create_indexes is no longer supported. Please use create_new_indexes.",
                            "migration_guide": "See docs/DTO_API_DOCUMENTATION.md"
                        }
                    }

                elif message['type'] == 'create_new_indexes':
                    # 벡터 인덱스 생성 (새 구조)
                    try:
                        neo4j_service.create_vector_indexes()
                        response = {
                            "type": "index_creation_result",
                            "status": "success",
                            "data": {
                                "message": "새 구조 인덱스 생성 완료"
                            }
                        }
                    except Exception as e:
                        response = {
                            "type": "index_creation_result",
                            "status": "error",
                            "data": {
                                "message": f"새 구조 인덱스 생성 실패: {str(e)}"
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