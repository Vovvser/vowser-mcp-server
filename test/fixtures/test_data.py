"""
테스트용 데이터 Fixtures
"""

# 테스트 케이스 1: YouTube에서 음악 검색 후 필터 적용
TEST_CASE_1 = {
    "sessionId": "session_20250123_test1",
    "startCommand": "유튜브에서 최신 음악 영상 찾기",
    "completePath": [
        {
            "order": 0,
            "url": "https://youtube.com",
            "locationData": None,
            "semanticData": None
        },
        {
            "order": 1,
            "url": "https://youtube.com",
            "locationData": {
                "primarySelector": "input#search",
                "fallbackSelectors": ["ytd-searchbox input", "input[name='search_query']"],
                "anchorPoint": "#masthead",
                "relativePathFromAnchor": "input#search",
                "elementSnapshot": {"tagName": "input", "attributes": {"id": "search"}}
            },
            "semanticData": {
                "textLabels": ["검색", "Search"],
                "contextText": {
                    "immediate": "검색창",
                    "section": "헤더",
                    "neighbor": ["YouTube", "마이크"]
                },
                "pageInfo": {"title": "YouTube", "url": "https://youtube.com"},
                "actionType": "click"
            }
        },
        {
            "order": 2,
            "url": "https://youtube.com/results?search_query=음악",
            "locationData": {
                "primarySelector": "button[aria-label='검색 필터']",
                "fallbackSelectors": ["#filter-button", "ytd-search-filter-renderer button"],
                "anchorPoint": "#container",
                "relativePathFromAnchor": "button[aria-label='검색 필터']",
                "elementSnapshot": {"tagName": "button"}
            },
            "semanticData": {
                "textLabels": ["필터", "검색 필터"],
                "contextText": {
                    "immediate": "검색 도구",
                    "section": "검색 결과",
                    "neighbor": ["정렬 기준", "모든 동영상"]
                },
                "pageInfo": {"title": "음악 - YouTube", "url": "https://youtube.com/results?search_query=음악"},
                "actionType": "click"
            }
        },
        {
            "order": 3,
            "url": "https://youtube.com/results?search_query=음악&sp=CAI%253D",
            "locationData": {
                "primarySelector": "a[aria-label='오늘']",
                "fallbackSelectors": ["yt-chip-cloud-chip-renderer:contains('오늘')"],
                "anchorPoint": "#chips",
                "relativePathFromAnchor": "a[aria-label='오늘']",
                "elementSnapshot": {"tagName": "a"}
            },
            "semanticData": {
                "textLabels": ["오늘", "Today"],
                "contextText": {
                    "immediate": "업로드 날짜",
                    "section": "필터",
                    "neighbor": ["이번 주", "이번 달", "올해"]
                },
                "pageInfo": {"title": "음악 - YouTube", "url": "https://youtube.com/results?search_query=음악&sp=CAI%253D"},
                "actionType": "click"
            }
        },
        {
            "order": 4,
            "url": "https://youtube.com/results?search_query=음악&sp=EgIIAg%253D%253D",
            "locationData": {
                "primarySelector": "ytd-video-renderer:first-child a#video-title",
                "fallbackSelectors": ["a#video-title:first", "h3.title-and-badge a"],
                "anchorPoint": "#contents",
                "relativePathFromAnchor": "ytd-video-renderer:first-child a",
                "elementSnapshot": {"tagName": "a", "attributes": {"id": "video-title"}}
            },
            "semanticData": {
                "textLabels": ["첫 번째 동영상", "최신 음악"],
                "contextText": {
                    "immediate": "동영상 제목",
                    "section": "검색 결과",
                    "neighbor": ["조회수", "업로드 날짜"]
                },
                "pageInfo": {"title": "음악 (오늘) - YouTube", "url": "https://youtube.com/results?search_query=음악&sp=EgIIAg%253D%253D"},
                "actionType": "click"
            }
        }
    ]
}

# 테스트 케이스 2: YouTube에서 음악 검색 후 바로 선택 (일부 경로 공유)
TEST_CASE_2 = {
    "sessionId": "session_20250123_test2",
    "startCommand": "유튜브에서 인기 음악 영상 보기",
    "completePath": [
        {
            "order": 0,
            "url": "https://youtube.com",
            "locationData": None,
            "semanticData": None
        },
        {
            "order": 1,
            "url": "https://youtube.com",
            "locationData": {
                "primarySelector": "input#search",
                "fallbackSelectors": ["ytd-searchbox input", "input[name='search_query']"],
                "anchorPoint": "#masthead",
                "relativePathFromAnchor": "input#search",
                "elementSnapshot": {"tagName": "input", "attributes": {"id": "search"}}
            },
            "semanticData": {
                "textLabels": ["검색", "Search"],
                "contextText": {
                    "immediate": "검색창",
                    "section": "헤더",
                    "neighbor": ["YouTube", "마이크"]
                },
                "pageInfo": {"title": "YouTube", "url": "https://youtube.com"},
                "actionType": "click"
            }
        },
        {
            "order": 2,
            "url": "https://youtube.com/results?search_query=음악",
            "locationData": {
                "primarySelector": "ytd-video-renderer:nth-child(3) a#video-title",
                "fallbackSelectors": ["#contents ytd-video-renderer:nth-child(3) a"],
                "anchorPoint": "#contents",
                "relativePathFromAnchor": "ytd-video-renderer:nth-child(3) a",
                "elementSnapshot": {"tagName": "a", "attributes": {"id": "video-title"}}
            },
            "semanticData": {
                "textLabels": ["세 번째 동영상", "인기 음악"],
                "contextText": {
                    "immediate": "동영상 제목",
                    "section": "검색 결과",
                    "neighbor": ["조회수 1M", "3일 전"]
                },
                "pageInfo": {"title": "음악 - YouTube", "url": "https://youtube.com/results?search_query=음악"},
                "actionType": "click"
            }
        },
        {
            "order": 3,
            "url": "https://youtube.com/watch?v=abc123",
            "locationData": {
                "primarySelector": "button[aria-label='좋아요']",
                "fallbackSelectors": ["#top-level-buttons button:first-child", "like-button-view-model button"],
                "anchorPoint": "#actions",
                "relativePathFromAnchor": "button[aria-label='좋아요']",
                "elementSnapshot": {"tagName": "button"}
            },
            "semanticData": {
                "textLabels": ["좋아요", "Like"],
                "contextText": {
                    "immediate": "동영상 액션",
                    "section": "플레이어",
                    "neighbor": ["싫어요", "공유", "저장"]
                },
                "pageInfo": {"title": "인기 음악 - YouTube", "url": "https://youtube.com/watch?v=abc123"},
                "actionType": "click"
            }
        }
    ]
}

# 원래 예시 데이터 (유튜브에서 좋아요 한 음악 재생목록 열기)
ORIGINAL_EXAMPLE = {
    "sessionId": "session_20250123_001",
    "startCommand": "유튜브에서 좋아요 한 음악 재생목록 열기",
    "completePath": [
        {
            "order": 0,
            "url": "https://youtube.com",
            "locationData": None,  # 시작점이므로 클릭 요소 없음
            "semanticData": None
        },
        {
            "order": 1,
            "url": "https://youtube.com",
            "locationData": {
                "primarySelector": "button[aria-label='라이브러리']",
                "fallbackSelectors": [
                    "ytd-mini-guide-entry-renderer:nth-child(4) button",
                    "button:has-text('라이브러리')"
                ],
                "anchorPoint": "#guide-renderer",
                "relativePathFromAnchor": "button[aria-label='라이브러리']",
                "elementSnapshot": {
                    "tagName": "button",
                    "attributes": {
                        "id": "endpoint",
                        "aria-label": "라이브러리",
                        "class": "style-scope ytd-mini-guide-entry-renderer"
                    }
                }
            },
            "semanticData": {
                "textLabels": [
                    "라이브러리",
                    "Library"
                ],
                "contextText": {
                    "immediate": "YouTube 가이드",
                    "section": "메인 네비게이션",
                    "neighbor": ["홈", "Shorts", "구독"]
                },
                "pageInfo": {
                    "title": "YouTube",
                    "url": "https://youtube.com"
                },
                "actionType": "click"
            }
        },
        {
            "order": 2,
            "url": "https://youtube.com/feed/library",
            "locationData": {
                "primarySelector": "tp-yt-paper-tab[aria-label='재생목록']",
                "fallbackSelectors": [
                    "paper-tab:nth-child(3)",
                    "tp-yt-paper-tab:has-text('재생목록')"
                ],
                "anchorPoint": "#tabs-container",
                "relativePathFromAnchor": "tp-yt-paper-tab:nth-child(3)",
                "elementSnapshot": {
                    "tagName": "tp-yt-paper-tab",
                    "attributes": {
                        "aria-label": "재생목록",
                        "role": "tab"
                    }
                }
            },
            "semanticData": {
                "textLabels": [
                    "재생목록",
                    "Playlists"
                ],
                "contextText": {
                    "immediate": "라이브러리 탭",
                    "section": "YouTube 라이브러리",
                    "neighbor": ["기록", "동영상", "나중에 볼 동영상", "좋아요 표시한 동영상"]
                },
                "pageInfo": {
                    "title": "라이브러리 - YouTube",
                    "url": "https://youtube.com/feed/library"
                },
                "actionType": "click"
            }
        },
        {
            "order": 3,
            "url": "https://youtube.com/feed/library/playlists",
            "locationData": {
                "primarySelector": "a[title='좋아요 표시한 음악']",
                "fallbackSelectors": [
                    "ytd-playlist-thumbnail a[href*='LM']",
                    "#content a:has-text('좋아요 표시한 음악')"
                ],
                "anchorPoint": "#contents",
                "relativePathFromAnchor": "ytd-grid-renderer a[title='좋아요 표시한 음악']",
                "elementSnapshot": {
                    "tagName": "a",
                    "attributes": {
                        "href": "/playlist?list=LM",
                        "title": "좋아요 표시한 음악"
                    }
                }
            },
            "semanticData": {
                "textLabels": [
                    "좋아요 표시한 음악",
                    "Liked Music",
                    "자동 재생목록"
                ],
                "contextText": {
                    "immediate": "재생목록",
                    "section": "내 재생목록",
                    "neighbor": ["나중에 볼 동영상", "새 재생목록"]
                },
                "pageInfo": {
                    "title": "재생목록 - YouTube",
                    "url": "https://youtube.com/feed/library/playlists"
                },
                "actionType": "click"
            }
        }
    ]
}

# 모든 테스트 케이스 리스트
ALL_TEST_CASES = [
    TEST_CASE_1,
    TEST_CASE_2,
    ORIGINAL_EXAMPLE
]

# 간단한 검증용 테스트 케이스 (최소한의 데이터)
MINIMAL_TEST_CASE = {
    "sessionId": "minimal_test",
    "startCommand": "간단한 테스트",
    "completePath": [
        {
            "order": 0,
            "url": "https://example.com",
            "locationData": None,
            "semanticData": None
        },
        {
            "order": 1,
            "url": "https://example.com/page1",
            "locationData": {
                "primarySelector": "button#test",
                "fallbackSelectors": ["button.test-btn"],
                "anchorPoint": "body",
                "relativePathFromAnchor": "button#test",
                "elementSnapshot": {"tagName": "button", "attributes": {"id": "test"}}
            },
            "semanticData": {
                "textLabels": ["테스트 버튼"],
                "contextText": {
                    "immediate": "메인 페이지",
                    "section": "콘텐츠 영역",
                    "neighbor": ["링크1", "링크2"]
                },
                "pageInfo": {"title": "Example Page", "url": "https://example.com"},
                "actionType": "click"
            }
        }
    ]
}