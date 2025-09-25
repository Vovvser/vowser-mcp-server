"""
Playwright 튜토리얼: 정부24 접속 → '주민등록표 등본(초본) 교부' 검색 → 서비스 카드 진입
- LangGraph 미사용, Playwright 단독 예제(동기 API)
- 로그인/간편인증은 본 튜토리얼 범위 밖(스샷으로 어디까지 갔는지만 확인)

실행:
  python gov24_playwright_tutorial.py
환경변수:
  HEADLESS=true   # 헤드리스 모드로 실행 (GUI 자동화 사용 시 false로 설정해야 함)
  SLOWMO=100      # 단계 사이 딜레이(ms)로 동작을 눈으로 보기 쉽게
"""

import os
import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# pyautogui 라이브러리가 필요합니다. GUI 자동화 단계에서 사용됩니다.
# 터미널에서 'pip install pyautogui opencv-python' 명령어로 미리 설치해주세요.
try:
    import pyautogui
    import pyperclip
except ImportError:
    print("[경고] pyautogui 라이브러리가 설치되지 않았습니다.")
    print("문서 출력 후 PDF 저장 단계에서 오류가 발생할 수 있습니다.")
    print("스크립트 실행 전 'pip install pyautogui opencv-python'을 실행해주세요.")

HEADLESS = os.environ.get("HEADLESS", "false").lower() == "true"
SLOWMO = int(os.environ.get("SLOWMO", "0"))
OUTDIR = Path("gov24_out")
OUTDIR.mkdir(exist_ok=True)

# --- 사용자 정보 설정 ---
# 이 부분의 값을 변경하여 다른 사용자의 정보로 자동화를 실행할 수 있습니다.
USER_INFO = {
    "name": "박대얼",
    "birth": "19980210",        # YYYYMMDD 형식
    "phone_prefix": "010",      # 통신사 번호
    "phone_suffix": "73745718"  # 나머지 휴대폰 번호
}

def take_shot(page, name):
    """페이지의 스크린샷을 찍어 저장합니다."""
    path = OUTDIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"[스크린샷] {path}")

def close_popup_if_exists(page):
    """
    정부24 메인 팝업(정기점검 안내 등)을 닫습니다.
    - 컨테이너: #layerModal_main_popup.iw-modal-auto.main-popup.on
    - 닫기 버튼: button.btn.tertiary.close-modal  (본문 하단)
    - 보조 닫기: button.btn-close-modal.close-modal (우측 상단 X)
    """
    try:
        # 1) 팝업 컨테이너가 붙어 있고 보이면 진행 (없으면 바로 리턴)
        modal = page.locator("#layerModal_main_popup")
        if not modal.count():
            print("[팝업] 컨테이너 없음 → 스킵")
            return
        # 보일 때까지 짧게 대기 (있지만 애니메이션 중일 수 있음)
        try:
            modal.wait_for(state="visible", timeout=3000)
        except PWTimeout:
            # 안 보이면 스킵
            if not modal.is_visible():
                print("[팝업] 컨테이너 비가시 → 스킵")
                return

        # 2) 컨테이너 범위 내 닫기 버튼 우선 클릭
        #    (다른 레이어가 가로막아도 force=True 로 강제 클릭)
        primary_close = modal.locator("button.btn.tertiary.close-modal")
        if primary_close.count() > 0:
            primary_close.first.click(force=True)
            print("[팝업] primary close-modal 클릭 완료")
            modal.wait_for(state="detached", timeout=2000)
            return

        # 3) 우상단 X 버튼 대체 셀렉터
        alt_close = page.locator("button.btn-close-modal.close-modal")
        if alt_close.count() > 0:
            alt_close.first.click(force=True)
            print("[팝업] alt close-modal(X) 클릭 완료")
            modal.wait_for(state="detached", timeout=2000)
            return

        # 4) '오늘 하루 그만 보기' 체크 후 닫기 (있을 경우)
        checkbox = page.locator("#chk_01_01")
        if checkbox.count() > 0 and not checkbox.first.is_checked():
            checkbox.first.check()
            print("[팝업] 오늘 하루 그만 보기 체크")

        any_close = modal.locator("button:has-text('닫기'), button.close-modal")
        if any_close.count() > 0:
            any_close.first.click(force=True)
            print("[팝업] 텍스트/폴백 닫기 클릭 완료")
            modal.wait_for(state="detached", timeout=2000)
            return

        # 5) 키보드 ESC 시도 (모달이 키 핸들링 할 때)
        page.keyboard.press("Escape")
        if not modal.is_visible():
            print("[팝업] ESC 로 닫힘")
            return

        # 6) 최후 수단: DOM 강제 제거 (튜토리얼/테스트 용)
        page.evaluate("document.querySelector('#layerModal_main_popup')?.remove()")
        print("[팝업] JS 강제 제거 처리")
    except Exception as e:
        # Detached 에러는 이미 닫혔다는 의미이므로 무시
        if "detache" not in str(e).lower():
            print(f"[팝업] 처리 실패(무시): {e}")

def click_rrc_shortcut(page):
    """
    메인 화면에서 '주민등록등본(초본)' 바로가기 <a>를 최대한 안정적으로 클릭한다.
    - 순서: role/name → title → 텍스트 포함 → href 패턴 → XPath
    """
    candidates = [
        # 1) 접근성 이름(가장 안정적)
        lambda: page.get_by_role("link", name="주민등록등본(초본)"),
        lambda: page.get_by_role("link", name="주민등록등본"),
        # 2) title 속성
        lambda: page.locator("a[title='주민등록등본(초본)']"),
        lambda: page.locator("a[title*='주민등록등본']"),
        # 3) 텍스트 포함
        lambda: page.locator("a:has-text('주민등록등본(초본)')"),
        lambda: page.locator("a:has-text('주민등록등본')"),
        # 4) href 패턴 (URL 구조가 바뀌어도 일부 키만 맞으면 탐지)
        lambda: page.locator("a[href*='AA020InfoCappView'][href*='CappBizCD=13100000015']"),
        # 5) XPath (텍스트 기반 최후 전 단계)
        lambda: page.locator("//a[contains(., '주민등록등본')]"),
    ]

    for i, maker in enumerate(candidates, 1):
        try:
            loc = maker()
            if loc.count() == 0:
                continue
            
            target = loc.first
            print(f"[RR 링크] 전략 #{i} 로 요소 발견 (count={loc.count()})")
            target.scroll_into_view_if_needed()
            
            # 일반 클릭 → 실패 시 force=True
            try:
                target.click(timeout=5000)
            except PWTimeout:
                print(f"[RR 링크] 일반 클릭 실패, 강제 클릭 시도...")
                target.click(timeout=5000, force=True)

            page.wait_for_load_state("networkidle", timeout=60_000)
            print(f"[RR 링크] 클릭 및 페이지 로드 완료")
            return True
        except Exception as e:
            print(f"[RR 링크] 전략 #{i} 실패: {e}")

    return False

def click_issue_button(page):
    """상세 페이지에서 '발급하기' 버튼 클릭."""
    try:
        # ID, 텍스트, 역할 등 다양한 방법으로 시도
        locators_to_try = [
            page.locator("#applyBtn"),
            page.get_by_role("button", name="발급하기"),
            page.locator("a:has-text('발급하기')")
        ]
        
        for loc in locators_to_try:
            if loc.count() > 0:
                btn = loc.first
                btn.scroll_into_view_if_needed()
                btn.click(force=True)
                print(f"[발급] '{btn.text_content()}' 버튼 클릭 완료")
                return True

        print("[발급] 버튼을 찾지 못했습니다.")
        return False
    except Exception as e:
        print(f"[발급] 클릭 실패: {e}")
        return False

def click_member_apply(page):
    """
    모달에서 '회원 신청하기' 링크 클릭.
    - 기본: id=#memberApplyBtn
    - 폴백: 접근성 이름 / 텍스트 / href 패턴 / JS 강제 클릭
    - 클릭 후 네비게이션(or networkidle) 대기
    """
    # 0) 모달 가시화 대기(있으면)
    try:
        # 모달 role=dialog 또는 class로 추정되는 컨테이너 후보
        modal = page.locator("[role='dialog'], .modal, .modal-wrap, .iw-modal-auto")
        if modal.count() > 0:
            try:
                modal.first.wait_for(state="visible", timeout=3000)
            except:
                pass
    except:
        pass

    # 1) id로 클릭 (가장 확실)
    btn = page.locator("#memberApplyBtn")
    if btn.count() > 0:
        btn.first.scroll_into_view_if_needed()
        with page.expect_navigation(wait_until="networkidle", timeout=60_000):
            try:
                btn.first.click(timeout=5000)
            except:
                btn.first.click(timeout=5000, force=True)
        print("[회원신청] #memberApplyBtn 클릭 성공")
        return True

    # 2) 접근성 이름/텍스트
    for maker in [
        lambda: page.get_by_role("link", name="회원 신청하기"),
        lambda: page.locator("a:has-text('회원 신청하기')"),
        lambda: page.locator("a[href*='AA040OfferMainFrm'][href*='capp_biz_cd=13100000015']")
    ]:
        loc = maker()
        if loc.count() == 0:
            continue
        loc = loc.first
        loc.scroll_into_view_if_needed()
        try:
            with page.expect_navigation(wait_until="networkidle", timeout=60_000):
                try:
                    loc.click(timeout=5000)
                except:
                    loc.click(timeout=5000, force=True)
            print("[회원신청] 대체 셀렉터 클릭 성공")
            return True
        except Exception as e:
            print(f"[회원신청] 대체 셀렉터 실패: {e}")

    print("[회원신청] 버튼을 끝내 찾지 못함")
    return False

def click_simple_auth(page):
    """로그인 방식 선택 화면에서 '간편인증' 카드를 클릭한다."""
    strategies = [
        # 가장 정확: 카드 구조 매칭
        lambda: page.locator("button.login-type:has-text('간편인증')"),
        # 접근성 이름
        lambda: page.get_by_role("button", name=re.compile("간편인증")),
    ]

    for i, make in enumerate(strategies, 1):
        try:
            loc = make()
            if loc.count() > 0:
                btn = loc.first
                btn.scroll_into_view_if_needed()
                
                # '간편인증' 버튼을 클릭합니다.
                # 클릭 후 페이지 전환(navigation)이 아니라 내용만 변경되므로,
                # 다음 함수에서 화면에 나타날 iframe이나 컨텐츠를 기다립니다.
                btn.click(force=True)
                
                print(f"[간편인증] 전략 #{i} 클릭 성공. 다음 단계로 진행합니다.")
                return True
        except Exception as e:
            print(f"[간편인증] 전략 #{i} 실패: {e}")

    print("[간편인증] 버튼을 찾지 못했습니다.")
    return False

def run_kakao_simple_auth(page, user_info):
    """
    간편인증 화면에서 정보를 입력하고 사용자의 인증 완료를 기다린 후 다음 단계로 진행합니다.
    """
    try:
        # --- 1. Iframe 탐색 및 대기 ---
        print("[간편인증] 간편인증 창(Iframe) 로딩 대기...")
        iframe_selector = 'iframe[src="/simpleCert.html"]'
        iframe = page.frame_locator(iframe_selector)
        
        # [핵심] Iframe 내부의 '이름' 입력창이 나타날 때까지 기다립니다.
        name_input_in_iframe = iframe.locator("#oacx_name")
        name_input_in_iframe.wait_for(state="visible", timeout=15000)
        
        print("[간편인증] Iframe 및 내부 컨텐츠 로딩 완료.")
        scope = iframe

        # --- 2. '카카오' 탭 선택 ---
        print("[간편인증] '카카오' 인증 방식 선택 시도...")
        # "카카오뱅크"가 아닌 "카카오"를 정확히 선택하기 위해 정규식에 단어 경계(\b)를 추가합니다.
        kakao_locators_to_try = [
            scope.get_by_alt_text(re.compile(r"\b카카오\b|\bKAKAO\b", re.IGNORECASE)),
            scope.get_by_role("button", name=re.compile(r"\b카카오\b|\bKAKAO\b", re.IGNORECASE)),
        ]
        
        clicked_kakao = False
        for i, locator in enumerate(kakao_locators_to_try, 1):
            if locator.count() > 0 and locator.first.is_visible(timeout=2000):
                locator.first.click(timeout=3000)
                print(f"[간편인증] '카카오' 선택 성공 (전략 #{i})")
                clicked_kakao = True
                break 

        if not clicked_kakao:
            print("[간편인증] '카카오' 선택 요소를 찾지 못했습니다. 기본 상태로 진행합니다.")
        
        # --- 3. 정보 입력 (속도 조절 추가) ---
        print("[간편인증] 사용자 정보 입력 시작...")
        scope.locator("#oacx_name").fill(user_info["name"]); time.sleep(0.5)
        scope.locator("#oacx_birth").fill(user_info["birth"]); time.sleep(0.5)
        scope.locator('select[data-id="oacx_phone1"]').select_option(value=user_info["phone_prefix"]); time.sleep(0.5)
        scope.locator("#oacx_phone2").fill(user_info["phone_suffix"]); time.sleep(0.5)
        print("[간편인증] 사용자 정보 입력 완료.")

        # --- 4. 동의 및 인증 요청 ---
        scope.locator("#totalAgree").check(); time.sleep(0.5)
        print("[간편인증] 전체동의 체크 완료")
        
        scope.locator("#oacx-request-btn-pc").click()
        print("[간편인증] '인증 요청' 버튼 클릭 완료.")

        # --- 5. 사용자 인증 대기 및 '인증 완료' 클릭 ---
        input("\n[사용자 확인 필요] 카카오톡 인증을 완료한 후, 여기에서 Enter 키를 눌러주세요...")
        
        print("[간편인증] '인증 완료' 버튼 클릭 시도...")
        auth_complete_btn = scope.get_by_role("button", name="인증 완료")
        auth_complete_btn.wait_for(state="visible", timeout=10000)

        with page.expect_navigation(wait_until="networkidle", timeout=60_000):
            auth_complete_btn.click()
        print("[간편인증] '인증 완료' 버튼 클릭 및 신청 페이지 이동 완료.")

    except PWTimeout as e:
        print(f"[간편인증] 처리 중 타임아웃 발생.")
        take_shot(page, "error_simple_auth_timeout")
        raise RuntimeError(f"간편인증 실패 (타임아웃): {e}")
    except Exception as e:
        print(f"[간편인증] 처리 중 예기치 않은 오류 발생: {e}")
        take_shot(page, "error_simple_auth_unexpected")
        raise RuntimeError(f"간편인증 실패: {e}")

def apply_for_document(page):
    """
    최종 신청서 페이지에서 천천히 스크롤하고 '신청하기' 버튼을 클릭합니다.
    """
    try:
        print("\n[신청서] 페이지를 천천히 아래로 스크롤합니다...")
        # 페이지 하단으로 여러 번에 나눠서 스크롤
        for i in range(5):
            page.mouse.wheel(0, 500)  # y-delta 500px 만큼 스크롤
            time.sleep(0.5)
            print(f"[신청서] 스크롤 중... ({i+1}/5)")

        print("[신청서] '신청하기' 버튼 탐색 및 클릭 시도...")
        apply_button = page.locator("#btn_end")
        apply_button.wait_for(state="visible", timeout=10000)
        
        # 버튼이 잘 보이도록 한 번 더 스크롤
        apply_button.scroll_into_view_if_needed()
        time.sleep(1) # 스크롤 후 잠시 대기

        apply_button.click()
        print("[신청서] '신청하기' 버튼 클릭 완료.")

        # 클릭 후 잠시 대기하여 결과 확인
        page.wait_for_load_state("networkidle", timeout=30_000)

    except PWTimeout:
        print("[신청서] '신청하기' 버튼을 찾지 못했거나 타임아웃이 발생했습니다.")
        take_shot(page, "error_apply_timeout")
        raise RuntimeError("신청하기 단계 실패 (타임아웃)")
    except Exception as e:
        print(f"[신청서] 신청하기 단계에서 예기치 않은 오류 발생: {e}")
        take_shot(page, "error_apply_unexpected")
        raise RuntimeError(f"신청하기 단계 실패: {e}")

def handle_document_printing(page, user_info):
    """
    신청 내역 페이지에서 최신 항목의 '문서출력'을 클릭하고,
    GUI 자동화(pyautogui)를 사용해 PDF로 저장합니다.
    """
    try:
        print("\n[문서출력] 신청 내역 목록 로딩 대기...")
        print_button = page.get_by_role("button", name="문서출력").first
        print_button.wait_for(state="visible", timeout=15000)
        print("[문서출력] 신청 내역 확인. 최신 항목의 '문서출력' 버튼을 클릭합니다.")

        with page.expect_popup() as popup_info:
            print_button.click()
        
        print_popup = popup_info.value
        print("[문서출력] 인쇄 미리보기 팝업창이 열렸습니다.")
        print_popup.wait_for_load_state("networkidle", timeout=60_000)

        # 1. pyautogui로 팝업창의 '인쇄' 버튼 클릭하여 OS 인쇄 대화상자 열기
        print("[GUI 자동화] pyautogui로 팝업창의 '인쇄' 버튼을 찾습니다...")
        time.sleep(2)  # 팝업창 UI가 완전히 렌더링될 시간을 줍니다.
        
        try:
            print_icon_location = pyautogui.locateCenterOnScreen('print_button_popup.png', confidence=0.9)
            if not print_icon_location:
                raise RuntimeError("팝업창에서 '인쇄' 버튼을 찾지 못했습니다. (print_button_popup.png)")
            
            print("[GUI 자동화] '인쇄' 버튼을 클릭하여 OS 인쇄 창을 엽니다...")
            pyautogui.click(print_icon_location)
        except pyautogui.PyAutoGUIException:
            raise RuntimeError("pyautogui가 화면의 이미지를 찾을 수 없습니다. 운영체제 화면 접근 권한을 확인해주세요.")

        time.sleep(3)  # OS 인쇄 대화상자가 나타날 시간을 줍니다.

        # 2. pyautogui로 OS 인쇄 대화상자 및 '다른 이름으로 저장' 창 제어
        print("[GUI 자동화] 지금부터 OS 인쇄 창을 제어합니다.")
        
        try:
            # 단계 A: 'PDF로 저장' 옵션 선택
            print("[GUI] 'PDF로 저장' 옵션을 선택하기 위해 드롭다운을 찾습니다...")
            
            dropdown_loc = pyautogui.locateCenterOnScreen('destination_dropdown.png', confidence=0.9)
            if dropdown_loc:
                pyautogui.click(dropdown_loc)
                print("[GUI] 대상 프린터 드롭다운('destination_dropdown.png') 클릭 완료.")
                time.sleep(1)
            else:
                print("[GUI] 대상 프린터 드롭다운을 찾지 못했습니다. 'PDF로 저장' 옵션을 바로 찾아봅니다.")

            save_pdf_option_loc = pyautogui.locateCenterOnScreen('save_as_pdf_option.png', confidence=0.9)
            if save_pdf_option_loc:
                pyautogui.click(save_pdf_option_loc)
                print("[GUI] 'PDF로 저장' 옵션('save_as_pdf_option.png') 클릭 완료.")
                time.sleep(1)
            else:
                print("[GUI] 'PDF로 저장' 옵션을 찾지 못했습니다. 기본 설정으로 진행될 수 있습니다.")

            # 단계 B: 인쇄 대화상자의 '인쇄' 버튼 클릭
            print("[GUI] 인쇄 창의 '인쇄' 버튼을 클릭합니다...")
            save_button_loc = pyautogui.locateCenterOnScreen('print_dialog_print_button.png', confidence=0.9)
            if not save_button_loc:
                raise RuntimeError("인쇄 대화상자에서 '인쇄' 버튼을 찾지 못했습니다. (print_dialog_print_button.png)")
            pyautogui.click(save_button_loc)
            print("[GUI] 인쇄 창의 '인쇄' 버튼 클릭 완료.")
            time.sleep(2)

            # 단계 C: '다른 이름으로 저장' 창 확인
            print("[GUI] '다른 이름으로 저장' 창이 나타날 때까지 대기...")
            save_dialog_pos = None
            for _ in range(10):
                save_dialog_pos = pyautogui.locateOnScreen('file_save_dialog.png', confidence=0.8)
                if save_dialog_pos:
                    print("[GUI] '다른 이름으로 저장' 창 확인.")
                    break
                time.sleep(1)
            if not save_dialog_pos:
                raise RuntimeError("'다른 이름으로 저장' 창을 찾지 못했습니다. (file_save_dialog.png)")

            # 단계 D: 주소 표시줄에 폴더 경로 입력
            print("[GUI] Alt+D 단축키로 주소창을 선택합니다.")
            pyautogui.hotkey('alt', 'd')
            time.sleep(1)

            folder_path = str(OUTDIR.resolve())
            pyperclip.copy(folder_path)
            print(f"[GUI] 클립보드에 복사된 폴더 경로: {folder_path}")
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(1)
            pyautogui.press('enter')
            time.sleep(1)

            # 단계 E: 파일 이름 입력란으로 이동 후 파일명 입력
            print("[GUI] Tab 키를 7번 눌러 '파일 이름' 입력란으로 이동합니다.")
            for _ in range(7):
                pyautogui.press('tab')
                time.sleep(0.2)
            
            file_name = "주민등록등본_" + user_info["name"] + ".pdf"
            pyperclip.copy(file_name)
            print(f"[GUI] 클립보드에 복사된 파일명: {file_name}")
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(1)

            # 단계 F: Enter를 눌러 저장 실행
            print("[GUI] Enter를 눌러 파일 저장을 실행합니다.")
            pyautogui.press('enter')
            time.sleep(2)

            full_path = OUTDIR / file_name
            if full_path.exists():
                print(f"[GUI 저장 완료] 파일이 '{full_path}' 경로에 저장되었습니다.")
            else:
                # 파일 저장 실패 시 대비책
                print(f"[GUI 저장 확인] 파일이 '{full_path}' 경로에 생성되지 않았습니다. Enter를 한 번 더 누릅니다.")
                pyautogui.press('enter')
                time.sleep(2)
                if full_path.exists():
                    print(f"[GUI 저장 완료-재시도] 파일이 '{full_path}' 경로에 저장되었습니다.")
                else:
                    print(f"[GUI 저장 실패] 최종적으로 파일 저장에 실패했습니다.")


        except (pyautogui.PyAutoGUIException, RuntimeError) as gui_error:
            print(f"\n[GUI 자동화 오류] OS 인쇄 창 제어 중 문제가 발생했습니다: {gui_error}")
            print("1. 스크립트와 동일한 폴더에 필요한 .png 스크린샷 파일들이 있는지 확인해주세요.")
            print("2. 스크린샷이 현재 PC의 화면 요소와 정확히 일치하는지 확인해주세요.")
            print("3. 스크립트 실행 중 다른 창이 인쇄 창을 가리지 않았는지 확인해주세요.")
            raise
        finally:
            if not print_popup.is_closed():
                print_popup.close()

    except Exception as e:
        print(f"[문서출력] 처리 중 오류 발생: {e}")
        take_shot(page, "error_printing_unexpected")
        raise


def main():
    if HEADLESS and 'pyautogui' in globals():
        print("[오류] pyautogui를 사용하는 GUI 자동화는 헤드리스(Headless) 모드에서 실행할 수 없습니다.")
        print("환경변수 HEADLESS를 'false'로 설정하거나 제거한 후 다시 시도해주세요.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=SLOWMO)
        context = browser.new_context(
            accept_downloads=True,
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # 1) 정부24 메인 진입
            print("\n[단계 1] 정부24 메인 페이지 접속")
            page.goto("https://www.gov.kr/portal/main", wait_until="networkidle", timeout=60_000)
            take_shot(page, "step1_home_loaded")
            
            close_popup_if_exists(page)
            take_shot(page, "step1_after_popup_closed")

            # 2) '주민등록등본(초본)' 링크 직접 클릭
            print("\n[단계 2] '주민등록등본(초본)' 바로가기 클릭")
            if not click_rrc_shortcut(page):
                raise RuntimeError("주민등록등본(초본) 링크를 찾거나 클릭하지 못했습니다.")
            take_shot(page, "step2_service_page_loaded")

            # 3) '발급하기' 버튼 클릭
            print("\n[단계 3] '발급하기' 버튼 클릭")
            if not click_issue_button(page):
                raise RuntimeError("발급하기 버튼 클릭 실패")
            take_shot(page, "step3_login_modal_appeared")
            
            # 4) '회원 신청하기' 클릭
            print("\n[단계 4] '회원 신청하기' 버튼 클릭")
            if not click_member_apply(page):
                raise RuntimeError("회원 신청하기 클릭 실패")
            take_shot(page, "step4_login_page_loaded")
            
            # 5) '간편인증' 방식 선택
            print("\n[단계 5] '간편인증' 방식 선택")
            if not click_simple_auth(page):
                raise RuntimeError("간편인증 버튼 클릭 실패")
            take_shot(page, "step5_simple_auth_page_loaded")

            # 6) 카카오 간편인증 정보 입력 및 완료
            print("\n[단계 6] 카카오 간편인증 정보 입력 및 완료")
            run_kakao_simple_auth(page, USER_INFO)
            take_shot(page, "step6_auth_complete_and_navigated")

            # 7) 최종 신청서 확인 및 '신청하기' 클릭
            print("\n[단계 7] 최종 신청서 확인 및 '신청하기' 클릭")
            apply_for_document(page)
            take_shot(page, "step7_application_submitted")

            # 8) 신청 내역 확인 및 문서 출력/저장
            print("\n[단계 8] 신청 내역 확인 및 문서 저장")
            handle_document_printing(page, USER_INFO)
            take_shot(page, "step8_document_saved")
            
            print("\n[성공] 모든 단계가 완료되었습니다. 60초 후 종료됩니다.")
            time.sleep(60)

        except Exception as e:
            print(f"\n[오류] 스크립트 실행 중 오류가 발생했습니다: {e}")
            take_shot(page, "final_error_state")
        finally:
            print("\n[종료] 튜토리얼을 마칩니다. 스크린샷과 PDF는 'gov24_out/' 폴더에 저장되었습니다.")
            context.close()
            browser.close()

if __name__ == "__main__":
    main()
