# Vowser MCP Server

FastAPI-based WebSocket server that serves as an MCP (Model Context Protocol) server for web crawling and path analysis. The server integrates with Neo4j for graph-based storage of web navigation paths and uses LangChain for AI-powered content analysis.

## Features

- **WebSocket Communication**: Real-time bidirectional communication via WebSocket
- **Neo4j Graph Database**: Stores web navigation paths as graph structures
- **AI-Powered Analysis**: LangChain integration for semantic content analysis
- **Path Search**: Natural language search for navigation paths using vector embeddings
- **Popular Path Tracking**: Usage-based path recommendations with weighted relationships

## Quick Start

### Environment Setup
```bash
# Install dependencies (recommended)
uv sync

# Alternative: pip install
pip install -r requirements.txt
```

### Configuration
Create a `.env` file:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
GOOGLE_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_key
```

### Running the Server
```bash
# Start the FastAPI server
uvicorn app.main:app --port 8000 --reload

# Alternative: using Python module
python -m uvicorn app.main:app --port 8000 --reload
```

### Testing
```bash
# Run comprehensive WebSocket tests
cd test/
python test_single.py

# Expected output: "전체 결과: 5/5 성공"
```

## API Documentation

### WebSocket Connection
- **URL**: `ws://localhost:8000/ws`
- **Protocol**: JSON-based message exchange

### Supported Message Types

#### 1. Save Navigation Path
```json
{
  "type": "save_path",
  "data": {
    "sessionId": "session-123",
    "startCommand": "유튜브에서 음악 찾기",
    "completePath": [...]
  }
}
```

#### 2. Search Paths
```json
{
  "type": "search_path",
  "data": {
    "query": "유튜브에서 좋아요 한 음악 재생목록 여는 방법",
    "limit": 3,
    "domain_hint": "youtube.com"
  }
}
```

#### 3. Check Graph Structure
```json
{
  "type": "check_graph",
  "data": {}
}
```

#### 4. Find Popular Paths
```json
{
  "type": "find_popular_paths",
  "data": {
    "domain": "youtube.com",
    "limit": 10
  }
}
```

#### 5. Visualize Paths
```json
{
  "type": "visualize_paths",
  "data": {
    "domain": "youtube.com"
  }
}
```

## Architecture

```
[vowser-client] <=> [vowser-backend] <=> [vowser-mcp-server]
```

The MCP server serves as the "brain" of the system, handling:
- Web navigation path storage and analysis
- AI-powered semantic search
- Graph-based path recommendations
- Usage pattern analysis

### Core Components

- **FastAPI WebSocket Server** (`app/main.py`): Single `/ws` endpoint for real-time communication
- **Neo4j Graph Database** (`app/services/neo4j_service.py`): Graph structures for navigation paths
- **AI Services** (`app/services/`): LangChain integration for content analysis and embeddings
- **Data Models** (`app/models/path.py`): Pydantic models for data validation

### Graph Schema

- **ROOT**: Domain-level nodes (e.g., youtube.com)
- **PAGE**: Interactive elements with selectors and embeddings
- **PATH**: Complete navigation sequences with semantic search capability
- **Relationships**: HAS_PAGE, NAVIGATES_TO, NAVIGATES_TO_CROSS_DOMAIN, CONTAINS

## Development

### Project Structure
```
vowser-mcp-server/
├── app/                    # Main application
│   ├── main.py            # FastAPI WebSocket server
│   ├── models/            # Pydantic models
│   └── services/          # Business logic
├── docs/                  # Documentation
├── test/                  # Test files
└── requirements.txt       # Dependencies
```

### Testing Strategy
- `test_single.py`: Comprehensive WebSocket message testing
- All tests should pass with "5/5 성공" result
- Integration tests for Neo4j functionality

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Related Projects

- **vowser-backend**: Kotlin/Spring Boot central API gateway
- **vowser-client**: Kotlin Multiplatform user-facing application

For more detailed information, see [CLAUDE.md](CLAUDE.md).