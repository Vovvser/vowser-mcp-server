"""
정부24 주민등록등본 경로 자동 수집 및 Neo4j 저장 스크립트 (리팩토링된 DB 구조용)
gov24_test.py의 경로를 분석하여 새로운 DTO(PathSubmission)에 맞춰 Neo4j에 저장합니다.
"""

import sys
import os
import io
from uuid import uuid4
from pydantic import BaseModel, Field

# Windows 콘솔 인코딩 문제 해결
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 프로젝트 루트를 Python 경로에 추가 (실제 환경에 맞게 조정 필요)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.services.neo4j_service import save_path_to_neo4j, check_graph_structure
from app.models.step import StepData, PathSubmission

# 새로운 DB 구조(PathSubmission)에 맞춘 정부24 주민등록등본 발급 경로 데이터
gov24_path_submission = {
    "sessionId": str(uuid4()),
    "taskIntent": "정부24 주민등록등본 발급",
    "domain": "gov.kr",
    "steps": [
        {
            # 단계 1: 메인 페이지에서 '주민등록등본(초본)' 바로가기 클릭
            "url": "https://www.gov.kr/",
            "domain": "gov.kr",
            "action": "click",
            "description": "메인 화면에서 '주민등록등본(초본)' 바로가기 클릭",
            "selectors": [
                "a[title='주민등록등본(초본)']",
                "a:has-text('주민등록등본(초본)')",
                "a[href*='AA020InfoCappView'][href*='CappBizCD=13100000015']"
            ],
            "textLabels": ["주민등록등본(초본)", "주민등록등본"],
            "isInput": False,
            "shouldWait": False
        },
        {
            # 단계 2: 서비스 상세 페이지에서 '발급하기' 버튼 클릭
            "url": "https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=13100000015&HighCtgCD=A01010001&tp_seq=01&Mcode=10200",
            "domain": "gov.kr",
            "action": "click",
            "description": "서비스 상세 정보 확인 후 '발급하기' 버튼 클릭",
            "selectors": [
                "#applyBtn",
                "button:has-text('발급하기')",
                "a:has-text('발급하기')"
            ],
            "textLabels": ["발급하기", "신청"],
            "isInput": False,
            "shouldWait": False
        },
        {
            # 단계 3: 로그인 모달에서 '회원 신청하기' 클릭
            "url": "https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=13100000015&HighCtgCD=A01010001&tp_seq=01&Mcode=10200",
            "domain": "gov.kr",
            "action": "click",
            "description": "로그인 안내 모달에서 '회원 신청하기' 버튼 클릭",
            "selectors": [
                "#memberApplyBtn",
                "a:has-text('회원 신청하기')",
                "a[href*='AA040OfferMainFrm'][href*='capp_biz_cd=13100000015']"
            ],
            "textLabels": ["회원 신청하기"],
            "isInput": False,
            "shouldWait": False
        },
        {
            # 단계 4: 로그인 방식 선택 화면에서 '간편인증' 클릭
            "url": "https://www.gov.kr/mw/AA040OfferMainFrm.do?capp_biz_cd=13100000015",
            "domain": "gov.kr",
            "action": "click",
            "description": "로그인 방식 중 '간편인증' 선택",
            "selectors": [
                "button.login-type:has-text('간편인증')",
                "button:has-text('간편인증')"
            ],
            "textLabels": ["간편인증"],
            "isInput": False,
            "shouldWait": False
        },
        {
            # 단계 5-1: 로그인 방식 선택 화면에서 '간편인증' 클릭
            "url": "https://www.gov.kr/mw/AA040OfferMainFrm.do?capp_biz_cd=13100000015",
            "domain": "gov.kr",
            "action": "click",
            "description": "간편인증 방식 중 '카카오톡' 선택",
            "selectors": [
                "li:has(.label-nm:has-text(/^카카오톡$/)) a.logoBg"
            ],
            "textLabels": ["카카오톡 인증"],
            "isInput": False,
            "shouldWait": False
        },
        {
            # 단계 5-2-1: 간편인증 이름 입력 (사용자 입력이 필요한 단계)
            # action: 'input'으로 지정하여 사용자 입력이 필요한 단계임을 명시
            "url": "https://www.gov.kr/mw/AA040OfferMainFrm.do?capp_biz_cd=13100000015",
            "domain": "gov.kr",
            "action": "input",
            "description": "간편인증 정보 '이름' 입력",
            "selectors": ["#oacx_name"],
            "textLabels": ["이름 입력"],
            "isInput": True,
            "inputType": "text",
            "inputPlaceholder": None,
            "shouldWait": False
        },
        {
            # 단계 5-2-2: 간편인증 생년월일 입력 (사용자 입력이 필요한 단계)
            "url": "https://www.gov.kr/mw/AA040OfferMainFrm.do?capp_biz_cd=13100000015",
            "domain": "gov.kr",
            "action": "input",
            "description": "간편인증 정보 '생년월일' 입력",
            "selectors": ["#oacx_birth"],
            "textLabels": ["생년월일 입력"],
            "isInput": True,
            "inputType": "text",
            "inputPlaceholder": None,
            "shouldWait": False
        },
        {
            # 단계 5-2-3: 간편인증 핸드폰 뒷 번호 입력 (사용자 입력이 필요한 단계)
            "url": "https://www.gov.kr/mw/AA040OfferMainFrm.do?capp_biz_cd=13100000015",
            "domain": "gov.kr",
            "action": "input",
            "description": "간편인증 정보 '핸드폰 뒷 번호' 입력",
            "selectors": ["#oacx_phone2"],
            "textLabels": ["핸드폰 뒷 번호 입력"],
            "isInput": True,
            "inputType": "text",
            "inputPlaceholder": None,
            "shouldWait": False
        },
        {
            # 단계 5-2-4: '전체동의' 체크 버튼 클릭
            "url": "https://www.gov.kr/mw/AA040OfferMainFrm.do?capp_biz_cd=13100000015",
            "domain": "gov.kr",
            "action": "click",
            "description": "정보 입력 후 '전체동의' 체크 버튼 클릭",
            "selectors": ["#totalAgree"],
            "textLabels": ["전체동의 체크"],
            "isInput": False,
            "shouldWait": False
        },
        {
            # 단계 6: '인증 요청' 버튼 클릭
            "url": "https://www.gov.kr/mw/AA040OfferMainFrm.do?capp_biz_cd=13100000015",
            "domain": "gov.kr",
            "action": "click",
            "description": "'인증 요청' 버튼 클릭",
            "selectors": ["#oacx-request-btn-pc"],
            "textLabels": ["인증 요청"],
            "isInput": False,
            "shouldWait": False
        },
        {
            # 단계 7: 사용자 카카오톡 인증 대기 (사용자 개입이 필요한 대기 단계)
            "url": "https://www.gov.kr/mw/AA040OfferMainFrm.do?capp_biz_cd=13100000015",
            "domain": "gov.kr",
            "action": "wait",
            "description": "사용자 카카오톡 인증 완료 대기",
            "selectors": [], # 특정 UI 요소가 아닌 시간/이벤트 기반 대기
            "textLabels": ["카카오톡 인증 완료 대기"],
            "isInput": False,
            "shouldWait": True,
            "waitMessage": "카카오톡으로 전송된 본인인증 요청을 완료한 후, 다음 단계를 진행하세요.",
            "maxWaitTime": 300 # 5분
        },
        {
            # 단계 8: '인증 완료' 버튼 클릭
            "url": "https://www.gov.kr/mw/AA040OfferMainFrm.do?capp_biz_cd=13100000015",
            "domain": "gov.kr",
            "action": "click",
            "description": "카카오톡 인증 후 '인증 완료' 버튼 클릭",
            "selectors": ["button:has-text('인증 완료')"],
            "textLabels": ["인증 완료"],
            "isInput": False,
            "shouldWait": False
        },
        {
            # 단계 9: 최종 신청서에서 '신청하기' 버튼 클릭
            "url": "https://www.gov.kr/mw/AA020InfoCappViewApp.do",
            "domain": "gov.kr",
            "action": "click",
            "description": "최종 신청 정보 확인 후 '신청하기' 버튼 클릭",
            "selectors": ["#btn_end"],
            "textLabels": ["신청하기"],
            "isInput": False,
            "shouldWait": False
        },
        {
            # 단계 10: 신청 내역 페이지에서 '문서출력' 클릭
            "url": "https://www.gov.kr/mw/AA020InfoCappViewApp.do",
            "domain": "gov.kr",
            "action": "click",
            "description": "처리 완료된 내역의 '문서출력' 버튼 클릭",
            "selectors": ["button:has-text('문서출력')"],
            "textLabels": ["문서출력", "출력"],
            "isInput": False,
            "shouldWait": False
        }
    ]
}


def main():
    print("=" * 80)
    print("정부24 주민등록등본 발급 경로 → Neo4j 자동 저장 (New DTO)")
    print("=" * 80)

    try:
        # 이 스크립트는 데이터 구조를 생성하는 데 중점을 둡니다.
        # 실제 Neo4j에 저장하려면 아래 주석 처리된 부분을
        # 프로젝트의 서비스 함수와 연결해야 합니다.
        print("\n[0단계] 딕셔너리 데이터를 Pydantic 모델 객체로 변환.")
        
        path_submission_object = PathSubmission(**gov24_path_submission)

        print("\n[1단계] 새로운 DTO 구조(PathSubmission)로 경로 데이터 생성 완료.")
        print(f"  - Session ID: {gov24_path_submission['sessionId']}")
        print(f"  - Task Intent: {gov24_path_submission['taskIntent']}")
        print(f"  - Domain: {gov24_path_submission['domain']}")
        print(f"  - 총 단계 수: {len(gov24_path_submission['steps'])}")
        
        print("\n[2단계] Neo4j에 경로 저장 (시뮬레이션)")
        
        result = save_path_to_neo4j(path_submission_object)
        print(f"✓ 저장 완료!")
        print(f"  - 상태: {result.get('status')}")
        print(f"  - 저장된 단계 수: {result.get('steps_saved')}")

        print("\n[3단계] Neo4j 그래프 구조 확인 (시뮬레이션)")
        stats = check_graph_structure()
        print(f"  - ROOT 노드 수: {stats.get('root_nodes')}")
        print(f"  - STEP 노드 수: {stats.get('step_nodes')}")

        print("\n" + "=" * 80)
        print("✓ 정부24 경로 데이터가 새로운 DTO 형식으로 성공적으로 생성되었습니다.")
        print("   이 데이터를 WebSocket API(`save_path_refactored`) 또는")
        print("   내부 서비스 함수로 전송하여 Neo4j에 저장할 수 있습니다.")
        print("=" * 80)


    except Exception as e:
        print(f"\n[오류] 데이터 생성 또는 처리 중 문제가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())