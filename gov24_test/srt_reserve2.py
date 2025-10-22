import asyncio
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple
from dotenv import load_dotenv
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
    Page,
    Locator,
)

"""
SRT 예매 자동화 (Python Playwright)
- 환경 변수(.env)에 저장된 휴대전화번호와 비밀번호를 이용해 자동 로그인
- 조회 폼(출발/도착/날짜/시간) 입력 → 조회하기 → 결과 필터링 → '예약하기' 클릭
- 창 유지 옵션(KEEP_BROWSER_OPEN), slow_mo 지원

※ 캡차/2단계 인증은 수동 처리 필요
"""

# ---- 설정값 ----------------------------------------------------
SRT_HOME = "https://etk.srail.kr/"
SEARCH_URL = "https://etk.srail.kr/hpg/hra/01/selectScheduleList.do"
HEADLESS = False
SLOW_MO = 150
KEEP_BROWSER_OPEN = True
KEEP_OPEN_MS = 3_600_000
WAIT_FOR_POPUP_TIMEOUT = 5_000 
MAX_RETRIES = 5              
RETRY_DELAY_MS = 2000
RESERVATION_DELAY_MS = 3000   # 예약 클릭 전 대기 시간 (3초로 변경, 5초는 너무 길 수 있음)

# =====================
# ✅ 사용자 파라미터
# =====================
class SearchParams:
    def __init__(
        self,
        srt_phone: str,
        srt_password: str,
        depart_station: str,    # 예: "수서"
        arrive_station: str,    # 예: "부산"
        date_str: str,          # "YYYYMMDD" 형식, 예: "20251023"
        time_start: Optional[str] = None,  # "HH:MM" (포함)
        time_end: Optional[str] = None,    # "HH:MM" (포함)
        seat_priority: Optional[List[str]] = None  # 예: ["일반실", "특실"]
    ):
        self.srt_phone = srt_phone
        self.srt_password = srt_password
        self.depart_station = depart_station
        self.arrive_station = arrive_station
        self.date_str = date_str
        self.time_start = time_start
        self.time_end = time_end
        self.seat_priority = seat_priority or ["일반실", "특실"]

# =====================
# 🔧 사이트 셀렉터 설정 (자동 로그인 요소 추가)
# =====================
SELECTORS = {
    # 로그인 폼 URL
    "login_url": "https://etk.srail.kr/cmc/01/selectLoginForm.do?pageId=CTE0001",
    # 홈 페이지의 로그인 링크/버튼 추가
    "link_login_home": "a:has-text('로그인')",
    # 로그인 요소 (휴대전화번호 방식)
    "radio_phone_login": "#srchDvCd3",
    "input_phone_number": "#srchDvNm03",
    "input_password": "#hmpgPwdCphd03",
    "btn_login_submit": "input[value='확인'].loginSubmit:not([disabled])",
    
    # 조회 폼
    "input_depart": "#dptRsStnCdNm",
    "input_arrive": "#arvRsStnCdNm",
    "autocomplete_item": ".station_layer a", # 자동완성 항목 (현재 코드에서는 미사용)
    "input_date": "#dptDt",
    "select_time": "#dptTm",
    "btn_inquiry": "input[value='조회하기']",

    # 결과 테이블
    "result_rows": "#result-form > fieldset > div.tbl_wrap > table > tbody > tr",
    "col_depart_time": "td:nth-child(4) > em.time",
    "col_arrive_time": "td:nth-child(5) > em.time",
    # 예약 버튼 (각 행 내부에서 찾음)
    "reserve_button_special": "td:nth-child(6) a:not(.btn_silver):has-text('예약하기')",
    "reserve_button_general": "td:nth-child(7) a:not(.btn_silver):has-text('예약하기')",
}

# =====================
# ⏱️ 유틸
# =====================

def format_date_for_srt(date_str: str) -> str:
    """ "YYYYMMDD" 형식의 문자열을 "YYYY/MM/DD(요일)" 형식으로 변환합니다. """
    try:
        dt = datetime.strptime(date_str, "%Y%m%d")
        weekdays = ["월", "화", "수", "목", "금", "토", "일"]
        day_of_week = weekdays[dt.weekday()]
        return f"{dt.strftime('%Y/%m/%d')}({day_of_week})"
    except ValueError:
        print(f"[WARN] 잘못된 날짜 형식: '{date_str}'. 변환하지 않고 반환합니다.")
        return date_str

def hhmm_to_min(hhmm: str) -> int:
    """ "HH:MM" 형식의 문자열을 분으로 변환합니다. """
    try:
        t = datetime.strptime(hhmm.strip(), "%H:%M")
        return t.hour * 60 + t.minute
    except ValueError:
        # 시간 형식 파싱 실패 시 -1 반환 대신, 0분으로 간주하여 비교 가능하게 함 (선택적)
        return -1

async def get_text_safe(loc: Locator) -> str:
    """ 로케이터에서 안전하게 텍스트를 추출합니다. """
    try:
        s = (await loc.first.text_content()) or ""
        return " ".join(s.split())
    except Exception:
        return ""

# =====================
# 🔐 로그인 & 페이지 이동 (자동 로그인 함수 추가)
# =====================

async def login_by_phone_number(page: Page, phone: str, password: str):
    """
    홈페이지에서 로그인 버튼을 클릭하여 로그인 페이지로 이동 후,
    휴대전화번호와 비밀번호를 이용하여 SRT에 자동 로그인합니다.
    """
    print("[INFO] 자동 로그인을 시도합니다...")
    
    # 1. 홈 페이지로 이동
    await page.goto(SRT_HOME, wait_until="domcontentloaded")

    # 2. 로그인 버튼 클릭 (로그인 페이지로 이동 기대)
    print("[INFO] 홈 페이지에서 '로그인' 버튼을 클릭하여 로그인 페이지로 이동합니다.")
    try:
        async with page.expect_navigation(timeout=10_000):
            await page.locator(SELECTORS["link_login_home"]).click()
    except PlaywrightTimeoutError:
        print("[ERROR] '로그인' 버튼 클릭 후 페이지 이동 시간 초과.")
        raise Exception("Login Failed: Timeout after clicking login button.")

    # 3. 휴대전화번호 라디오 버튼 클릭
    await page.locator(SELECTORS["radio_phone_login"]).click()
    print("[INFO] 휴대전화번호 로그인 유형 선택.")

    # 4. 휴대전화번호 입력
    # Playwright는 JS의 하이픈 제거 로직을 따르지 않으므로, 하이픈 없는 번호로 입력해야 합니다.
    # 하지만 SRT는 입력 시 JS로 하이픈을 넣기 때문에, 하이픈이 없는 번호를 입력하는 것이 더 안전합니다.
    phone_no_hyphen = phone.replace("-", "")
    await page.locator(SELECTORS["input_phone_number"]).fill(phone_no_hyphen)
    print(f"[INFO] 휴대전화번호 입력 완료: {phone_no_hyphen}")

    # 5. 비밀번호 입력
    await page.locator(SELECTORS["input_password"]).fill(password)
    print("[INFO] 비밀번호 입력 완료.")

    # 6. 확인 (로그인) 버튼 클릭
    try:
        async with page.expect_navigation(timeout=10_000):
            await page.locator(SELECTORS["btn_login_submit"]).click()

        # 로그인 성공 확인 (URL이 SRT_HOME으로 이동했는지 확인)
        current_url = page.url
        if SRT_HOME in current_url:
            print("[SUCCESS] 자동 로그인 성공.")
        else:
            # 실패 시 URL이 로그인 페이지 그대로이거나 다른 오류 페이지일 수 있음
            print("[ERROR] 자동 로그인 실패. ID/PW 또는 캡차/2단계 인증을 확인하세요.")
            raise Exception("Login Failed: Not redirected to home page.")

    except PlaywrightTimeoutError:
        print("[ERROR] 자동 로그인 실패. 페이지 이동 시간 초과. ID/PW 오류 또는 캡차/2단계 인증 확인 필요.")
        raise Exception("Login Failed: Timeout during navigation.")
    except Exception as e:
        print(f"[ERROR] 로그인 중 오류 발생: {e}")
        raise

async def ensure_logged_in(context, page: Page, p: SearchParams):
    if not p.srt_phone or not p.srt_password:
        print("[ERROR] 자동 로그인을 위한 SRT_PHONE 또는 SRT_PASSWORD 환경 변수가 설정되지 않았습니다.")
        print("[INFO] Playwright 브라우저가 열리면 수동으로 로그인해주세요.")
        
        # 수동 로그인 모드
        await page.goto(SRT_HOME, wait_until="domcontentloaded")
        input("SRT 웹사이트에 수동 로그인이 완료되면 Enter 키를 눌러주세요... ")
    else:
        # 자동 로그인 모드
        await login_by_phone_number(page, p.srt_phone, p.srt_password)


async def goto_search(page: Page):
    """시간표 조회 페이지로 이동하고 팝업을 닫습니다."""
    print("[INFO] 조회 페이지로 이동합니다...")
    await page.goto(SEARCH_URL, wait_until="domcontentloaded")
    # 페이지 로드 후 나타날 수 있는 팝업 처리
    try:
        close_button = page.locator(".ui-dialog-titlebar-close")
        await close_button.wait_for(state="visible", timeout=WAIT_FOR_POPUP_TIMEOUT)
        await close_button.click()
        print("[INFO] 팝업을 닫았습니다.")
    except PlaywrightTimeoutError:
        print("[INFO] 팝업이 나타나지 않았습니다. 계속 진행합니다.")
    await page.wait_for_load_state("networkidle")

# =====================
# 🧭 조회 폼 채우기 & 제출
# =====================
async def fill_search_form(page: Page, p: SearchParams):
    """
    조회 폼을 채웁니다. 역 입력 시 자동 완성 목록을 클릭하여 안정성을 높입니다.
    """
    print("[INFO] 조회 폼 입력을 시작합니다...")

    # --- 출발역 ---
    depart_input = page.locator(SELECTORS["input_depart"])
    await depart_input.fill(p.depart_station)
    print(f"[INFO] 출발역 '{p.depart_station}' 입력 완료.")

    # --- 도착역 ---
    arrive_input = page.locator(SELECTORS["input_arrive"])
    await arrive_input.fill(p.arrive_station)
    print(f"[INFO] 도착역 '{p.arrive_station}' 입력 완료.")

    # --- 날짜 ---
    date_label = format_date_for_srt(p.date_str)
    await page.locator(SELECTORS["input_date"]).select_option(label=date_label)
    print(f"[INFO] 날짜 '{date_label}' 선택 완료.")

    # --- 시간 ---
    if p.time_start and await page.locator(SELECTORS["select_time"]).count():
        # 입력된 시간(예: "17:00")에서 시간(hour) 부분만 정수로 추출합니다.
        hour = int(p.time_start.split(":")[0])
        
        # SRT 시간 선택기는 2시간 단위(0, 2, 4...)이므로,
        # 입력된 시간보다 작거나 같은 가장 가까운 짝수를 찾습니다.
        selected_hour = hour - (hour % 2)
        
        # SRT 웹사이트 <option>의 value 형식("HH0000")에 맞게 변환합니다.
        hour_value_str = str(selected_hour).zfill(2)
        value_to_select = f"{hour_value_str}0000"
        
        await page.locator(SELECTORS["select_time"]).select_option(value=value_to_select)
        print(f"[INFO] 출발 시각을 '{hour_value_str}:00'으로 선택 완료.")


async def submit_inquiry(page: Page):
    """조회하기 버튼을 클릭하고 결과가 로드될 때까지 기다립니다."""
    # Playwright는 .click() 후의 네트워크 활동을 자동으로 대기할 수 있지만,
    # 명시적으로 로딩을 기다리는 것이 좋습니다.
    print("[INFO] '조회하기' 버튼을 클릭합니다.")
    await page.locator(SELECTORS["btn_inquiry"]).click()
    # 다음 시도를 위해 결과 로딩 후 잠시 대기
    await page.wait_for_timeout(500) 
    print("[INFO] 조회 요청 완료.")

# =====================
# 🎯 결과 필터링 & 예약 클릭
# =====================
async def filter_and_reserve(page: Page, p: SearchParams) -> bool:
    """
    조건에 맞는 예약 가능한 좌석을 필터링하고 예약을 시도합니다.
    """
    rows = page.locator(SELECTORS["result_rows"])
    n = await rows.count()
    if n == 0:
        print("[WARN] 검색 결과 행이 없습니다.")
        return False

    print(f"[INFO] {n}개의 운행 정보를 찾았습니다. 예약 가능한 좌석을 탐색합니다.")

    min_start = hhmm_to_min(p.time_start) if p.time_start else -1
    min_end = hhmm_to_min(p.time_end) if p.time_end else 1441 # 24 * 60 + 1

    # 1. 클릭할 후보 버튼들을 먼저 모두 찾습니다.
    candidates = []
    for i in range(n):
        row = rows.nth(i)
        
        # 출발 시간 확인을 위한 로케이터 생성
        dpt_cell_loc = row.locator(SELECTORS["col_depart_time"]).first
        # is_visible()을 사용하여 행이 유효한지 먼저 확인
        if not await dpt_cell_loc.is_visible():
            continue

        dpt_text = await get_text_safe(dpt_cell_loc)
        if not dpt_text:
            continue

        dpt_min = hhmm_to_min(dpt_text)

        # 시간 필터링
        if not (min_start <= dpt_min < min_end):
            continue

        # 좌석 우선순위에 따라 예약 가능한 버튼을 후보 리스트에 추가
        for seat_type in p.seat_priority:
            button_selector = ""
            if seat_type == "특실":
                button_selector = SELECTORS["reserve_button_special"]
            elif seat_type == "일반실":
                button_selector = SELECTORS["reserve_button_general"]

            if button_selector:
                reserve_button = row.locator(button_selector).first
                # is_visible()을 사용하여 버튼이 실제로 '예약하기' 상태인지 확인
                if await reserve_button.is_visible():
                    candidates.append({
                        "button": reserve_button,
                        "time": dpt_text,
                        "seat": seat_type
                    })
                    # 우선순위에 맞는 좌석이 발견되면 다음 좌석 타입은 건너뛰고 다음 행으로 넘어감
                    break 

    if not candidates:
        print("[FAIL] 조건에 맞는 예약 가능한 좌석을 찾지 못했습니다.")
        return False

    print(f"[INFO] {len(candidates)}개의 예약 가능한 좌석을 찾았습니다. 순서대로 예약을 시도합니다.")

    # 2. 찾은 후보 버튼들을 순서대로 클릭 시도
    for candidate in candidates:
        try:
            print(f"[INFO] {RESERVATION_DELAY_MS / 1000:.0f}초 후 ({candidate['time']} 출발, {candidate['seat']}) 예약을 시도합니다...")
            # 예약 클릭 전 딜레이
            await page.wait_for_timeout(RESERVATION_DELAY_MS)
            
            # 페이지가 이동하거나 새로운 팝업이 열릴 것을 기대합니다.
            # expect_event('popup') 또는 expect_navigation()을 사용할 수 있지만,
            # Playwright의 자동 대기 기능을 신뢰하고 단순 click()만 사용합니다.
            print("button:", candidate["button"])
            await candidate["button"].click()
            
            # 클릭 성공 후, URL이 바뀌거나 다음 단계로 넘어갔는지 확인하는 로직 추가 가능
            # 여기서는 클릭 성공 시 루프를 종료하는 것으로 만족합니다.
            print(f"[SUCCESS] 예약 버튼 클릭 성공! ({candidate['time']} 출발, {candidate['seat']})")
            return True
        except Exception as e:
            # 예기치 않은 오류가 발생해도 다음 후보를 시도할 수 있도록 처리
            print(f"[WARN] 버튼 클릭 실패 ({candidate['time']} 출발, {candidate['seat']}): {e}")
            continue 

    print("[FAIL] 모든 예약 가능한 좌석의 클릭에 실패했습니다.")
    return False

# =====================
# ▶ main: 실행 흐름
# =====================
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS,
            slow_mo=SLOW_MO,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context_kw = {}
        context = await browser.new_context(**context_kw)
        page = await context.new_page()

        try:
            # parameter 설정
            params = SearchParams(
                srt_phone="01073745718",
                srt_password="dkskdlrj789*",
                depart_station="수서",
                arrive_station="동대구",
                date_str="20251030", # 'YYYYMMDD' 형식으로 변경 필요
                time_start="12:00",
                time_end="20:00",
                seat_priority=["일반실"], # ["일반실", "특실"] 또는 ["특실"] 등으로 설정
            )
            
            # 1) 로그인 세션 확보 (자동 로그인 시도)
            await ensure_logged_in(context, page, params)

            # 2) 조회 페이지 이동
            await goto_search(page)            

            # 3) 폼 입력 (1회만 수행)
            await fill_search_form(page, params)

            success = False
            # 4) 조회 및 결과 확인 (성공할 때까지 최대 횟수만큼 재시도)
            for i in range(MAX_RETRIES):
                print(f"\n[INFO] 조회 시도 ({i + 1}/{MAX_RETRIES})...")
                # 5-1) 조회 버튼 클릭
                await submit_inquiry(page)

                try:
                    # 5-2) 결과 테이블이 나타날 때까지 대기
                    await page.wait_for_selector(SELECTORS["result_rows"], timeout=10_000)
                    print("[INFO] 조회 결과 로딩 완료. 좌석 확인 중...")

                    # 5-3) 결과 필터링 및 예약 시도
                    success = await filter_and_reserve(page, params)
                    if success:
                        break  # 예약 성공 시 재시도 루프 탈출
                except PlaywrightTimeoutError:
                    print("[WARN] 결과 테이블 로딩 시간 초과. 재시도합니다.")
                    await page.wait_for_timeout(RETRY_DELAY_MS)
                except Exception as e:
                    # 예약 버튼 클릭 후 페이지가 넘어가서 발생하는 일반적인 오류 (예약 성공으로 간주)
                    if "Login Failed" not in str(e):
                        print(f"[INFO] 예약 버튼 클릭 후 페이지 이동 감지. 성공으로 간주합니다.")
                        success = True
                        break
                    else:
                        raise e # 로그인 실패는 치명적이므로 다시 던짐
            
            if success:
                print("\n[알림] 예약 버튼 클릭에 성공했습니다. 브라우저에서 좌석 선택 및 결제를 진행하세요.")
            else:
                print(f"\n[알림] {MAX_RETRIES}번 시도했지만 조건에 맞는 좌석을 찾지 못했습니다. 프로그램을 종료합니다.")

            # 6) 창 유지 옵션
            if KEEP_BROWSER_OPEN and success:
                print(f"[INFO] 창 유지 모드: {KEEP_OPEN_MS/1000:.0f}초 동안 브라우저를 유지합니다.")
                await page.wait_for_timeout(KEEP_OPEN_MS)

        except PlaywrightTimeoutError as e:
            print(f"\n[ERROR] Playwright 시간 초과 오류: {e}")
        except Exception as e:
            print(f"\n[ERROR] 예상치 못한 오류가 발생했습니다: {e}")
        finally:
            print("[INFO] 브라우저를 닫습니다.")
            await context.close()
            await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] 사용자 요청으로 프로그램을 종료합니다.")
    except Exception as e:
        print(f"[CRITICAL ERROR] 프로그램 실행 중 치명적인 오류 발생: {e}")
