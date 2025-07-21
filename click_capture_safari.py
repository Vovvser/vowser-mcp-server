import asyncio
from playwright.async_api import async_playwright

async def capture_click_safari(url):
    """WebKit(Safari) 브라우저를 사용하는 안정적인 버전"""
    async with async_playwright() as p:
        print("WebKit(Safari) 브라우저를 시작합니다...")
        
        # WebKit 브라우저 사용
        browser = await p.webkit.launch(headless=False)
        
        try:
            page = await browser.new_page()
            
            # 실제 웹사이트로 이동
            print(f"페이지 로딩 중: {url}")
            await page.goto(url)
            await page.wait_for_load_state('networkidle', timeout=30000)
            
            print("\n✅ 페이지가 로드되었습니다!")
            print("클릭 가능한 요소(버튼, 링크 등)를 클릭하세요...\n")
            
            # 클릭 대기 및 감지 (클릭 가능한 요소만)
            clicked_info = await page.evaluate("""
                new Promise((resolve) => {
                    // 클릭 가능한 요소인지 확인하는 함수
                    function isClickable(element) {
                        const tag = element.tagName.toLowerCase();
                        
                        // 기본적으로 클릭 가능한 태그들
                        const clickableTags = ['a', 'button', 'input', 'select', 'textarea', 'label'];
                        if (clickableTags.includes(tag)) return true;
                        
                        // input 타입 확인
                        if (tag === 'input') {
                            const type = element.type;
                            const clickableTypes = ['button', 'submit', 'reset', 'checkbox', 'radio', 'file'];
                            if (clickableTypes.includes(type)) return true;
                        }
                        
                        // onclick 이벤트가 있는지 확인
                        if (element.onclick || element.getAttribute('onclick')) return true;
                        
                        // cursor가 pointer인지 확인
                        const computedStyle = window.getComputedStyle(element);
                        if (computedStyle.cursor === 'pointer') return true;
                        
                        // role이 button이나 link인지 확인
                        const role = element.getAttribute('role');
                        if (role === 'button' || role === 'link') return true;
                        
                        // data-* 속성으로 클릭 가능 표시
                        if (element.hasAttribute('data-clickable') || 
                            element.hasAttribute('data-href') ||
                            element.hasAttribute('data-action')) return true;
                        
                        return false;
                    }
                    
                    // 요소의 CSS 선택자 경로 생성
                    function getElementPath(element) {
                        const path = [];
                        let current = element;
                        
                        while (current && current !== document.body && path.length < 5) {
                            let selector = current.tagName.toLowerCase();
                            
                            if (current.id) {
                                selector += '#' + current.id;
                                path.unshift(selector);
                                break;  // ID가 있으면 여기서 끝
                            }
                            
                            if (current.className) {
                                const classes = current.className.split(' ').filter(c => c.trim());
                                if (classes.length > 0) {
                                    selector += '.' + classes.slice(0, 2).join('.');
                                }
                            }
                            
                            path.unshift(selector);
                            current = current.parentElement;
                        }
                        
                        return path.join(' > ');
                    }
                    
                    document.addEventListener('click', function(e) {
                        const element = e.target;
                        
                        // 클릭 가능한 요소인지 확인
                        if (isClickable(element)) {
                            // 기본 동작 방지 (페이지 이동 등)
                            e.preventDefault();
                            e.stopPropagation();
                            
                            // 시각적 피드백
                            element.style.outline = '3px solid #ff0000';
                            element.style.outlineOffset = '2px';
                            element.style.backgroundColor = 'rgba(255, 0, 0, 0.2)';
                            
                            // 요소 정보 수집
                            const info = {
                                tagName: element.tagName,
                                id: element.id || null,
                                className: element.className || null,
                                text: element.innerText || element.textContent || element.value || '',
                                href: element.href || null,
                                onclick: element.onclick ? 'true' : 'false',
                                role: element.getAttribute('role') || null,
                                type: element.type || null,
                                name: element.name || null,
                                value: element.value || null,
                                outerHTML: element.outerHTML,
                                cssSelector: getElementPath(element),
                                cursor: window.getComputedStyle(element).cursor,
                                position: element.getBoundingClientRect(),
                                timestamp: new Date().toISOString()
                            };
                            
                            console.log('클릭한 요소:', info);
                            setTimeout(() => resolve(info), 500);
                        }
                    }, true);
                    
                    console.log('클릭 감지 준비 완료! 클릭 가능한 요소를 찾아서 클릭하세요.');
                })
            """)
            
            # 브라우저 종료
            await browser.close()
            
            # 결과 출력
            print("\n" + "="*70)
            print("🎯 클릭한 요소 정보")
            print("="*70)
            
            print(f"\n📌 기본 정보:")
            print(f"  • 태그: <{clicked_info['tagName'].lower()}>")
            print(f"  • ID: {clicked_info['id'] or '없음'}")
            print(f"  • 클래스: {clicked_info['className'] or '없음'}")
            print(f"  • 텍스트: {clicked_info['text'] or '없음'}")
            
            if clicked_info['href']:
                print(f"  • 링크: {clicked_info['href']}")
            if clicked_info['type']:
                print(f"  • 타입: {clicked_info['type']}")
            if clicked_info['role']:
                print(f"  • 역할: {clicked_info['role']}")
            if clicked_info['name']:
                print(f"  • 이름: {clicked_info['name']}")
            if clicked_info['value']:
                print(f"  • 값: {clicked_info['value']}")
            if clicked_info['onclick'] == 'true':
                print(f"  • onclick 이벤트: 있음")
                
            print(f"  • 커서 스타일: {clicked_info['cursor']}")
            print(f"  • 클릭 시간: {clicked_info['timestamp']}")
            
            print(f"\n📍 위치 정보:")
            pos = clicked_info['position']
            print(f"  • X: {pos['x']:.1f}, Y: {pos['y']:.1f}")
            print(f"  • 너비: {pos['width']:.1f}, 높이: {pos['height']:.1f}")
            
            print(f"\n🔍 CSS 선택자:")
            print(f"  {clicked_info['cssSelector']}")
            
            print(f"\n📝 HTML:")
            print(f"  {clicked_info['outerHTML']}")
            
            return clicked_info
            
        except Exception as e:
            print(f"오류 발생: {e}")
            await browser.close()

if __name__ == "__main__":
    # 테스트할 URL (여기서 직접 수정하세요)
    url = "https://naver.com"
    
    print("🚀 WebKit(Safari) 클릭 캡처를 시작합니다...")
    print(f"접속 URL: {url}")
    print("클릭 감지를 시작합니다...\n")
    
    asyncio.run(capture_click_safari(url))