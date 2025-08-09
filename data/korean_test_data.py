"""
한국 인기 사이트 테스트 데이터
"""

# 네이버 웹툰 테스트 케이스들
NAVER_WEBTOON_CASES = [
    {
        "sessionId": "naver_webtoon_001",
        "startCommand": "네이버 웹툰에서 월요웹툰 외모지상주의 최신화 보기",
        "completePath": [
            {
                "order": 0,
                "url": "https://comic.naver.com",
                "locationData": None,
                "semanticData": None
            },
            {
                "order": 1,
                "url": "https://comic.naver.com",
                "locationData": {
                    "primarySelector": "a.Nbtn_webtoon",
                    "fallbackSelectors": ["a[href*='webtoon']", "nav a:contains('웹툰')"],
                    "anchorPoint": "#header",
                    "relativePathFromAnchor": "a.Nbtn_webtoon",
                    "elementSnapshot": {"tagName": "a", "attributes": {"class": "Nbtn_webtoon"}}
                },
                "semanticData": {
                    "textLabels": ["웹툰", "WEBTOON"],
                    "contextText": {
                        "immediate": "네비게이션",
                        "section": "헤더",
                        "neighbor": ["홈", "웹소설", "베스트도전"]
                    },
                    "pageInfo": {"title": "네이버 웹툰", "url": "https://comic.naver.com"},
                    "actionType": "click"
                }
            },
            {
                "order": 2,
                "url": "https://comic.naver.com/webtoon",
                "locationData": {
                    "primarySelector": "li.day_mon a",
                    "fallbackSelectors": ["li[class*='mon'] a", "a:contains('월요웹툰')"],
                    "anchorPoint": "#weekdayList",
                    "relativePathFromAnchor": "li.day_mon a",
                    "elementSnapshot": {"tagName": "a", "attributes": {"class": "day_link"}}
                },
                "semanticData": {
                    "textLabels": ["월요웹툰", "월"],
                    "contextText": {
                        "immediate": "요일별 웹툰",
                        "section": "웹툰 목록",
                        "neighbor": ["일", "화", "수", "목", "금", "토"]
                    },
                    "pageInfo": {"title": "요일별 웹툰 - 네이버 웹툰", "url": "https://comic.naver.com/webtoon"},
                    "actionType": "click"
                }
            },
            {
                "order": 3,
                "url": "https://comic.naver.com/webtoon/weekday/mon",
                "locationData": {
                    "primarySelector": "div.thumb a[title='외모지상주의']",
                    "fallbackSelectors": ["a[href*='lookism']", "img[alt='외모지상주의']"],
                    "anchorPoint": "#content",
                    "relativePathFromAnchor": "div.thumb a[title='외모지상주의']",
                    "elementSnapshot": {"tagName": "a", "attributes": {"title": "외모지상주의"}}
                },
                "semanticData": {
                    "textLabels": ["외모지상주의", "박태준"],
                    "contextText": {
                        "immediate": "월요웹툰",
                        "section": "웹툰 리스트",
                        "neighbor": ["별점 9.9", "업데이트"]
                    },
                    "pageInfo": {"title": "월요웹툰 - 네이버 웹툰", "url": "https://comic.naver.com/webtoon/weekday/mon"},
                    "actionType": "click"
                }
            }
        ]
    },
    {
        "sessionId": "naver_webtoon_002",
        "startCommand": "네이버 웹툰 로맨스 장르에서 여신강림 관심웹툰 등록",
        "completePath": [
            {
                "order": 0,
                "url": "https://comic.naver.com",
                "locationData": None,
                "semanticData": None
            },
            {
                "order": 1,
                "url": "https://comic.naver.com",
                "locationData": {
                    "primarySelector": "a.genre_tab",
                    "fallbackSelectors": ["a[href*='genre']", "nav a:contains('장르')"],
                    "anchorPoint": "#header",
                    "relativePathFromAnchor": "a.genre_tab",
                    "elementSnapshot": {"tagName": "a", "attributes": {"class": "genre_tab"}}
                },
                "semanticData": {
                    "textLabels": ["장르", "Genre"],
                    "contextText": {
                        "immediate": "네비게이션",
                        "section": "헤더",
                        "neighbor": ["요일", "완결", "웹소설"]
                    },
                    "pageInfo": {"title": "네이버 웹툰", "url": "https://comic.naver.com"},
                    "actionType": "click"
                }
            },
            {
                "order": 2,
                "url": "https://comic.naver.com/genre",
                "locationData": {
                    "primarySelector": "a[data-genre='romance']",
                    "fallbackSelectors": ["a:contains('로맨스')", "div.genre_item a[href*='romance']"],
                    "anchorPoint": "#content",
                    "relativePathFromAnchor": "a[data-genre='romance']",
                    "elementSnapshot": {"tagName": "a", "attributes": {"data-genre": "romance"}}
                },
                "semanticData": {
                    "textLabels": ["로맨스", "Romance"],
                    "contextText": {
                        "immediate": "장르 목록",
                        "section": "장르별 웹툰",
                        "neighbor": ["액션", "판타지", "드라마", "일상"]
                    },
                    "pageInfo": {"title": "장르별 웹툰 - 네이버 웹툰", "url": "https://comic.naver.com/genre"},
                    "actionType": "click"
                }
            },
            {
                "order": 3,
                "url": "https://comic.naver.com/genre/romance",
                "locationData": {
                    "primarySelector": "div.thumb a[title='여신강림']",
                    "fallbackSelectors": ["a[href*='703846']", "img[alt='여신강림']"],
                    "anchorPoint": "#content",
                    "relativePathFromAnchor": "div.thumb a[title='여신강림']",
                    "elementSnapshot": {"tagName": "a", "attributes": {"title": "여신강림"}}
                },
                "semanticData": {
                    "textLabels": ["여신강림", "야옹이"],
                    "contextText": {
                        "immediate": "로맨스 웹툰",
                        "section": "장르 리스트",
                        "neighbor": ["별점 9.8", "매주 화요일"]
                    },
                    "pageInfo": {"title": "로맨스 웹툰 - 네이버 웹툰", "url": "https://comic.naver.com/genre/romance"},
                    "actionType": "click"
                }
            },
            {
                "order": 4,
                "url": "https://comic.naver.com/webtoon/list?titleId=703846",
                "locationData": {
                    "primarySelector": "button.btn_favorite",
                    "fallbackSelectors": ["button[aria-label='관심웹툰']", "span.ico_favorite"],
                    "anchorPoint": "#content",
                    "relativePathFromAnchor": "button.btn_favorite",
                    "elementSnapshot": {"tagName": "button", "attributes": {"class": "btn_favorite"}}
                },
                "semanticData": {
                    "textLabels": ["관심웹툰 등록", "♥ 관심"],
                    "contextText": {
                        "immediate": "웹툰 정보",
                        "section": "웹툰 상세",
                        "neighbor": ["첫화보기", "최신화보기", "공유하기"]
                    },
                    "pageInfo": {"title": "여신강림 - 네이버 웹툰", "url": "https://comic.naver.com/webtoon/list?titleId=703846"},
                    "actionType": "click"
                }
            }
        ]
    }
]

# 쿠팡 쇼핑 테스트 케이스들
COUPANG_CASES = [
    {
        "sessionId": "coupang_001",
        "startCommand": "쿠팡에서 신라면 로켓배송으로 바로구매",
        "completePath": [
            {
                "order": 0,
                "url": "https://www.coupang.com",
                "locationData": None,
                "semanticData": None
            },
            {
                "order": 1,
                "url": "https://www.coupang.com",
                "locationData": {
                    "primarySelector": "a.rocket-delivery",
                    "fallbackSelectors": ["a[href*='rocket']", "nav a:contains('로켓배송')"],
                    "anchorPoint": "#gnbAnalytics",
                    "relativePathFromAnchor": "a.rocket-delivery",
                    "elementSnapshot": {"tagName": "a", "attributes": {"class": "rocket-delivery"}}
                },
                "semanticData": {
                    "textLabels": ["로켓배송", "Rocket Delivery"],
                    "contextText": {
                        "immediate": "메인 네비게이션",
                        "section": "헤더",
                        "neighbor": ["로켓프레시", "골드박스", "와우회원"]
                    },
                    "pageInfo": {"title": "쿠팡!", "url": "https://www.coupang.com"},
                    "actionType": "click"
                }
            },
            {
                "order": 2,
                "url": "https://www.coupang.com/np/campaigns/82",
                "locationData": {
                    "primarySelector": "a[data-category='food']",
                    "fallbackSelectors": ["a:contains('식품')", "li.category-food a"],
                    "anchorPoint": "#searchCategoryComponent",
                    "relativePathFromAnchor": "a[data-category='food']",
                    "elementSnapshot": {"tagName": "a", "attributes": {"data-category": "food"}}
                },
                "semanticData": {
                    "textLabels": ["식품", "Food"],
                    "contextText": {
                        "immediate": "카테고리",
                        "section": "로켓배송 카테고리",
                        "neighbor": ["패션", "뷰티", "가전", "생활용품"]
                    },
                    "pageInfo": {"title": "로켓배송 - 쿠팡!", "url": "https://www.coupang.com/np/campaigns/82"},
                    "actionType": "click"
                }
            },
            {
                "order": 3,
                "url": "https://www.coupang.com/np/categories/194276",
                "locationData": {
                    "primarySelector": "input#headerSearchKeyword",
                    "fallbackSelectors": ["input[name='q']", "input.search-input"],
                    "anchorPoint": "#headerSearchForm",
                    "relativePathFromAnchor": "input#headerSearchKeyword",
                    "elementSnapshot": {"tagName": "input", "attributes": {"id": "headerSearchKeyword"}}
                },
                "semanticData": {
                    "textLabels": ["검색", "신라면"],
                    "contextText": {
                        "immediate": "검색창",
                        "section": "헤더",
                        "neighbor": ["검색버튼", "장바구니", "마이쿠팡"]
                    },
                    "pageInfo": {"title": "식품 - 쿠팡!", "url": "https://www.coupang.com/np/categories/194276"},
                    "actionType": "type"
                }
            },
            {
                "order": 4,
                "url": "https://www.coupang.com/vp/products/6184421598",
                "locationData": {
                    "primarySelector": "button.buy-now",
                    "fallbackSelectors": ["button[class*='buy']", "button:contains('바로구매')"],
                    "anchorPoint": "#btfTab",
                    "relativePathFromAnchor": "button.buy-now",
                    "elementSnapshot": {"tagName": "button", "attributes": {"class": "buy-now"}}
                },
                "semanticData": {
                    "textLabels": ["바로구매", "Buy Now"],
                    "contextText": {
                        "immediate": "구매 옵션",
                        "section": "상품 상세",
                        "neighbor": ["장바구니 담기", "찜하기", "수량"]
                    },
                    "pageInfo": {"title": "농심 신라면 20개입 - 쿠팡!", "url": "https://www.coupang.com/vp/products/6184421598"},
                    "actionType": "click"
                }
            }
        ]
    },
    {
        "sessionId": "coupang_002",
        "startCommand": "쿠팡 골드박스 타임특가에서 갤럭시버즈 즉시구매",
        "completePath": [
            {
                "order": 0,
                "url": "https://www.coupang.com",
                "locationData": None,
                "semanticData": None
            },
            {
                "order": 1,
                "url": "https://www.coupang.com",
                "locationData": {
                    "primarySelector": "a.goldbox-link",
                    "fallbackSelectors": ["a[href*='goldbox']", "nav a:contains('골드박스')"],
                    "anchorPoint": "#gnb",
                    "relativePathFromAnchor": "a.goldbox-link",
                    "elementSnapshot": {"tagName": "a", "attributes": {"class": "goldbox-link"}}
                },
                "semanticData": {
                    "textLabels": ["골드박스", "Gold Box"],
                    "contextText": {
                        "immediate": "특가 메뉴",
                        "section": "헤더",
                        "neighbor": ["로켓배송", "로켓프레시", "베스트"]
                    },
                    "pageInfo": {"title": "쿠팡!", "url": "https://www.coupang.com"},
                    "actionType": "click"
                }
            },
            {
                "order": 2,
                "url": "https://www.coupang.com/np/goldbox",
                "locationData": {
                    "primarySelector": "div.time-deal-tab",
                    "fallbackSelectors": ["a:contains('타임특가')", "button.time-deal"],
                    "anchorPoint": "#goldbox-tabs",
                    "relativePathFromAnchor": "div.time-deal-tab",
                    "elementSnapshot": {"tagName": "div", "attributes": {"class": "time-deal-tab"}}
                },
                "semanticData": {
                    "textLabels": ["타임특가", "Time Deal"],
                    "contextText": {
                        "immediate": "딜 종류",
                        "section": "골드박스",
                        "neighbor": ["오늘의 딜", "일일특가", "위클리특가"]
                    },
                    "pageInfo": {"title": "골드박스 - 쿠팡!", "url": "https://www.coupang.com/np/goldbox"},
                    "actionType": "click"
                }
            },
            {
                "order": 3,
                "url": "https://www.coupang.com/vp/products/7145896127",
                "locationData": {
                    "primarySelector": "button.buy-immediately",
                    "fallbackSelectors": ["button[class*='immediate']", "button:contains('즉시구매')"],
                    "anchorPoint": "#btfTab",
                    "relativePathFromAnchor": "button.buy-immediately",
                    "elementSnapshot": {"tagName": "button", "attributes": {"class": "buy-immediately"}}
                },
                "semanticData": {
                    "textLabels": ["즉시구매", "Buy Immediately"],
                    "contextText": {
                        "immediate": "타임특가",
                        "section": "상품 상세",
                        "neighbor": ["남은시간", "할인율", "한정수량"]
                    },
                    "pageInfo": {"title": "삼성 갤럭시버즈2 프로 - 쿠팡!", "url": "https://www.coupang.com/vp/products/7145896127"},
                    "actionType": "click"
                }
            }
        ]
    }
]

# 나무위키 테스트 케이스들
NAMUWIKI_CASES = [
    {
        "sessionId": "namuwiki_001",
        "startCommand": "나무위키에서 이순신 검색 후 임진왜란 문서로 이동",
        "completePath": [
            {
                "order": 0,
                "url": "https://namu.wiki",
                "locationData": None,
                "semanticData": None
            },
            {
                "order": 1,
                "url": "https://namu.wiki",
                "locationData": {
                    "primarySelector": "input.search-input",
                    "fallbackSelectors": ["input[name='q']", "input[placeholder*='검색']"],
                    "anchorPoint": "#app",
                    "relativePathFromAnchor": "input.search-input",
                    "elementSnapshot": {"tagName": "input", "attributes": {"class": "search-input"}}
                },
                "semanticData": {
                    "textLabels": ["검색", "이순신"],
                    "contextText": {
                        "immediate": "검색창",
                        "section": "헤더",
                        "neighbor": ["나무위키", "최근변경", "랜덤"]
                    },
                    "pageInfo": {"title": "나무위키", "url": "https://namu.wiki"},
                    "actionType": "type"
                }
            },
            {
                "order": 2,
                "url": "https://namu.wiki/search?q=이순신",
                "locationData": {
                    "primarySelector": "div.search-result a[href*='이순신']",
                    "fallbackSelectors": ["a:contains('이순신')", "h2 a[href*='w/이순신']"],
                    "anchorPoint": "#content",
                    "relativePathFromAnchor": "div.search-result a",
                    "elementSnapshot": {"tagName": "a", "attributes": {"href": "/w/이순신"}}
                },
                "semanticData": {
                    "textLabels": ["이순신", "李舜臣"],
                    "contextText": {
                        "immediate": "검색 결과",
                        "section": "문서 목록",
                        "neighbor": ["조선 장군", "충무공", "임진왜란"]
                    },
                    "pageInfo": {"title": "검색 결과 - 나무위키", "url": "https://namu.wiki/search?q=이순신"},
                    "actionType": "click"
                }
            },
            {
                "order": 3,
                "url": "https://namu.wiki/w/이순신",
                "locationData": {
                    "primarySelector": "div.toc a[href='#s-2']",
                    "fallbackSelectors": ["a:contains('생애')", "div.wiki-heading-content a[href='#s-2']"],
                    "anchorPoint": "#toc",
                    "relativePathFromAnchor": "a[href='#s-2']",
                    "elementSnapshot": {"tagName": "a", "attributes": {"href": "#s-2"}}
                },
                "semanticData": {
                    "textLabels": ["2. 생애", "Life"],
                    "contextText": {
                        "immediate": "목차",
                        "section": "문서 목차",
                        "neighbor": ["1. 개요", "3. 업적", "4. 평가"]
                    },
                    "pageInfo": {"title": "이순신 - 나무위키", "url": "https://namu.wiki/w/이순신"},
                    "actionType": "click"
                }
            },
            {
                "order": 4,
                "url": "https://namu.wiki/w/이순신#s-2",
                "locationData": {
                    "primarySelector": "a.wiki-link[href*='임진왜란']",
                    "fallbackSelectors": ["a:contains('임진왜란')", "span.wiki-link a[href*='임진왜란']"],
                    "anchorPoint": "#s-2",
                    "relativePathFromAnchor": "a.wiki-link[href*='임진왜란']",
                    "elementSnapshot": {"tagName": "a", "attributes": {"class": "wiki-link"}}
                },
                "semanticData": {
                    "textLabels": ["임진왜란", "壬辰倭亂"],
                    "contextText": {
                        "immediate": "생애 내용",
                        "section": "본문",
                        "neighbor": ["1592년", "왜군", "조선 수군"]
                    },
                    "pageInfo": {"title": "이순신 - 나무위키", "url": "https://namu.wiki/w/이순신#s-2"},
                    "actionType": "click"
                }
            }
        ]
    }
]

# 네이버 통합검색 테스트 케이스들
NAVER_CASES = [
    {
        "sessionId": "naver_001",
        "startCommand": "네이버에서 손흥민 뉴스 검색 후 스포츠 섹션 이동",
        "completePath": [
            {
                "order": 0,
                "url": "https://www.naver.com",
                "locationData": None,
                "semanticData": None
            },
            {
                "order": 1,
                "url": "https://www.naver.com",
                "locationData": {
                    "primarySelector": "input#query",
                    "fallbackSelectors": ["input[name='query']", "input.input_text"],
                    "anchorPoint": "#header",
                    "relativePathFromAnchor": "input#query",
                    "elementSnapshot": {"tagName": "input", "attributes": {"id": "query"}}
                },
                "semanticData": {
                    "textLabels": ["검색", "손흥민"],
                    "contextText": {
                        "immediate": "통합검색",
                        "section": "헤더",
                        "neighbor": ["네이버", "검색버튼"]
                    },
                    "pageInfo": {"title": "네이버", "url": "https://www.naver.com"},
                    "actionType": "type"
                }
            },
            {
                "order": 2,
                "url": "https://search.naver.com/search.naver?query=손흥민",
                "locationData": {
                    "primarySelector": "a.tab[data-tab='news']",
                    "fallbackSelectors": ["a:contains('뉴스')", "ul.type_tab a[href*='news']"],
                    "anchorPoint": "#lnb",
                    "relativePathFromAnchor": "a.tab[data-tab='news']",
                    "elementSnapshot": {"tagName": "a", "attributes": {"data-tab": "news"}}
                },
                "semanticData": {
                    "textLabels": ["뉴스", "NEWS"],
                    "contextText": {
                        "immediate": "검색 탭",
                        "section": "검색 옵션",
                        "neighbor": ["통합검색", "이미지", "동영상", "지식iN"]
                    },
                    "pageInfo": {"title": "손흥민 - 네이버 검색", "url": "https://search.naver.com/search.naver?query=손흥민"},
                    "actionType": "click"
                }
            },
            {
                "order": 3,
                "url": "https://search.naver.com/search.naver?where=news&query=손흥민",
                "locationData": {
                    "primarySelector": "a.news_tit",
                    "fallbackSelectors": ["div.news_area a.news_tit", "a[class*='title']"],
                    "anchorPoint": "#main_pack",
                    "relativePathFromAnchor": "a.news_tit",
                    "elementSnapshot": {"tagName": "a", "attributes": {"class": "news_tit"}}
                },
                "semanticData": {
                    "textLabels": ["손흥민 해트트릭", "토트넘 승리"],
                    "contextText": {
                        "immediate": "뉴스 제목",
                        "section": "뉴스 검색결과",
                        "neighbor": ["스포츠서울", "1시간 전", "관련뉴스"]
                    },
                    "pageInfo": {"title": "손흥민 뉴스 - 네이버 검색", "url": "https://search.naver.com/search.naver?where=news&query=손흥민"},
                    "actionType": "click"
                }
            }
        ]
    },
    {
        "sessionId": "naver_002",
        "startCommand": "네이버 지도에서 강남역 맛집 검색 후 예약",
        "completePath": [
            {
                "order": 0,
                "url": "https://map.naver.com",
                "locationData": None,
                "semanticData": None
            },
            {
                "order": 1,
                "url": "https://map.naver.com",
                "locationData": {
                    "primarySelector": "input.search_input",
                    "fallbackSelectors": ["input[placeholder*='검색']", "input#search-input"],
                    "anchorPoint": "#container",
                    "relativePathFromAnchor": "input.search_input",
                    "elementSnapshot": {"tagName": "input", "attributes": {"class": "search_input"}}
                },
                "semanticData": {
                    "textLabels": ["장소 검색", "강남역 맛집"],
                    "contextText": {
                        "immediate": "지도 검색",
                        "section": "검색창",
                        "neighbor": ["길찾기", "내 주변", "즐겨찾기"]
                    },
                    "pageInfo": {"title": "네이버 지도", "url": "https://map.naver.com"},
                    "actionType": "type"
                }
            },
            {
                "order": 2,
                "url": "https://map.naver.com/search/강남역%20맛집",
                "locationData": {
                    "primarySelector": "div.place_item[data-rank='1']",
                    "fallbackSelectors": ["li.search_item:first-child", "a.place_name:first"],
                    "anchorPoint": "#searchList",
                    "relativePathFromAnchor": "div.place_item[data-rank='1']",
                    "elementSnapshot": {"tagName": "div", "attributes": {"data-rank": "1"}}
                },
                "semanticData": {
                    "textLabels": ["1위 맛집", "강남 소고기 전문점"],
                    "contextText": {
                        "immediate": "검색 결과",
                        "section": "맛집 목록",
                        "neighbor": ["별점 4.8", "리뷰 1,234", "영업중"]
                    },
                    "pageInfo": {"title": "강남역 맛집 - 네이버 지도", "url": "https://map.naver.com/search/강남역%20맛집"},
                    "actionType": "click"
                }
            },
            {
                "order": 3,
                "url": "https://map.naver.com/restaurant/1234567890",
                "locationData": {
                    "primarySelector": "button.reservation",
                    "fallbackSelectors": ["a[href*='booking']", "button:contains('예약')"],
                    "anchorPoint": "#app-root",
                    "relativePathFromAnchor": "button.reservation",
                    "elementSnapshot": {"tagName": "button", "attributes": {"class": "reservation"}}
                },
                "semanticData": {
                    "textLabels": ["예약하기", "네이버 예약"],
                    "contextText": {
                        "immediate": "매장 정보",
                        "section": "상세 정보",
                        "neighbor": ["전화", "영업시간", "메뉴"]
                    },
                    "pageInfo": {"title": "강남 소고기 전문점 - 네이버 지도", "url": "https://map.naver.com/restaurant/1234567890"},
                    "actionType": "click"
                }
            }
        ]
    }
]

# 유튜브 한국 콘텐츠 테스트 케이스들
YOUTUBE_KOREA_CASES = [
    {
        "sessionId": "youtube_korea_001",
        "startCommand": "유튜브에서 뉴진스 신곡 MV 검색 후 구독",
        "completePath": [
            {
                "order": 0,
                "url": "https://www.youtube.com",
                "locationData": None,
                "semanticData": None
            },
            {
                "order": 1,
                "url": "https://www.youtube.com",
                "locationData": {
                    "primarySelector": "input#search",
                    "fallbackSelectors": ["ytd-searchbox input", "input[name='search_query']"],
                    "anchorPoint": "#masthead",
                    "relativePathFromAnchor": "input#search",
                    "elementSnapshot": {"tagName": "input", "attributes": {"id": "search"}}
                },
                "semanticData": {
                    "textLabels": ["검색", "뉴진스 신곡"],
                    "contextText": {
                        "immediate": "검색창",
                        "section": "헤더",
                        "neighbor": ["YouTube", "마이크", "만들기"]
                    },
                    "pageInfo": {"title": "YouTube", "url": "https://www.youtube.com"},
                    "actionType": "type"
                }
            },
            {
                "order": 2,
                "url": "https://www.youtube.com/results?search_query=뉴진스+신곡",
                "locationData": {
                    "primarySelector": "ytd-video-renderer:first-child a#video-title",
                    "fallbackSelectors": ["a#video-title:first", "h3.title-and-badge a"],
                    "anchorPoint": "#contents",
                    "relativePathFromAnchor": "ytd-video-renderer:first-child a",
                    "elementSnapshot": {"tagName": "a", "attributes": {"id": "video-title"}}
                },
                "semanticData": {
                    "textLabels": ["NewJeans (뉴진스) 'ETA' Official MV", "HYBE LABELS"],
                    "contextText": {
                        "immediate": "검색 결과",
                        "section": "동영상 목록",
                        "neighbor": ["조회수 10M", "1일 전", "3:21"]
                    },
                    "pageInfo": {"title": "뉴진스 신곡 - YouTube", "url": "https://www.youtube.com/results?search_query=뉴진스+신곡"},
                    "actionType": "click"
                }
            },
            {
                "order": 3,
                "url": "https://www.youtube.com/watch?v=jOTfBlKSQYY",
                "locationData": {
                    "primarySelector": "button#subscribe-button",
                    "fallbackSelectors": ["ytd-subscribe-button-renderer button", "tp-yt-paper-button.ytd-subscribe-button-renderer"],
                    "anchorPoint": "#owner",
                    "relativePathFromAnchor": "button#subscribe-button",
                    "elementSnapshot": {"tagName": "button", "attributes": {"id": "subscribe-button"}}
                },
                "semanticData": {
                    "textLabels": ["구독", "Subscribe"],
                    "contextText": {
                        "immediate": "채널 정보",
                        "section": "동영상 플레이어",
                        "neighbor": ["HYBE LABELS", "구독자 7.2M", "알림 설정"]
                    },
                    "pageInfo": {"title": "NewJeans 'ETA' Official MV - YouTube", "url": "https://www.youtube.com/watch?v=jOTfBlKSQYY"},
                    "actionType": "click"
                }
            }
        ]
    },
    {
        "sessionId": "youtube_korea_002",
        "startCommand": "유튜브에서 쯔양 먹방 라이브 스트리밍 시청",
        "completePath": [
            {
                "order": 0,
                "url": "https://www.youtube.com",
                "locationData": None,
                "semanticData": None
            },
            {
                "order": 1,
                "url": "https://www.youtube.com",
                "locationData": {
                    "primarySelector": "input#search",
                    "fallbackSelectors": ["ytd-searchbox input", "input[name='search_query']"],
                    "anchorPoint": "#masthead",
                    "relativePathFromAnchor": "input#search",
                    "elementSnapshot": {"tagName": "input", "attributes": {"id": "search"}}
                },
                "semanticData": {
                    "textLabels": ["검색", "쯔양"],
                    "contextText": {
                        "immediate": "검색창",
                        "section": "헤더",
                        "neighbor": ["YouTube", "음성 검색"]
                    },
                    "pageInfo": {"title": "YouTube", "url": "https://www.youtube.com"},
                    "actionType": "type"
                }
            },
            {
                "order": 2,
                "url": "https://www.youtube.com/results?search_query=쯔양",
                "locationData": {
                    "primarySelector": "ytd-channel-renderer a.channel-link",
                    "fallbackSelectors": ["a[href*='@tzuyang']", "ytd-channel-renderer #main-link"],
                    "anchorPoint": "#contents",
                    "relativePathFromAnchor": "ytd-channel-renderer a",
                    "elementSnapshot": {"tagName": "a", "attributes": {"class": "channel-link"}}
                },
                "semanticData": {
                    "textLabels": ["쯔양", "tzuyang"],
                    "contextText": {
                        "immediate": "채널",
                        "section": "검색 결과",
                        "neighbor": ["구독자 1024만명", "동영상 832개", "확인됨"]
                    },
                    "pageInfo": {"title": "쯔양 - YouTube", "url": "https://www.youtube.com/results?search_query=쯔양"},
                    "actionType": "click"
                }
            },
            {
                "order": 3,
                "url": "https://www.youtube.com/@tzuyang6812",
                "locationData": {
                    "primarySelector": "paper-tab.tab-content[role='tab']:nth-child(4)",
                    "fallbackSelectors": ["paper-tab:contains('라이브')", "yt-tab-shape[tab-title='라이브']"],
                    "anchorPoint": "#tabsContent",
                    "relativePathFromAnchor": "paper-tab:nth-child(4)",
                    "elementSnapshot": {"tagName": "paper-tab", "attributes": {"role": "tab"}}
                },
                "semanticData": {
                    "textLabels": ["라이브", "LIVE"],
                    "contextText": {
                        "immediate": "채널 탭",
                        "section": "채널 네비게이션",
                        "neighbor": ["홈", "동영상", "Shorts", "재생목록"]
                    },
                    "pageInfo": {"title": "쯔양 - YouTube", "url": "https://www.youtube.com/@tzuyang6812"},
                    "actionType": "click"
                }
            },
            {
                "order": 4,
                "url": "https://www.youtube.com/@tzuyang6812/streams",
                "locationData": {
                    "primarySelector": "ytd-rich-item-renderer:first-child a#thumbnail",
                    "fallbackSelectors": ["a.yt-simple-endpoint[aria-label*='라이브']", "ytd-thumbnail a[href*='live']"],
                    "anchorPoint": "#contents",
                    "relativePathFromAnchor": "ytd-rich-item-renderer:first-child a",
                    "elementSnapshot": {"tagName": "a", "attributes": {"id": "thumbnail"}}
                },
                "semanticData": {
                    "textLabels": ["🔴 실시간 먹방", "치킨 20마리 도전"],
                    "contextText": {
                        "immediate": "라이브 스트림",
                        "section": "라이브 목록",
                        "neighbor": ["실시간 시청자 5.2만명", "스트리밍 중", "슈퍼챗"]
                    },
                    "pageInfo": {"title": "쯔양 라이브 - YouTube", "url": "https://www.youtube.com/@tzuyang6812/streams"},
                    "actionType": "click"
                }
            }
        ]
    }
]

# 배달의민족 테스트 케이스
BAEMIN_CASES = [
    {
        "sessionId": "baemin_001",
        "startCommand": "배민에서 치킨 별점순 정렬 후 BBQ 주문",
        "completePath": [
            {
                "order": 0,
                "url": "https://www.baemin.com",
                "locationData": None,
                "semanticData": None
            },
            {
                "order": 1,
                "url": "https://www.baemin.com",
                "locationData": {
                    "primarySelector": "div.category[data-name='치킨']",
                    "fallbackSelectors": ["div[onclick*='chicken']", "img[alt='치킨']"],
                    "anchorPoint": "#category-grid",
                    "relativePathFromAnchor": "div.category[data-name='치킨']",
                    "elementSnapshot": {"tagName": "div", "attributes": {"data-name": "치킨"}}
                },
                "semanticData": {
                    "textLabels": ["치킨", "Chicken"],
                    "contextText": {
                        "immediate": "카테고리",
                        "section": "음식 카테고리",
                        "neighbor": ["피자", "중식", "한식", "분식"]
                    },
                    "pageInfo": {"title": "배달의민족", "url": "https://www.baemin.com"},
                    "actionType": "click"
                }
            },
            {
                "order": 2,
                "url": "https://www.baemin.com/category/치킨",
                "locationData": {
                    "primarySelector": "button.filter_sort",
                    "fallbackSelectors": ["select.sort-option", "button:contains('별점순')"],
                    "anchorPoint": "#filter-bar",
                    "relativePathFromAnchor": "button.filter_sort",
                    "elementSnapshot": {"tagName": "button", "attributes": {"class": "filter_sort"}}
                },
                "semanticData": {
                    "textLabels": ["별점순", "평점 높은순"],
                    "contextText": {
                        "immediate": "정렬 옵션",
                        "section": "필터",
                        "neighbor": ["기본순", "주문많은순", "배달팁순", "최소주문순"]
                    },
                    "pageInfo": {"title": "치킨 - 배달의민족", "url": "https://www.baemin.com/category/치킨"},
                    "actionType": "click"
                }
            },
            {
                "order": 3,
                "url": "https://www.baemin.com/restaurant/12345",
                "locationData": {
                    "primarySelector": "button.btn_order",
                    "fallbackSelectors": ["a[href*='order']", "button:contains('주문하기')"],
                    "anchorPoint": "#restaurant-detail",
                    "relativePathFromAnchor": "button.btn_order",
                    "elementSnapshot": {"tagName": "button", "attributes": {"class": "btn_order"}}
                },
                "semanticData": {
                    "textLabels": ["주문하기", "Order Now"],
                    "contextText": {
                        "immediate": "주문 버튼",
                        "section": "매장 상세",
                        "neighbor": ["최소주문 17,000원", "배달팁 2,000원", "45분 예상"]
                    },
                    "pageInfo": {"title": "BBQ 치킨 - 배달의민족", "url": "https://www.baemin.com/restaurant/12345"},
                    "actionType": "click"
                }
            }
        ]
    }
]

# 당근마켓 테스트 케이스
DAANGN_CASES = [
    {
        "sessionId": "daangn_001",
        "startCommand": "당근마켓에서 아이패드 검색 후 채팅하기",
        "completePath": [
            {
                "order": 0,
                "url": "https://www.daangn.com",
                "locationData": None,
                "semanticData": None
            },
            {
                "order": 1,
                "url": "https://www.daangn.com",
                "locationData": {
                    "primarySelector": "input.search-input",
                    "fallbackSelectors": ["input[placeholder*='검색']", "input[name='search']"],
                    "anchorPoint": "#header",
                    "relativePathFromAnchor": "input.search-input",
                    "elementSnapshot": {"tagName": "input", "attributes": {"class": "search-input"}}
                },
                "semanticData": {
                    "textLabels": ["동네 검색", "아이패드"],
                    "contextText": {
                        "immediate": "검색창",
                        "section": "헤더",
                        "neighbor": ["당근마켓", "내 근처", "채팅"]
                    },
                    "pageInfo": {"title": "당근마켓", "url": "https://www.daangn.com"},
                    "actionType": "type"
                }
            },
            {
                "order": 2,
                "url": "https://www.daangn.com/search/아이패드",
                "locationData": {
                    "primarySelector": "article.item-card:first-child a",
                    "fallbackSelectors": ["article:first-child a", "a.item-link:first"],
                    "anchorPoint": "#article-list",
                    "relativePathFromAnchor": "article.item-card:first-child a",
                    "elementSnapshot": {"tagName": "a", "attributes": {"class": "item-link"}}
                },
                "semanticData": {
                    "textLabels": ["아이패드 프로 11인치", "350,000원"],
                    "contextText": {
                        "immediate": "중고 물품",
                        "section": "검색 결과",
                        "neighbor": ["강남구", "1시간 전", "관심 23"]
                    },
                    "pageInfo": {"title": "아이패드 - 당근마켓", "url": "https://www.daangn.com/search/아이패드"},
                    "actionType": "click"
                }
            },
            {
                "order": 3,
                "url": "https://www.daangn.com/articles/567890123",
                "locationData": {
                    "primarySelector": "button.btn_chat",
                    "fallbackSelectors": ["button:contains('채팅하기')", "a[href*='chat']"],
                    "anchorPoint": "#article-detail",
                    "relativePathFromAnchor": "button.btn_chat",
                    "elementSnapshot": {"tagName": "button", "attributes": {"class": "btn_chat"}}
                },
                "semanticData": {
                    "textLabels": ["채팅하기", "문의하기"],
                    "contextText": {
                        "immediate": "연락 수단",
                        "section": "상품 상세",
                        "neighbor": ["관심", "공유", "가격제안"]
                    },
                    "pageInfo": {"title": "아이패드 프로 11인치 - 당근마켓", "url": "https://www.daangn.com/articles/567890123"},
                    "actionType": "click"
                }
            }
        ]
    }
]

# 무신사 테스트 케이스
MUSINSA_CASES = [
    {
        "sessionId": "musinsa_001",
        "startCommand": "무신사에서 나이키 브랜드 스트릿 코디 전체구매",
        "completePath": [
            {
                "order": 0,
                "url": "https://www.musinsa.com",
                "locationData": None,
                "semanticData": None
            },
            {
                "order": 1,
                "url": "https://www.musinsa.com",
                "locationData": {
                    "primarySelector": "a.brand-link",
                    "fallbackSelectors": ["nav a:contains('브랜드')", "a[href*='brand']"],
                    "anchorPoint": "#gnb",
                    "relativePathFromAnchor": "a.brand-link",
                    "elementSnapshot": {"tagName": "a", "attributes": {"class": "brand-link"}}
                },
                "semanticData": {
                    "textLabels": ["브랜드", "BRAND"],
                    "contextText": {
                        "immediate": "메인 메뉴",
                        "section": "네비게이션",
                        "neighbor": ["랭킹", "업데이트", "코디", "세일"]
                    },
                    "pageInfo": {"title": "무신사 스토어", "url": "https://www.musinsa.com"},
                    "actionType": "click"
                }
            },
            {
                "order": 2,
                "url": "https://www.musinsa.com/brands",
                "locationData": {
                    "primarySelector": "a[data-brand='nike']",
                    "fallbackSelectors": ["a:contains('나이키')", "div.brand-item a[href*='nike']"],
                    "anchorPoint": "#brand-list",
                    "relativePathFromAnchor": "a[data-brand='nike']",
                    "elementSnapshot": {"tagName": "a", "attributes": {"data-brand": "nike"}}
                },
                "semanticData": {
                    "textLabels": ["나이키", "NIKE"],
                    "contextText": {
                        "immediate": "브랜드 목록",
                        "section": "인기 브랜드",
                        "neighbor": ["아디다스", "컨버스", "반스", "뉴발란스"]
                    },
                    "pageInfo": {"title": "브랜드 - 무신사", "url": "https://www.musinsa.com/brands"},
                    "actionType": "click"
                }
            },
            {
                "order": 3,
                "url": "https://www.musinsa.com/brands/nike",
                "locationData": {
                    "primarySelector": "a.coordi-tab",
                    "fallbackSelectors": ["a:contains('코디')", "nav a[href*='coordi']"],
                    "anchorPoint": "#brand-nav",
                    "relativePathFromAnchor": "a.coordi-tab",
                    "elementSnapshot": {"tagName": "a", "attributes": {"class": "coordi-tab"}}
                },
                "semanticData": {
                    "textLabels": ["코디", "스타일"],
                    "contextText": {
                        "immediate": "브랜드 메뉴",
                        "section": "나이키 페이지",
                        "neighbor": ["상품", "매거진", "스냅", "리뷰"]
                    },
                    "pageInfo": {"title": "나이키 - 무신사", "url": "https://www.musinsa.com/brands/nike"},
                    "actionType": "click"
                }
            },
            {
                "order": 4,
                "url": "https://www.musinsa.com/brands/nike/coordi",
                "locationData": {
                    "primarySelector": "div.coordi-item[data-style='street']",
                    "fallbackSelectors": ["div.style-card:first", "a.coordi-link[data-style='street']"],
                    "anchorPoint": "#coordi-list",
                    "relativePathFromAnchor": "div.coordi-item[data-style='street']",
                    "elementSnapshot": {"tagName": "div", "attributes": {"data-style": "street"}}
                },
                "semanticData": {
                    "textLabels": ["스트릿 코디", "Street Style"],
                    "contextText": {
                        "immediate": "코디 상품",
                        "section": "나이키 코디",
                        "neighbor": ["좋아요 1.2K", "댓글 89", "총 5개 아이템"]
                    },
                    "pageInfo": {"title": "나이키 코디 - 무신사", "url": "https://www.musinsa.com/brands/nike/coordi"},
                    "actionType": "click"
                }
            },
            {
                "order": 5,
                "url": "https://www.musinsa.com/coordi/detail/34567",
                "locationData": {
                    "primarySelector": "button.btn_buy_all",
                    "fallbackSelectors": ["button:contains('전체구매')", "a.all-buy"],
                    "anchorPoint": "#coordi-detail",
                    "relativePathFromAnchor": "button.btn_buy_all",
                    "elementSnapshot": {"tagName": "button", "attributes": {"class": "btn_buy_all"}}
                },
                "semanticData": {
                    "textLabels": ["전체구매", "한번에 구매"],
                    "contextText": {
                        "immediate": "구매 옵션",
                        "section": "코디 상세",
                        "neighbor": ["총 금액 428,000원", "5개 상품", "장바구니"]
                    },
                    "pageInfo": {"title": "스트릿 코디 - 무신사", "url": "https://www.musinsa.com/coordi/detail/34567"},
                    "actionType": "click"
                }
            }
        ]
    }
]

# 멜론 테스트 케이스
MELON_CASES = [
    {
        "sessionId": "melon_001",
        "startCommand": "멜론 TOP100에서 1위곡 재생 후 플레이리스트 추가",
        "completePath": [
            {
                "order": 0,
                "url": "https://www.melon.com",
                "locationData": None,
                "semanticData": None
            },
            {
                "order": 1,
                "url": "https://www.melon.com",
                "locationData": {
                    "primarySelector": "a.menu_chart",
                    "fallbackSelectors": ["a:contains('멜론차트')", "nav a[href*='chart']"],
                    "anchorPoint": "#gnb",
                    "relativePathFromAnchor": "a.menu_chart",
                    "elementSnapshot": {"tagName": "a", "attributes": {"class": "menu_chart"}}
                },
                "semanticData": {
                    "textLabels": ["멜론차트", "Chart"],
                    "contextText": {
                        "immediate": "메인 메뉴",
                        "section": "네비게이션",
                        "neighbor": ["최신", "장르", "DJ플레이리스트", "매거진"]
                    },
                    "pageInfo": {"title": "멜론", "url": "https://www.melon.com"},
                    "actionType": "click"
                }
            },
            {
                "order": 2,
                "url": "https://www.melon.com/chart",
                "locationData": {
                    "primarySelector": "a.top100",
                    "fallbackSelectors": ["a:contains('TOP100')", "div.chart_menu a[href*='top100']"],
                    "anchorPoint": "#conts",
                    "relativePathFromAnchor": "a.top100",
                    "elementSnapshot": {"tagName": "a", "attributes": {"class": "top100"}}
                },
                "semanticData": {
                    "textLabels": ["TOP100", "실시간 차트"],
                    "contextText": {
                        "immediate": "차트 종류",
                        "section": "멜론차트",
                        "neighbor": ["일간", "주간", "월간", "HOT100"]
                    },
                    "pageInfo": {"title": "멜론차트 - 멜론", "url": "https://www.melon.com/chart"},
                    "actionType": "click"
                }
            },
            {
                "order": 3,
                "url": "https://www.melon.com/chart/top100",
                "locationData": {
                    "primarySelector": "tr[data-rank='1'] button.btn_play",
                    "fallbackSelectors": ["tr:first-child .btn_icon.play", "button[title='재생']"],
                    "anchorPoint": "#frm",
                    "relativePathFromAnchor": "tr[data-rank='1'] button.btn_play",
                    "elementSnapshot": {"tagName": "button", "attributes": {"class": "btn_play"}}
                },
                "semanticData": {
                    "textLabels": ["재생", "Play"],
                    "contextText": {
                        "immediate": "1위",
                        "section": "TOP100",
                        "neighbor": ["Seven (feat. Latto)", "정국", "담기"]
                    },
                    "pageInfo": {"title": "멜론 TOP100 - 멜론", "url": "https://www.melon.com/chart/top100"},
                    "actionType": "click"
                }
            },
            {
                "order": 4,
                "url": "https://www.melon.com/chart/top100",
                "locationData": {
                    "primarySelector": "tr[data-rank='1'] button.btn_add_playlist",
                    "fallbackSelectors": ["button[title='플레이리스트 추가']", "a.btn_menu_add"],
                    "anchorPoint": "#frm",
                    "relativePathFromAnchor": "tr[data-rank='1'] button.btn_add_playlist",
                    "elementSnapshot": {"tagName": "button", "attributes": {"class": "btn_add_playlist"}}
                },
                "semanticData": {
                    "textLabels": ["플레이리스트 추가", "+"],
                    "contextText": {
                        "immediate": "곡 옵션",
                        "section": "1위 곡",
                        "neighbor": ["재생", "담기", "다운", "뮤비"]
                    },
                    "pageInfo": {"title": "멜론 TOP100 - 멜론", "url": "https://www.melon.com/chart/top100"},
                    "actionType": "click"
                }
            }
        ]
    }
]

# 왓챠 테스트 케이스
WATCHA_CASES = [
    {
        "sessionId": "watcha_001",
        "startCommand": "왓챠에서 한국 드라마 이상한 변호사 우영우 시청",
        "completePath": [
            {
                "order": 0,
                "url": "https://watcha.com",
                "locationData": None,
                "semanticData": None
            },
            {
                "order": 1,
                "url": "https://watcha.com",
                "locationData": {
                    "primarySelector": "a[href='/browse']",
                    "fallbackSelectors": ["a:contains('탐색')", "nav a.browse"],
                    "anchorPoint": "#root",
                    "relativePathFromAnchor": "a[href='/browse']",
                    "elementSnapshot": {"tagName": "a", "attributes": {"href": "/browse"}}
                },
                "semanticData": {
                    "textLabels": ["탐색", "Browse"],
                    "contextText": {
                        "immediate": "메인 메뉴",
                        "section": "네비게이션",
                        "neighbor": ["홈", "평가", "보관함", "검색"]
                    },
                    "pageInfo": {"title": "왓챠", "url": "https://watcha.com"},
                    "actionType": "click"
                }
            },
            {
                "order": 2,
                "url": "https://watcha.com/browse",
                "locationData": {
                    "primarySelector": "button.filter_korean",
                    "fallbackSelectors": ["button:contains('한국')", "div.filter button[data-country='KR']"],
                    "anchorPoint": "#browse-filters",
                    "relativePathFromAnchor": "button.filter_korean",
                    "elementSnapshot": {"tagName": "button", "attributes": {"class": "filter_korean"}}
                },
                "semanticData": {
                    "textLabels": ["한국", "Korean"],
                    "contextText": {
                        "immediate": "국가 필터",
                        "section": "필터 옵션",
                        "neighbor": ["미국", "일본", "영국", "중국"]
                    },
                    "pageInfo": {"title": "탐색 - 왓챠", "url": "https://watcha.com/browse"},
                    "actionType": "click"
                }
            },
            {
                "order": 3,
                "url": "https://watcha.com/browse?country=KR",
                "locationData": {
                    "primarySelector": "button.filter_drama",
                    "fallbackSelectors": ["button:contains('드라마')", "div.genre button[data-genre='drama']"],
                    "anchorPoint": "#browse-filters",
                    "relativePathFromAnchor": "button.filter_drama",
                    "elementSnapshot": {"tagName": "button", "attributes": {"class": "filter_drama"}}
                },
                "semanticData": {
                    "textLabels": ["드라마", "Drama"],
                    "contextText": {
                        "immediate": "장르 필터",
                        "section": "필터 옵션",
                        "neighbor": ["영화", "예능", "다큐멘터리", "애니메이션"]
                    },
                    "pageInfo": {"title": "한국 콘텐츠 - 왓챠", "url": "https://watcha.com/browse?country=KR"},
                    "actionType": "click"
                }
            },
            {
                "order": 4,
                "url": "https://watcha.com/browse?country=KR&genre=drama",
                "locationData": {
                    "primarySelector": "div.content_item a[title='이상한 변호사 우영우']",
                    "fallbackSelectors": ["a:contains('우영우')", "div.poster a[href*='woo-young-woo']"],
                    "anchorPoint": "#content-grid",
                    "relativePathFromAnchor": "div.content_item a[title='이상한 변호사 우영우']",
                    "elementSnapshot": {"tagName": "a", "attributes": {"title": "이상한 변호사 우영우"}}
                },
                "semanticData": {
                    "textLabels": ["이상한 변호사 우영우", "16부작"],
                    "contextText": {
                        "immediate": "드라마",
                        "section": "한국 드라마",
                        "neighbor": ["평점 4.5", "2022", "법정"]
                    },
                    "pageInfo": {"title": "한국 드라마 - 왓챠", "url": "https://watcha.com/browse?country=KR&genre=drama"},
                    "actionType": "click"
                }
            },
            {
                "order": 5,
                "url": "https://watcha.com/contents/tDxGW8r",
                "locationData": {
                    "primarySelector": "button.btn_play",
                    "fallbackSelectors": ["button:contains('재생')", "a.watch-now"],
                    "anchorPoint": "#content-detail",
                    "relativePathFromAnchor": "button.btn_play",
                    "elementSnapshot": {"tagName": "button", "attributes": {"class": "btn_play"}}
                },
                "semanticData": {
                    "textLabels": ["재생", "1화 시청하기"],
                    "contextText": {
                        "immediate": "시청 옵션",
                        "section": "드라마 상세",
                        "neighbor": ["보고싶어요", "평가하기", "코멘트"]
                    },
                    "pageInfo": {"title": "이상한 변호사 우영우 - 왓챠", "url": "https://watcha.com/contents/tDxGW8r"},
                    "actionType": "click"
                }
            }
        ]
    }
]

# SSG닷컴 테스트 케이스
SSG_CASES = [
    {
        "sessionId": "ssg_001",
        "startCommand": "SSG닷컴 새벽배송으로 한우 구매",
        "completePath": [
            {
                "order": 0,
                "url": "https://www.ssg.com",
                "locationData": None,
                "semanticData": None
            },
            {
                "order": 1,
                "url": "https://www.ssg.com",
                "locationData": {
                    "primarySelector": "a.dawn_delivery",
                    "fallbackSelectors": ["a:contains('새벽배송')", "nav a[href*='dawn']"],
                    "anchorPoint": "#header",
                    "relativePathFromAnchor": "a.dawn_delivery",
                    "elementSnapshot": {"tagName": "a", "attributes": {"class": "dawn_delivery"}}
                },
                "semanticData": {
                    "textLabels": ["새벽배송", "쓱-새벽배송"],
                    "contextText": {
                        "immediate": "배송 서비스",
                        "section": "헤더",
                        "neighbor": ["쓱배송", "트레이더스", "백화점배송"]
                    },
                    "pageInfo": {"title": "SSG.COM", "url": "https://www.ssg.com"},
                    "actionType": "click"
                }
            },
            {
                "order": 2,
                "url": "https://www.ssg.com/service/dawn",
                "locationData": {
                    "primarySelector": "a[data-category='fresh']",
                    "fallbackSelectors": ["a:contains('신선식품')", "div.category a[href*='fresh']"],
                    "anchorPoint": "#category-nav",
                    "relativePathFromAnchor": "a[data-category='fresh']",
                    "elementSnapshot": {"tagName": "a", "attributes": {"data-category": "fresh"}}
                },
                "semanticData": {
                    "textLabels": ["신선식품", "Fresh"],
                    "contextText": {
                        "immediate": "카테고리",
                        "section": "새벽배송",
                        "neighbor": ["정육", "수산", "과일", "채소"]
                    },
                    "pageInfo": {"title": "새벽배송 - SSG.COM", "url": "https://www.ssg.com/service/dawn"},
                    "actionType": "click"
                }
            },
            {
                "order": 3,
                "url": "https://www.ssg.com/service/dawn/fresh",
                "locationData": {
                    "primarySelector": "input.search_input",
                    "fallbackSelectors": ["input[placeholder*='검색']", "input#query"],
                    "anchorPoint": "#searchbar",
                    "relativePathFromAnchor": "input.search_input",
                    "elementSnapshot": {"tagName": "input", "attributes": {"class": "search_input"}}
                },
                "semanticData": {
                    "textLabels": ["검색", "한우"],
                    "contextText": {
                        "immediate": "상품 검색",
                        "section": "검색창",
                        "neighbor": ["검색버튼", "최근검색어"]
                    },
                    "pageInfo": {"title": "신선식품 - SSG.COM", "url": "https://www.ssg.com/service/dawn/fresh"},
                    "actionType": "type"
                }
            },
            {
                "order": 4,
                "url": "https://www.ssg.com/search?query=한우",
                "locationData": {
                    "primarySelector": "div.product a[data-info*='한우 1++']",
                    "fallbackSelectors": ["li.product_item:first a", "a.product_link:contains('한우')"],
                    "anchorPoint": "#product_list",
                    "relativePathFromAnchor": "div.product a[data-info*='한우 1++']",
                    "elementSnapshot": {"tagName": "a", "attributes": {"data-info": "한우 1++"}}
                },
                "semanticData": {
                    "textLabels": ["한우 1++ 등심", "300g"],
                    "contextText": {
                        "immediate": "상품",
                        "section": "검색 결과",
                        "neighbor": ["39,900원", "무료배송", "리뷰 4.9"]
                    },
                    "pageInfo": {"title": "한우 검색결과 - SSG.COM", "url": "https://www.ssg.com/search?query=한우"},
                    "actionType": "click"
                }
            },
            {
                "order": 5,
                "url": "https://www.ssg.com/item/dealItemView.ssg?itemId=1000034567890",
                "locationData": {
                    "primarySelector": "button.btn_buy",
                    "fallbackSelectors": ["button:contains('구매하기')", "a.order_btn"],
                    "anchorPoint": "#order_area",
                    "relativePathFromAnchor": "button.btn_buy",
                    "elementSnapshot": {"tagName": "button", "attributes": {"class": "btn_buy"}}
                },
                "semanticData": {
                    "textLabels": ["구매하기", "바로구매"],
                    "contextText": {
                        "immediate": "주문",
                        "section": "상품 상세",
                        "neighbor": ["장바구니", "선물하기", "수량"]
                    },
                    "pageInfo": {"title": "한우 1++ 등심 - SSG.COM", "url": "https://www.ssg.com/item/dealItemView.ssg?itemId=1000034567890"},
                    "actionType": "click"
                }
            }
        ]
    }
]

# 모든 테스트 케이스를 하나의 리스트로 결합
ALL_KOREAN_TEST_CASES = (
    NAVER_WEBTOON_CASES +
    COUPANG_CASES +
    NAMUWIKI_CASES +
    NAVER_CASES +
    YOUTUBE_KOREA_CASES +
    BAEMIN_CASES +
    DAANGN_CASES +
    MUSINSA_CASES +
    MELON_CASES +
    WATCHA_CASES +
    SSG_CASES
)

# 테스트 데이터 개수 확인
print(f"총 테스트 케이스 수: {len(ALL_KOREAN_TEST_CASES)}")
print(f"네이버 웹툰: {len(NAVER_WEBTOON_CASES)}")
print(f"쿠팡: {len(COUPANG_CASES)}")
print(f"나무위키: {len(NAMUWIKI_CASES)}")
print(f"네이버: {len(NAVER_CASES)}")
print(f"유튜브 한국: {len(YOUTUBE_KOREA_CASES)}")
print(f"배민: {len(BAEMIN_CASES)}")
print(f"당근마켓: {len(DAANGN_CASES)}")
print(f"무신사: {len(MUSINSA_CASES)}")
print(f"멜론: {len(MELON_CASES)}")
print(f"왓챠: {len(WATCHA_CASES)}")
print(f"SSG: {len(SSG_CASES)}")