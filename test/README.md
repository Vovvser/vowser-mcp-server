# Vowser MCP Server - 테스트 가이드

## 테스트 구조 개요

이 프로젝트는 **FastAPI + WebSocket 서버**입니다. 
다양한 테스트 방법을 제공하여 모든 기능을 검증할 수 있습니다.

## 테스트 파일별 기능

### **1. WebSocket 테스트**

#### `test_single.py`
- **기능**: 각 WebSocket 메시지 타입을 개별적으로 테스트
- **장점**: 문제 발생 시 정확한 원인 파악 가능
- **테스트 항목**:
  - `check_graph`: 그래프 구조 확인
  - `visualize_paths`: 도메인별 경로 시각화
  - `find_popular_paths`: 인기 경로 찾기
  - `save_path`: 경로 저장

```bash
cd test/
python test_single.py
```

#### `test_websocket.py`
- **기능**: 기본 WebSocket 연결 및 간단한 메시지 테스트
- **용도**: 연결 상태 확인용

### **2. 데이터 & 설정**

#### `fixtures/test_data.py`
- **기능**: 모든 테스트 케이스 데이터
- **포함 데이터**:
  - `TEST_CASE_1`: YouTube 음악 검색 + 필터 적용
  - `TEST_CASE_2`: YouTube 음악 검색 + 바로 선택  
  - `ORIGINAL_EXAMPLE`: 좋아요 한 음악 재생목록 열기
  - `MINIMAL_TEST_CASE`: 최소한의 검증용 데이터

#### `test_request.json` & `test_analyze_request.json`
- **기능**: JSON 형태의 테스트 요청 데이터
- **용도**: 수동 테스트 또는 외부 도구에서 사용

#### `test.ipynb`
- **기능**: Jupyter 노트북 기반 대화형 테스트
- **용도**: 개발 중 실시간 테스트 및 디버깅

#### `websocket_test.html`
- **기능**: 브라우저 기반 WebSocket 테스트 도구
- **장점**: 시각적 인터페이스, 실시간 로그 확인
- **사용법**: 브라우저에서 파일 열기 → 연결 → 테스트 버튼 클릭

## 권장 테스트 순서

### **1. 빠른 검증**
```bash
cd test/
python test_single.py
```
**기대 결과**: 5/5 성공


## 테스트 결과 해석

### **성공 사례**
```
전체 결과: 5/5 성공
모든 테스트 통과!
```

### **실패 시 대응**
1. **서버 실행 확인**: `uvicorn app.main:app --port 8000`
2. **환경변수 확인**: `.env` 파일의 API 키들
3. **Neo4j 연결 확인**: 데이터베이스 접속 정보
4. **로그 확인**: 터미널 출력에서 상세 에러 메시지

## 개발자용 테스트

### **새로운 기능 추가 시**
1. `fixtures/test_data.py`에 테스트 데이터 추가
2. `test_single.py`에 새 테스트 케이스 추가  
3. 전체 테스트 실행으로 회귀 테스트

### **WebSocket 메시지 형식**
```json
{
  "type": "메시지_타입",
  "data": {
    // 메시지별 데이터
  }
}
```

지원하는 메시지 타입:
- `save_path`: 경로 저장
- `check_graph`: 그래프 구조 확인
- `visualize_paths`: 도메인별 경로 시각화
- `find_popular_paths`: 인기 경로 찾기