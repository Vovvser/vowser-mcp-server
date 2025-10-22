"""
SRT 승차권 예매 경로 자동 수집 및 데이터 구조화 스크립트
srt_reserve2.py의 경로를 분석하여 새로운 DTO(PathSubmission)에 맞춰 데이터를 생성합니다.
"""

import sys
import os
import io
import json
from uuid import uuid4

# Windows 콘솔 인코딩 문제 해결
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 프로젝트 루트를 Python 경로에 추가 (실제 환경에 맞게 조정 필요)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# app.models.step.PathSubmission 을 사용하기 위함.
# 실제 DB 저장 로직은 주석 처리.
from app.services.neo4j_service import save_path_to_neo4j
from app.models.step import PathSubmission

# srt_reserve2.py를 기반으로 새로운 DB 구조(PathSubmission)에 맞춘 SRT 승차권 예매 경로 데이터
srt_path_submission = {
    "sessionId": str(uuid4()),
    "taskIntent": "SRT 승차권 예약하기",
    "domain": "etk.srail.kr",
    "steps": [
        {
            # 단계 1: SRT 메인 페이지에서 '로그인' 링크 클릭
            "url": "https://etk.srail.kr/",
            "domain": "etk.srail.kr",
            "action": "click",
            "description": "메인 화면에서 '로그인' 링크 클릭",
            "selectors": ["a:has-text('로그인')"],
            "textLabels": ["로그인"],
            "isInput": False,
            "shouldWait": False
        },
        {
            # 단계 2: 로그인 유형 '휴대전화번호' 선택
            "url": "https://etk.srail.kr/cmc/01/selectLoginForm.do?pageId=CTE0001",
            "domain": "etk.srail.kr",
            "action": "click",
            "description": "로그인 유형 중 '휴대전화번호' 라디오 버튼 선택",
            "selectors": ["#srchDvCd3"],
            "textLabels": ["휴대전화번호로 로그인", "핸드폰 번호로 로그인"],
            "isInput": False,
            "shouldWait": False
        },
        {
            # 단계 3-1: 휴대전화번호 입력
            "url": "https://etk.srail.kr/cmc/01/selectLoginForm.do?pageId=CTE0001",
            "domain": "etk.srail.kr",
            "action": "input",
            "description": "로그인 정보 '휴대전화번호' 입력",
            "selectors": ["#srchDvNm03"],
            "textLabels": ["휴대전화번호 입력", "핸드폰 번호 입력"],
            "isInput": True,
            "inputType": "telephone",
            "inputPlaceholder": None,
            "shouldWait": False
        },
        {
            # 단계 3-2: 비밀번호 입력
            "url": "https://etk.srail.kr/cmc/01/selectLoginForm.do?pageId=CTE0001",
            "domain": "etk.srail.kr",
            "action": "input",
            "description": "로그인 정보 '비밀번호' 입력",
            "selectors": ["#hmpgPwdCphd03"],
            "textLabels": ["비밀번호 입력"],
            "isInput": True,
            "inputType": "password",
            "inputPlaceholder": None,
            "shouldWait": False
        },
        {
            # 단계 4: '확인' 버튼 클릭하여 로그인
            "url": "https://etk.srail.kr/cmc/01/selectLoginForm.do?pageId=CTE0001",
            "domain": "etk.srail.kr",
            "action": "click",
            "description": "정보 입력 후 '확인' 버튼 클릭하여 로그인",
            "selectors": ["input[value='확인'].loginSubmit:not([disabled])"],
            "textLabels": ["확인", "로그인"],
            "isInput": False,
            "shouldWait": False
        },
        {
            # 단계 5: (로그인 후) 승차권 예매 페이지로 이동
            # srt_reserve2.py에서는 goto_search로 바로 이동하지만, 실제 사용자 흐름에서는
            # 메인 페이지의 '승차권 예매' 버튼을 클릭할 수 있습니다.
            # 여기서는 스크립트 흐름에 맞춰 직접 URL로 이동하는 것을 표현합니다.
            "url": "https://etk.srail.kr/hpg/hra/01/selectScheduleList.do",
            "domain": "etk.srail.kr",
            "action": "navigate", # 페이지 직접 이동을 나타내는 가상 액션
            "description": "승차권 조회 페이지로 이동",
            "selectors": [],
            "textLabels": ["승차권 조회 페이지"],
            "isInput": False,
            "shouldWait": False
        },
        {
            # 단계 6-1: 출발역 입력
            "url": "https://etk.srail.kr/hpg/hra/01/selectScheduleList.do",
            "domain": "etk.srail.kr",
            "action": "input",
            "description": "조회 정보 '출발역' 입력",
            "selectors": ["#dptRsStnCdNm"],
            "textLabels": ["출발역"],
            "isInput": True,
            "inputType": "text",
            "inputPlaceholder": "수서", # 예: 수서
            "shouldWait": False
        },
        {
            # 단계 6-2: 도착역 입력
            "url": "https://etk.srail.kr/hpg/hra/01/selectScheduleList.do",
            "domain": "etk.srail.kr",
            "action": "input",
            "description": "조회 정보 '도착역' 입력",
            "selectors": ["#arvRsStnCdNm"],
            "textLabels": ["도착역"],
            "isInput": True,
            "inputType": "text",
            "inputPlaceholder": "부산", # 예: 부산
            "shouldWait": False
        },
        {
            # 단계 6-3: 출발일 선택
            "url": "https://etk.srail.kr/hpg/hra/01/selectScheduleList.do",
            "domain": "etk.srail.kr",
            "action": "select", # select box 선택
            "description": "조회 정보 '출발일' 선택",
            "selectors": ["#dptDt"],
            "textLabels": ["출발일", "출발날짜"],
            "isInput": True,
            "inputType": "text",
            "inputPlaceholder": "2025/11/05(수)",
            "shouldWait": False
        },
        {
            # 단계 6-4: 출발시각 선택
            "url": "https://etk.srail.kr/hpg/hra/01/selectScheduleList.do",
            "domain": "etk.srail.kr",
            "action": "select", # select box 선택
            "description": "조회 정보 '출발시각' 선택",
            "selectors": ["#dptTm"],
            "textLabels": ["출발시각"],
            "isInput": True,
            "inputType": "text",
            "inputPlaceholder": "14",
            "shouldWait": False
        },
        {
            # 단계 7: '조회하기' 버튼 클릭
            "url": "https://etk.srail.kr/hpg/hra/01/selectScheduleList.do",
            "domain": "etk.srail.kr",
            "action": "click",
            "description": "조회 조건 입력 후 '조회하기' 버튼 클릭",
            "selectors": ["input[value='조회하기']"],
            "textLabels": ["조회하기"],
            "isInput": False,
            "shouldWait": False
        },
        {
            # 단계 8: 조회 결과에서 '예약하기' 버튼 클릭
            # srt_reserve2.py는 조건에 맞는 좌석을 필터링하지만, 여기서는 일반적인 경로를 정의합니다.
            "url": "https://etk.srail.kr/hpg/hra/01/selectScheduleList.do",
            "domain": "etk.srail.kr",
            "action": "click",
            "description": "조회된 열차 목록에서 '예약하기' 버튼 클릭",
            "selectors": [
                "#result-form > fieldset > div.tbl_wrap > table > tbody > tr > td:nth-child(7) > a.btn_burgundy_dark:has-text('예약하기'):first-of-type",
                "#result-form > fieldset > div.tbl_wrap > table > tbody > tr > td:nth-child(6) > a.btn_burgundy_dark:has-text('예약하기'):first-of-type",
                
            ],
            "textLabels": ["예약하기"],
            "isInput": False,
            "shouldWait": False
        }
    ]
}


def main():
    print("=" * 80)
    print("SRT 승차권 예매 경로 → 데이터 구조화 (New DTO)")
    print("=" * 80)

    try:
        print("\n[0단계] 딕셔너리 데이터를 Pydantic 모델 객체로 변환 (검증).")
        path_submission_object = PathSubmission(**srt_path_submission)
        print("\n[1단계] 새로운 DTO 구조(PathSubmission)로 경로 데이터 생성 완료.")
        print(f"  - Session ID: {srt_path_submission['sessionId']}")
        print(f"  - Task Intent: {srt_path_submission['taskIntent']}")
        print(f"  - Domain: {srt_path_submission['domain']}")
        print(f"  - 총 단계 수: {len(srt_path_submission['steps'])}")

        print("\n[2단계] 생성된 SRT 예매 경로 데이터 출력.")
        
        # JSON 직렬화를 위해 Pydantic 모델을 다시 dict로 변환
        path_data_dict = path_submission_object.model_dump()
        
        # 보기 좋게 JSON 형식으로 출력
        print(json.dumps(path_data_dict, indent=2, ensure_ascii=False))

        print("✓ SRT 예매 경로 데이터가 새로운 DTO 형식으로 성공적으로 생성 및 출력되었습니다.")
        print("   이 데이터를 WebSocket API(`save_new_path`)로 전송하여 Neo4j에 저장할 수 있습니다.")
        
        result = save_path_to_neo4j(path_submission_object)
        print(f"✓ 저장 완료!")
        print(f"  - 상태: {result.get('status')}")
        print(f"  - 저장된 단계 수: {result.get('steps_saved')}")       
    
    except Exception as e:
        print(f"\n[오류] 데이터 생성 또는 처리 중 문제가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())