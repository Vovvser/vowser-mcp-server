# Spring Boot Integration Guide

## 1. Dependencies (build.gradle)

```gradle
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-websocket'
    implementation 'org.java-websocket:Java-WebSocket:1.5.3'
    implementation 'com.fasterxml.jackson.core:jackson-databind'
}
```

## 2. WebSocket Client Service

```java
@Service
@Slf4j
public class VowserMcpClient {
    
    private final String WS_URI = "ws://localhost:8000/ws";
    private WebSocketClient webSocketClient;
    private final ObjectMapper objectMapper = new ObjectMapper();
    private CompletableFuture<String> responseFuture;
    
    @PostConstruct
    public void connect() {
        try {
            webSocketClient = new WebSocketClient(new URI(WS_URI)) {
                @Override
                public void onOpen(ServerHandshake handshake) {
                    log.info("Connected to Vowser MCP Server");
                }
                
                @Override
                public void onMessage(String message) {
                    log.info("Received: {}", message);
                    if (responseFuture != null) {
                        responseFuture.complete(message);
                    }
                }
                
                @Override
                public void onClose(int code, String reason, boolean remote) {
                    log.info("Connection closed: {}", reason);
                }
                
                @Override
                public void onError(Exception ex) {
                    log.error("WebSocket error", ex);
                }
            };
            
            webSocketClient.connectBlocking();
        } catch (Exception e) {
            log.error("Failed to connect", e);
        }
    }
    
    // 경로 저장
    public CompletableFuture<SavePathResponse> savePath(PathData pathData) {
        Map<String, Object> message = Map.of(
            "type", "save_path",
            "data", pathData
        );
        
        return sendMessage(message)
            .thenApply(response -> parseResponse(response, SavePathResponse.class));
    }
    
    // 자연어 경로 검색
    public CompletableFuture<SearchPathResponse> searchPath(String query, int limit) {
        Map<String, Object> message = Map.of(
            "type", "search_path",
            "data", Map.of(
                "query", query,
                "limit", limit
            )
        );
        
        return sendMessage(message)
            .thenApply(response -> parseResponse(response, SearchPathResponse.class));
    }
    
    // 그래프 통계
    public CompletableFuture<GraphStatsResponse> checkGraph() {
        Map<String, Object> message = Map.of("type", "check_graph");
        
        return sendMessage(message)
            .thenApply(response -> parseResponse(response, GraphStatsResponse.class));
    }
    
    // 인덱스 생성
    public CompletableFuture<IndexResponse> createIndexes() {
        Map<String, Object> message = Map.of("type", "create_indexes");
        
        return sendMessage(message)
            .thenApply(response -> parseResponse(response, IndexResponse.class));
    }
    
    // 오래된 경로 정리
    public CompletableFuture<CleanupResponse> cleanupPaths() {
        Map<String, Object> message = Map.of("type", "cleanup_paths");
        
        return sendMessage(message)
            .thenApply(response -> parseResponse(response, CleanupResponse.class));
    }
    
    private CompletableFuture<String> sendMessage(Map<String, Object> message) {
        try {
            responseFuture = new CompletableFuture<>();
            String json = objectMapper.writeValueAsString(message);
            webSocketClient.send(json);
            return responseFuture;
        } catch (Exception e) {
            return CompletableFuture.failedFuture(e);
        }
    }
    
    private <T> T parseResponse(String json, Class<T> clazz) {
        try {
            return objectMapper.readValue(json, clazz);
        } catch (Exception e) {
            throw new RuntimeException("Failed to parse response", e);
        }
    }
    
    @PreDestroy
    public void disconnect() {
        if (webSocketClient != null) {
            webSocketClient.close();
        }
    }
}
```

## 3. DTOs

```java
// 요청 DTOs
@Data
@Builder
public class PathData {
    private String sessionId;
    private String startCommand;
    private List<PathStep> completePath;
}

@Data
@Builder
public class PathStep {
    private int order;
    private String url;
    private LocationData locationData;
    private SemanticData semanticData;
}

@Data
public class LocationData {
    private String primarySelector;
    private List<String> fallbackSelectors;
    private String anchorPoint;
    private String relativePathFromAnchor;
    private Map<String, Object> elementSnapshot;
}

@Data
public class SemanticData {
    private List<String> textLabels;
    private Map<String, Object> contextText;
    private Map<String, Object> pageInfo;
    private String actionType;
}

// 응답 DTOs
@Data
public class SearchPathResponse {
    private String type;
    private String status;
    private SearchPathData data;
}

@Data
public class SearchPathData {
    private String query;
    private List<MatchedPath> matchedPaths;
    private SearchMetadata searchMetadata;
}

@Data
public class MatchedPath {
    private String pathId;
    private double relevanceScore;
    private int totalWeight;
    private String lastUsed;
    private Double estimatedTime;
    private List<PathStepResponse> steps;
}

@Data
public class PathStepResponse {
    private int order;
    private String type;
    private String pageId;
    private String domain;
    private String url;
    private String selector;
    private String anchorPoint;
    private String action;
    private List<String> textLabels;
}
```

## 4. Controller 예제

```java
@RestController
@RequestMapping("/api/vowser")
@RequiredArgsConstructor
public class VowserController {
    
    private final VowserMcpClient vowserClient;
    
    // 경로 저장
    @PostMapping("/paths")
    public CompletableFuture<SavePathResponse> savePath(@RequestBody PathData pathData) {
        return vowserClient.savePath(pathData);
    }
    
    // 자연어 검색
    @GetMapping("/paths/search")
    public CompletableFuture<SearchPathResponse> searchPath(
            @RequestParam String query,
            @RequestParam(defaultValue = "3") int limit) {
        return vowserClient.searchPath(query, limit);
    }
    
    // 그래프 통계
    @GetMapping("/graph/stats")
    public CompletableFuture<GraphStatsResponse> getGraphStats() {
        return vowserClient.checkGraph();
    }
    
    // 인덱스 생성 (관리자용)
    @PostMapping("/admin/indexes")
    public CompletableFuture<IndexResponse> createIndexes() {
        return vowserClient.createIndexes();
    }
    
    // 경로 정리 (스케줄러용)
    @PostMapping("/admin/cleanup")
    public CompletableFuture<CleanupResponse> cleanupPaths() {
        return vowserClient.cleanupPaths();
    }
}
```

## 5. 사용 예제

```java
@Service
@RequiredArgsConstructor
public class PathService {
    
    private final VowserMcpClient vowserClient;
    
    // 사용자가 브라우저에서 수집한 경로 저장
    public void saveUserPath(BrowserPathData browserData) {
        PathData pathData = PathData.builder()
            .sessionId(browserData.getSessionId())
            .startCommand("유튜브에서 음악 검색")
            .completePath(convertToPathSteps(browserData))
            .build();
            
        vowserClient.savePath(pathData)
            .thenAccept(response -> {
                log.info("Path saved: {}", response.getStatus());
            });
    }
    
    // 자연어로 경로 검색
    public CompletableFuture<List<NavigationPath>> searchNavigationPaths(String userQuery) {
        return vowserClient.searchPath(userQuery, 5)
            .thenApply(response -> {
                return response.getData().getMatchedPaths().stream()
                    .map(this::convertToNavigationPath)
                    .collect(Collectors.toList());
            });
    }
    
    // 매월 실행되는 정리 스케줄러
    @Scheduled(cron = "0 0 2 1 * ?") // 매월 1일 새벽 2시
    public void monthlyCleanup() {
        vowserClient.cleanupPaths()
            .thenAccept(response -> {
                log.info("Cleanup completed: {} paths cleaned", 
                    response.getData().getDeletedPaths());
            });
    }
}
```

## 6. WebSocket 연결 관리 (고급)

```java
@Component
@Slf4j
public class VowserConnectionManager {
    
    private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
    private VowserMcpClient client;
    private volatile boolean isConnected = false;
    
    @PostConstruct
    public void init() {
        // 연결 상태 모니터링 및 재연결
        scheduler.scheduleWithFixedDelay(this::checkConnection, 0, 30, TimeUnit.SECONDS);
    }
    
    private void checkConnection() {
        if (!isConnected || !client.isOpen()) {
            log.info("Attempting to reconnect to Vowser MCP Server...");
            try {
                client.reconnect();
                isConnected = true;
            } catch (Exception e) {
                log.error("Reconnection failed", e);
                isConnected = false;
            }
        }
    }
    
    @EventListener(ApplicationReadyEvent.class)
    public void onApplicationReady() {
        // 앱 시작 시 인덱스 생성 확인
        client.createIndexes()
            .thenAccept(response -> {
                log.info("Vowser indexes ready: {}", response.getData().getMessage());
            });
    }
}
```

## 7. 환경별 설정

```yaml
# application.yml
vowser:
  mcp:
    url: ${VOWSER_MCP_URL:ws://localhost:8000/ws}
    connection-timeout: 5000
    response-timeout: 10000
    
# application-prod.yml
vowser:
  mcp:
    url: ws://vowser-mcp-server:8000/ws
```

## 8. 통합 테스트

```java
@SpringBootTest
@AutoConfigureMockMvc
class VowserIntegrationTest {
    
    @Autowired
    private VowserMcpClient vowserClient;
    
    @Test
    void testSearchPath() {
        // Given
        String query = "유튜브 음악 검색하는 방법";
        
        // When
        SearchPathResponse response = vowserClient.searchPath(query, 3)
            .get(5, TimeUnit.SECONDS);
        
        // Then
        assertThat(response.getStatus()).isEqualTo("success");
        assertThat(response.getData().getMatchedPaths()).isNotEmpty();
    }
}
```

## 주의사항

1. **연결 관리**: WebSocket 연결이 끊어질 수 있으므로 재연결 로직 필요
2. **비동기 처리**: CompletableFuture로 비동기 처리 권장
3. **에러 처리**: timeout, connection error 등 처리 필요
4. **메시지 큐**: 동시 요청이 많을 경우 메시지 큐 고려

## 사용 시나리오

1. **브라우저 확장 프로그램** → Spring Boot 서버 → **Vowser MCP Server**
2. 사용자가 "유튜브 음악 검색 방법" 입력
3. Spring Boot가 search_path API 호출
4. 검색된 경로를 사용자에게 반환
5. 사용자가 경로 사용 시 자동으로 가중치 증가