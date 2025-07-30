# Vowser MCP Server - WebSocket API 문서

## 연결 정보
- **WebSocket URL**: `ws://localhost:8000/ws`
- **프로토콜**: JSON 메시지 기반 양방향 통신

## 메시지 포맷

### 요청 메시지 구조
```json
{
  "type": "메시지_타입",
  "data": {
    // 메시지별 데이터
  }
}
```

### 응답 메시지 구조
```json
{
  "type": "응답_타입",
  "status": "success|error",
  "data": {
    // 응답 데이터
  }
}
```

## 지원 메시지 타입

### 1. 페이지 구조 분석 (PRD 4.1.1)

**요청:**
```json
{
  "type": "analyze_page",
  "data": {
    "url": "https://example.com",
    "save_to_db": true
  }
}
```

**응답:**
```json
{
  "type": "page_analysis_result",
  "status": "success",
  "data": {
    "analysis": {
      "page_title": "페이지 제목",
      "sections": [
        {
          "section_name": "섹션명",
          "elements": [
            {
              "text": "요소 텍스트",
              "action_type": "click|input|navigate"
            }
          ]
        }
      ]
    },
    "metadata": {
      "url": "https://example.com",
      "saved_to_db": true,
      "save_result": {...}
    }
  }
}
```

### 2. 음성 명령 경로 저장 (PRD 4.1.2)

**요청:**
```json
{
  "type": "save_path",
  "data": {
    "startCommand": "유튜브에서 음악 찾기",
    "completePath": [
      {
        "order": 0,
        "url": "https://youtube.com",
        "actionType": "navigate"
      },
      {
        "order": 1,
        "url": "https://youtube.com",
        "actionType": "click",
        "locationData": {
          "primarySelector": "#search-input",
          "fallbackSelectors": [".search-box"]
        },
        "semanticData": {
          "textLabels": ["검색"],
          "actionType": "input",
          "contextText": {
            "immediate": "검색창",
            "section": "헤더 영역"
          }
        }
      }
    ]
  }
}
```

**응답:**
```json
{
  "type": "path_save_result",
  "status": "success",
  "data": {
    "message": "Path data processed successfully!",
    "result": {
      "status": "success",
      "saved_steps": 1
    }
  }
}
```

### 3. 분석 기록 조회 (PRD 4.1.3)

**요청:**
```json
{
  "type": "get_analysis_history",
  "data": {
    "domain": "youtube.com",  // 선택사항
    "limit": 10
  }
}
```

**응답:**
```json
{
  "type": "analysis_history_result",
  "status": "success",
  "data": {
    "analysis_history": [
      {
        "analysisId": "abc123",
        "url": "https://youtube.com",
        "domain": "youtube.com",
        "pageTitle": "YouTube",
        "analyzedAt": "2024-01-15T10:30:00Z",
        "sectionsCount": 5
      }
    ],
    "total_count": 1
  }
}
```

### 4. 통합 분석 대시보드 (PRD 4.1.4)

**요청:**
```json
{
  "type": "get_analytics_dashboard",
  "data": {}
}
```

**응답:**
```json
{
  "type": "analytics_dashboard_result",
  "status": "success",
  "data": {
    "dashboard": {
      "graph_statistics": {
        "root_count": 5,
        "page_count": 25,
        "has_page_count": 20,
        "navigates_to_count": 15,
        "cross_domain_count": 3
      },
      "domain_statistics": [...],
      "popular_paths": [...],
      "weighted_paths": [...]
    }
  }
}
```

### 5. 특정 도메인 분석 (PRD 4.1.4)

**요청:**
```json
{
  "type": "get_domain_analysis",
  "data": {
    "domain": "youtube.com"
  }
}
```

**응답:**
```json
{
  "type": "domain_analysis_result",
  "status": "success",
  "data": {
    "domain": "youtube.com",
    "analysis": {
      "paths": [...],
      "popular_paths": [...]
    }
  }
}
```

## 에러 처리

**에러 응답:**
```json
{
  "type": "error",
  "status": "error",
  "data": {
    "message": "에러 메시지",
    "original_type": "원본_메시지_타입"
  }
}
```

## 연결 상태 관리

- **연결 성공**: 로그에 "✅ WebSocket 연결됨" 출력
- **연결 종료**: 로그에 "❌ WebSocket 연결 종료" 출력
- **처리 로그**: 각 메시지 처리 시 상세 로그 출력

## vowser-backend 통합 예시

```kotlin
// Kotlin WebSocket 클라이언트 예시
val client = OkHttpClient()
val request = Request.Builder()
    .url("ws://localhost:8000/ws")
    .build()

val webSocket = client.newWebSocket(request, object : WebSocketListener() {
    override fun onMessage(webSocket: WebSocket, text: String) {
        val response = JSON.parse(text)
        // 응답 처리
    }
})

// 페이지 분석 요청
val message = """
{
  "type": "analyze_page",
  "data": {
    "url": "https://youtube.com",
    "save_to_db": true
  }
}
"""
webSocket.send(message)
```