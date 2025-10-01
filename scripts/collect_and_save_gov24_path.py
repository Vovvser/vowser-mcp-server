"""
정부24 주민등록등본 경로 자동 수집 및 Neo4j 저장 스크립트
gov24_test.py의 경로를 분석하여 Neo4j에 자동으로 저장합니다.
"""

import sys
import os
import io

# Windows 콘솔 인코딩 문제 해결
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.services.neo4j_service import save_path_to_neo4j, add_metadata_to_path, check_graph_structure

# 정부24 주민등록등본 발급 경로 데이터
gov24_path_data = {
    "sessionId": "gov24_rrc_session_001",
    "startCommand": "정부24에서 주민등록등본 발급하기",
    "completePath": [
        {
            "order": 0,
            "url": "https://www.gov.kr/portal/main",
            "locationData": None,
            "semanticData": None
        },
        {
            "order": 1,
            "url": "https://www.gov.kr/portal/main",
            "locationData": {
                "primarySelector": "a[title='주민등록등본(초본)']",
                "fallbackSelectors": [
                    "a:has-text('주민등록등본(초본)')",
                    "a[href*='AA020InfoCappView'][href*='CappBizCD=13100000015']"
                ],
                "anchorPoint": "body",
                "relativePathFromAnchor": "a[title='주민등록등본(초본)']",
                "elementSnapshot": {
                    "tagName": "a",
                    "attributes": {
                        "title": "주민등록등본(초본)",
                        "href": "/portal/service/serviceInfo/AA020InfoCappView.do?CappBizCD=13100000015"
                    }
                }
            },
            "semanticData": {
                "textLabels": ["주민등록등본(초본)", "주민등록등본"],
                "contextText": {
                    "immediate": "바로가기 카드",
                    "section": "메인 페이지 서비스 목록",
                    "neighbor": ["민원서비스", "인기서비스"]
                },
                "pageInfo": {
                    "title": "정부24",
                    "url": "https://www.gov.kr/portal/main"
                },
                "actionType": "click"
            }
        },
        {
            "order": 2,
            "url": "https://www.gov.kr/portal/service/serviceInfo/AA020InfoCappView.do?CappBizCD=13100000015",
            "locationData": {
                "primarySelector": "#applyBtn",
                "fallbackSelectors": [
                    "button:has-text('발급하기')",
                    "a:has-text('발급하기')"
                ],
                "anchorPoint": "#contents",
                "relativePathFromAnchor": "#applyBtn",
                "elementSnapshot": {
                    "tagName": "button",
                    "attributes": {
                        "id": "applyBtn"
                    }
                }
            },
            "semanticData": {
                "textLabels": ["발급하기", "신청"],
                "contextText": {
                    "immediate": "서비스 상세",
                    "section": "서비스 신청 영역",
                    "neighbor": ["서비스 안내", "신청방법"]
                },
                "pageInfo": {
                    "title": "주민등록표 등본(초본) 교부 - 정부24",
                    "url": "https://www.gov.kr/portal/service/serviceInfo/AA020InfoCappView.do?CappBizCD=13100000015"
                },
                "actionType": "click"
            }
        },
        {
            "order": 3,
            "url": "https://www.gov.kr/portal/service/serviceInfo/AA020InfoCappView.do?CappBizCD=13100000015",
            "locationData": {
                "primarySelector": "#memberApplyBtn",
                "fallbackSelectors": [
                    "a:has-text('회원 신청하기')",
                    "a[href*='AA040OfferMainFrm'][href*='capp_biz_cd=13100000015']"
                ],
                "anchorPoint": "[role='dialog']",
                "relativePathFromAnchor": "#memberApplyBtn",
                "elementSnapshot": {
                    "tagName": "a",
                    "attributes": {
                        "id": "memberApplyBtn",
                        "href": "/portal/AA040OfferMainFrm.do?capp_biz_cd=13100000015"
                    }
                }
            },
            "semanticData": {
                "textLabels": ["회원 신청하기", "회원신청"],
                "contextText": {
                    "immediate": "로그인 모달",
                    "section": "로그인 방식 선택",
                    "neighbor": ["비회원 신청하기", "로그인"]
                },
                "pageInfo": {
                    "title": "주민등록표 등본(초본) 교부 - 정부24",
                    "url": "https://www.gov.kr/portal/service/serviceInfo/AA020InfoCappView.do?CappBizCD=13100000015"
                },
                "actionType": "click"
            }
        },
        {
            "order": 4,
            "url": "https://www.gov.kr/mw/AA040OfferMainFrm.do?capp_biz_cd=13100000015",
            "locationData": {
                "primarySelector": "button.login-type:has-text('간편인증')",
                "fallbackSelectors": [
                    "button:has-text('간편인증')"
                ],
                "anchorPoint": ".login-type-container",
                "relativePathFromAnchor": "button.login-type:has-text('간편인증')",
                "elementSnapshot": {
                    "tagName": "button",
                    "attributes": {
                        "class": "login-type"
                    }
                }
            },
            "semanticData": {
                "textLabels": ["간편인증", "간편 로그인"],
                "contextText": {
                    "immediate": "로그인 방식 선택 화면",
                    "section": "인증 방법 카드",
                    "neighbor": ["공동인증서", "금융인증서", "휴대폰 인증"]
                },
                "pageInfo": {
                    "title": "로그인 - 정부24",
                    "url": "https://www.gov.kr/mw/AA040OfferMainFrm.do?capp_biz_cd=13100000015"
                },
                "actionType": "click"
            }
        },
        {
            "order": 5,
            "url": "https://www.gov.kr/mw/AA040OfferMainFrm.do?capp_biz_cd=13100000015",
            "locationData": {
                "primarySelector": "iframe[src='/simpleCert.html'] >>> #oacx-request-btn-pc",
                "fallbackSelectors": [
                    "#oacx-request-btn-pc"
                ],
                "anchorPoint": "iframe[src='/simpleCert.html']",
                "relativePathFromAnchor": "#oacx-request-btn-pc",
                "elementSnapshot": {
                    "tagName": "button",
                    "attributes": {
                        "id": "oacx-request-btn-pc"
                    }
                }
            },
            "semanticData": {
                "textLabels": ["인증 요청", "카카오 간편인증"],
                "contextText": {
                    "immediate": "간편인증 입력 폼",
                    "section": "iframe 내부 인증 화면",
                    "neighbor": ["이름", "생년월일", "휴대폰 번호", "전체동의"]
                },
                "pageInfo": {
                    "title": "간편인증 - 정부24",
                    "url": "https://www.gov.kr/mw/AA040OfferMainFrm.do?capp_biz_cd=13100000015"
                },
                "actionType": "click"
            }
        },
        {
            "order": 6,
            "url": "https://www.gov.kr/mw/AA040OfferMainFrm.do?capp_biz_cd=13100000015",
            "locationData": {
                "primarySelector": "iframe[src='/simpleCert.html'] >>> button:has-text('인증 완료')",
                "fallbackSelectors": [
                    "button:has-text('인증 완료')"
                ],
                "anchorPoint": "iframe[src='/simpleCert.html']",
                "relativePathFromAnchor": "button:has-text('인증 완료')",
                "elementSnapshot": {
                    "tagName": "button"
                }
            },
            "semanticData": {
                "textLabels": ["인증 완료", "간편인증 완료"],
                "contextText": {
                    "immediate": "간편인증 결과 화면",
                    "section": "iframe 내부 인증 완료 버튼",
                    "neighbor": ["카카오톡 인증 완료 안내"]
                },
                "pageInfo": {
                    "title": "간편인증 - 정부24",
                    "url": "https://www.gov.kr/mw/AA040OfferMainFrm.do?capp_biz_cd=13100000015"
                },
                "actionType": "click"
            }
        },
        {
            "order": 7,
            "url": "https://www.gov.kr/mw/AA020OfferMainFrm.do",
            "locationData": {
                "primarySelector": "#btn_end",
                "fallbackSelectors": [
                    "button:has-text('신청하기')"
                ],
                "anchorPoint": ".apply-section",
                "relativePathFromAnchor": "#btn_end",
                "elementSnapshot": {
                    "tagName": "button",
                    "attributes": {
                        "id": "btn_end"
                    }
                }
            },
            "semanticData": {
                "textLabels": ["신청하기", "최종 신청"],
                "contextText": {
                    "immediate": "신청서 작성 완료",
                    "section": "신청서 하단 버튼 영역",
                    "neighbor": ["이전", "임시저장", "신청내역"]
                },
                "pageInfo": {
                    "title": "주민등록표 등본(초본) 교부 신청 - 정부24",
                    "url": "https://www.gov.kr/mw/AA020OfferMainFrm.do"
                },
                "actionType": "click"
            }
        },
        {
            "order": 8,
            "url": "https://www.gov.kr/mw/AA020InfoCappViewApp.do",
            "locationData": {
                "primarySelector": "button:has-text('문서출력')",
                "fallbackSelectors": [
                    "button[onclick*='printDocument']"
                ],
                "anchorPoint": ".application-result",
                "relativePathFromAnchor": "button:has-text('문서출력')",
                "elementSnapshot": {
                    "tagName": "button"
                }
            },
            "semanticData": {
                "textLabels": ["문서출력", "PDF 저장", "출력"],
                "contextText": {
                    "immediate": "신청 완료 내역",
                    "section": "신청 내역 목록",
                    "neighbor": ["신청일시", "처리상태", "상세보기"]
                },
                "pageInfo": {
                    "title": "신청내역 - 정부24",
                    "url": "https://www.gov.kr/mw/AA020InfoCappViewApp.do"
                },
                "actionType": "click"
            }
        }
    ]
}


def main():
    print("=" * 80)
    print("정부24 주민등록등본 발급 경로 → Neo4j 자동 저장")
    print("=" * 80)

    try:
        # 1. 메타데이터 추가 (경로 ID, 임베딩 생성 등)
        print("\n[1단계] 경로 데이터에 메타데이터 추가 중...")
        path_with_metadata = add_metadata_to_path(gov24_path_data)
        print(f"✓ 메타데이터 추가 완료")
        print(f"  - 경로 ID: {path_with_metadata['metadata']['pathId']}")
        print(f"  - 시작 명령: {path_with_metadata['startCommand']}")
        print(f"  - 총 단계 수: {len(path_with_metadata['completePath'])}")

        # 2. Neo4j에 저장
        print("\n[2단계] Neo4j에 경로 저장 중...")
        result = save_path_to_neo4j(path_with_metadata)
        print(f"✓ 저장 완료!")
        print(f"  - 상태: {result.get('status')}")
        print(f"  - 저장된 단계 수: {result.get('saved_steps')}")

        # 3. 그래프 구조 확인
        print("\n[3단계] Neo4j 그래프 구조 확인...")
        stats = check_graph_structure()

        print("\n" + "=" * 80)
        print("✓ 정부24 경로 데이터가 성공적으로 Neo4j에 저장되었습니다!")
        print("=" * 80)

        print("\n다음 명령으로 저장된 데이터를 확인할 수 있습니다:")
        print("  - 경로 시각화: visualize_paths('gov.kr')")
        print("  - 경로 검색: search_paths_by_query('주민등록등본 발급', domain_hint='gov.kr')")

    except Exception as e:
        print(f"\n[오류] 저장 중 문제가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())