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
- 1회 로그인 후 storage_state.json으로 세션을 저장/재사용
- 조회 폼(출발/도착/날짜/시간) 입력 → 조회하기 → 결과 필터링 → '예약하기' 클릭
- 창 유지 옵션(KEEP_BROWSER_OPEN), slow_mo 지원
- iframe/동적 로딩 대비 기본 대기 포함

※ 캡차/2단계 인증은 수동 처리 필요
"""

# ---- 설정값 ----------------------------------------------------
SRT_HOME = "https://etk.srail.kr/"           # SRT 홈 (필요 시 변경)
SEARCH_URL = "https://etk.srail.kr/hpg/hra/01/selectScheduleList.do"  # 조회 페이지
STORAGE = "storage_state.json"               # 로그인 세션 저장 파일
HEADLESS = False                              # True면 창 없이 실행
SLOW_MO = 150                                 # 동작을 천천히 보기 위한 슬로 모션(ms)
KEEP_BROWSER_OPEN = True                      # 실행 후 창 유지 여부
KEEP_OPEN_MS = 3_600_000                      # 1시간 유지 (원하면 변경)
CHECK_INTERVAL_MS = 500                       # 버튼 감시 간격(ms)
WAIT_ACTIVE_TIMEOUT = 120_000                 # 활성화 대기 최대시간(ms) = 2분
CLICK_RETRY = 3                               # 클릭 재시도

# 선택자 후보들 (활성화된 '예매' 버튼을 넓게 커버)
RESERVE_SELECTORS = [
    # 1) 버튼/링크 텍스트가 '예매'인 경우
    "button:has-text('예매'):not([disabled])",
    "a:has-text('예매'):not([aria-disabled='true']):not([disabled])",
    # 2) ARIA 롤 버튼/링크
    "[role='button']:has-text('예매'):not([aria-disabled='true'])",
    # 3) 버튼 내부 텍스트 공백/대소문자 변형 대응
    "button:has(:text-matches('^\\s*예\\s*매\\s*$', 'i')):not([disabled])",
    "a:has(:text-matches('^\\s*예\\s*매\\s*$', 'i')):not([aria-disabled='true'])",
]

# =====================
# ✅ 사용자 파라미터
# =====================
class SearchParams:
    def __init__(
        self,
        depart_station: str,    # 예: "수서"
        arrive_station: str,    # 예: "부산"
        date_str: str,          # "YYYY-MM-DD"
        time_start: Optional[str] = None,  # "HH:MM" (포함)
        time_end: Optional[str] = None,    # "HH:MM" (포함)
        seat_priority: Optional[List[str]] = None  # 예: ["일반실", "특실"]
    ):
        self.depart_station = depart_station
        self.arrive_station = arrive_station
        self.date_str = date_str
        self.time_start = time_start
        self.time_end = time_end
        self.seat_priority = seat_priority or ["일반실", "특실"]

# =====================
# 🔧 사이트 셀렉터 설정 (필요 시 수정)
# =====================
SELECTORS = {
    # 조회 폼
    "select_depart": "#dptRsStnCdNm",          # 출발역 <select>
    "select_arrive": "#arvRsStnCdNm",          # 도착역 <select>
    "input_date": "#dptDt",                  # 날짜 <input type=date or text>
    "select_time": "#dptTm",                 # 시간 <select> (없으면 생략)
    "btn_inquiry": "input.inquery_btn[type='submit'], button.inquery_btn",  # 조회하기 버튼

    # 결과 테이블/행/열 (사이트 HTML에 맞게 조정)
    "result_rows": "table tbody tr",         # 결과 행
    "col_depart_time": ".dptTime, td:nth-child(4)",  # 출발시간 셀
    "col_arrive_time": ".arvTime, td:nth-child(5)",  # (옵션) 도착시간 셀
    "col_seat_text": "td",                          # (옵션) 좌석 정보 텍스트 위치
    # 예약 버튼 (각 행 내부에서 찾음)
    "reserve_button": "a.btn_burgundy_dark:has-text('예약하기')",
}

# =====================
# ⏱️ 유틸
# =====================

def hhmm_to_min(hhmm: str) -> int:
    v = hhmm.strip()
    if ":" not in v:
        # 930 → 09:30 허용
        if len(v) in (3, 4):
            v = v.zfill(4)
            v = f"{v[:-2]}:{v[-2:]}"
    t = datetime.strptime(v, "%H:%M")
    return t.hour * 60 + t.minute

async def get_text_safe(loc: Locator) -> str:
    try:
        s = (await loc.first.text_content()) or ""
        return " ".join(s.split())
    except Exception:
        return ""

# iframe 안에 있을 가능성도 고려 ⇒ 프레임 전역 탐색
def build_query_js():
    joined = " || ".join([
        f"(Array.from(document.querySelectorAll(`{sel}`)).filter(el => el.offsetParent !== null && getComputedStyle(el).visibility !== 'hidden').length > 0)"
        for sel in RESERVE_SELECTORS
    ])
    return f"() => {{ try {{ return ({joined}); }} catch (e) {{ return false; }} }}"

def build_query_js_return_nodes():
    parts = []
    for sel in RESERVE_SELECTORS:
        parts.append(
            f"""Array.from(document.querySelectorAll(`{sel}`))
                .filter(el => el && el.offsetParent !== null && getComputedStyle(el).visibility !== 'hidden')"""
        )
    return ("() => {\n"
            "  try {\n"
            "    const lists = [\n" + ",\n".join(parts) + "\n" +
            "    ];\n"
            "    return lists.flat();\n"
            "  } catch (e) { return []; }\n"
            "}")

# =====================
# 🔐 로그인 & 페이지 이동
# =====================
async def ensure_logged_in(context, page: Page):
    """storage_state.json이 없으면 로그인 페이지로 보내 수동 로그인 유도 → 저장"""
    if Path(STORAGE).exists():
        return  # 이미 저장된 세션 사용

    print("[INFO] 처음 실행: SRT 로그인 후 창을 닫지 말고, 상단 메뉴가 보이면 콘솔에 Enter를 누르세요.")
    await page.goto(SRT_HOME, wait_until="domcontentloaded")
    input("로그인이 완료되면 Enter 키를 눌러주세요... ")
    await context.storage_state(path=STORAGE)
    print("[INFO] 로그인 세션 저장 완료:", STORAGE)

async def goto_search(page: Page):
    """시간표 조회 페이지로 이동"""
    await page.goto(SEARCH_URL, wait_until="domcontentloaded")
    await page.wait_for_load_state("networkidle")

# =====================
# 🧭 조회 폼 채우기 & 제출
# =====================
# ✅ 수정된 fill_search_form(): 출발/도착 도시가 input 필드일 때

async def fill_search_form(page: Page, p: SearchParams):
    # 출발/도착역이 select가 아니라 input일 때는 select_option 대신 fill() 사용
    if await page.locator(SELECTORS["select_depart"]).count():
        await page.locator(SELECTORS["select_depart"]).fill(p.depart_station)
        # 자동완성 제안이 있을 경우 Enter 키 입력으로 확정
        await page.keyboard.press("Enter")

    if await page.locator(SELECTORS["select_arrive"]).count():
        await page.locator(SELECTORS["select_arrive"]).fill(p.arrive_station)
        await page.keyboard.press("Enter")

    # 날짜 입력 (type=date 또는 text)
    try:
        await page.wait_for_selector(SELECTORS["input_date"], timeout=5000)
        await page.select_option(SELECTORS["input_date"], label=p.date_str)
        print(f"[INFO] 날짜 '{p.date_str}' 선택 완료 (label 기준)")
    except Exception:
    # 일부 사이트는 label이 아닌 value 속성으로만 일치할 수 있음
        try:
            await page.select_option(SELECTORS["input_date"], value=p.date_str)
            print(f"[INFO] 날짜 '{p.date_str}' 선택 완료 (value 기준)")
        except Exception as e:
            print(f"[ERROR] 날짜 선택 실패: {e}")

    # 시간 select가 있으면 시작 시간을 기준으로 맞춤(없으면 생략)
    if p.time_start and await page.locator(SELECTORS["select_time"]).count():
        hour = p.time_start.split(":")[0]
        try:
            await page.locator(SELECTORS["select_time"]).select_option(label=hour)
        except Exception:
            await page.locator(SELECTORS["select_time"]).select_option(value=hour)

async def submit_inquiry(page: Page):
    await page.wait_for_selector(SELECTORS["btn_inquiry"], timeout=10_000)
    await page.click(SELECTORS["btn_inquiry"])
    #await page.wait_for_load_state("networkidle")

# =====================
# 🎯 결과 필터링 & 예약 클릭
# =====================
async def filter_and_reserve(page: Page, p: SearchParams) -> bool:
    """
    1) 결과 행 로드 대기
    2) 시간 필터(선택) 적용
    3) 좌석 우선순위대로 예약 버튼 클릭 시도
    """
    await page.wait_for_selector(SELECTORS["result_rows"], timeout=2000)
    rows = page.locator(SELECTORS["result_rows"])
    n = await rows.count()
    if n == 0:
        print("[WARN] 검색 결과가 없습니다.")
        return False

    # 시간 범위 파싱
    min_start = hhmm_to_min(p.time_start) if p.time_start else None
    min_end = hhmm_to_min(p.time_end) if p.time_end else None

    candidates: List[Tuple[int, Locator]] = []

    for i in range(n):
        row = rows.nth(i)
        dpt_cell = row.locator(SELECTORS["col_depart_time"]).first
        dpt_text = await get_text_safe(dpt_cell)
        if not dpt_text:
            continue
        try:
            print("dpt_text:", dpt_text)
            dpt_min = hhmm_to_min(dpt_text)
        except Exception:
            dpt_min = None

        # 시간 필터
        if min_start is not None and dpt_min is not None and dpt_min < min_start:
            continue
        if min_end is not None and dpt_min is not None and dpt_min > min_end:
            continue

        # 좌석/버튼 찾기 — 기본은 단일 "예약하기" 버튼
        btn = row.locator(SELECTORS["reserve_button"]).first
        if await btn.count():
            candidates.append((i, btn))
            continue

        # (옵션) 좌석별 버튼이 따로 있는 경우 — 필요 시 커스터마이즈
        # for seat in p.seat_priority:
        #     seat_btn = row.locator(f"a:has-text('{seat}')").first
        #     if await seat_btn.count():
        #         candidates.append((i, seat_btn))
        #         break

    if not candidates:
        print("[WARN] 조건에 맞는 예약 버튼을 찾지 못했습니다.")
        return False

    # 첫 후보부터 클릭
    for idx, btn in candidates:
        try:
            await btn.scroll_into_view_if_needed()
            await btn.click()
            print(f"[INFO] 예약 버튼 클릭 성공 (row={idx})")
            return True
        except Exception as e:
            print(f"[WARN] 예약 클릭 실패(row={idx}): {e}")
            continue

    print("[ERROR] 모든 후보 클릭 실패")
    return False

# =====================
# (옵션) 단순 감시 클릭: '예약하기' 텍스트만 보고 즉시 클릭
# =====================
async def wait_and_click_reserve(page: Page) -> bool:
    try:
        await page.wait_for_selector(
            "a.btn_burgundy_dark:has-text('예약하기')",
            timeout=30_000,
        )
        buttons = await page.query_selector_all(
            "a.btn_burgundy_dark:has-text('예약하기')"
        )
        if not buttons:
            print("[WARN] 예약하기 버튼을 찾지 못했습니다.")
            return False
        for idx, btn in enumerate(buttons):
            try:
                await btn.scroll_into_view_if_needed()
                await btn.click()
                print(f"[INFO] 예약하기 버튼 클릭 성공 (index={idx})")
                return True
            except Exception as e:
                print(f"[WARN] 예약하기 버튼 클릭 실패 (index={idx}): {e}")
                continue
        print("[ERROR] 모든 예약하기 버튼 클릭 시도 실패.")
        return False
    except Exception as e:
        print(f"[ERROR] 예약하기 버튼을 찾는 중 오류 발생: {e}")
        return False

# =====================
# ▶ 플로우 조립
# =====================
async def run_flow(page: Page, params: SearchParams) -> bool:
    await fill_search_form(page, params)
    await submit_inquiry(page)
    ok = await filter_and_reserve(page, params)
    if ok:
        print("[DONE] 조건에 맞는 예약 버튼 클릭 완료 → 좌석 선택/결제 단계로 이동합니다.")
        return True
    else:
        print("[DONE] 조건에 맞는 결과를 찾지 못했습니다.")
        return False

# =====================
# ▶ main: 올바른 순서로 실행
# =====================
async def main():
    load_dotenv()
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS,
            slow_mo=SLOW_MO,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context_kw = {}
        if Path(STORAGE).exists():
            context_kw["storage_state"] = STORAGE
        context = await browser.new_context(**context_kw)
        page = await context.new_page()

        # 1) 로그인 세션 확보
        await ensure_logged_in(context, page)

        # 2) 조회 페이지 이동
        await goto_search(page)

        # 3) 파라미터 설정 (필요 시 외부에서 입력받아 주입)
        params = SearchParams(
            depart_station="수서",
            arrive_station="동대구",
            date_str="20251023",
            time_start="16:00",
            time_end="18:00",
            seat_priority=["일반실", "특실"],
        )

        # 4) 폼 입력 → 조회 → 결과 필터링 → 예약 클릭
        await run_flow(page, params)

        # (옵션) 단순 감시 클릭 방식 사용 시 아래를 대체 호출
        # await wait_and_click_reserve(page)

        # 5) 창 유지 옵션
        if KEEP_BROWSER_OPEN:
            print(f"[INFO] 창 유지 모드: {KEEP_OPEN_MS/1000:.0f}s 동안 창을 유지합니다.")
            try:
                await page.wait_for_timeout(KEEP_OPEN_MS)
            except Exception:
                pass

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
