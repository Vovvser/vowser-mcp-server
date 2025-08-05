# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **vowser-mcp-server** - a FastAPI-based WebSocket server that serves as an MCP (Model Context Protocol) server for web crawling and path analysis. The server integrates with Neo4j for graph-based storage of web navigation paths and uses LangChain for AI-powered content analysis.

## Development Commands

### Environment Setup
```bash
# Install dependencies (use uv - this project uses uv.lock)
uv sync

# Alternative: pip install
pip install -r requirements.txt
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

# Run basic WebSocket connection test
python test_websocket.py

# Interactive testing via Jupyter
jupyter notebook test.ipynb

# Browser-based WebSocket testing
# Open test/websocket_test.html in browser
```

### Database Operations
```bash
# The server automatically connects to Neo4j on startup
# Check connection status in server logs: "Neo4j Service: Database connection successful."
```

## Architecture

### Core Components

**FastAPI WebSocket Server** (`app/main.py`):
- Single WebSocket endpoint at `/ws` for real-time communication
- Handles multiple message types: `save_path`, `check_graph`, `visualize_paths`, `find_popular_paths`
- JSON-based message protocol with structured request/response format

**Neo4j Graph Database** (`app/services/neo4j_service.py`):
- Stores web navigation paths as graph structures
- Node types: ROOT (domains), PAGE (clickable elements), PAGE_ANALYSIS, SECTION, ELEMENT
- Relationship types: HAS_PAGE, NAVIGATES_TO, NAVIGATES_TO_CROSS_DOMAIN
- Weighted relationships track usage frequency and popularity

**AI Services** (`app/services/`):
- `embedding_service.py`: Generates semantic embeddings for UI elements
- `ai_module.py`: LangChain integration for content analysis
- Uses Google Gemini and OpenAI models for semantic understanding

**Data Models** (`app/models/path.py`):
- Pydantic models for path data validation
- Structured representation of user navigation sequences with semantic metadata

### Message Flow

1. **Client** sends WebSocket message to `/ws`
2. **Server** parses message type and routes to appropriate service
3. **Neo4j Service** processes data (save paths, query graph structure)
4. **AI Services** enhance data with embeddings and semantic analysis
5. **Server** returns structured JSON response to client

### Graph Schema

- **ROOT**: Domain-level nodes (e.g., youtube.com)
- **PAGE**: Interactive elements with selectors, text labels, and embeddings
- **Relationships**: Weighted connections tracking user navigation patterns
- **Cross-domain navigation**: Special relationship type for domain transitions

## Environment Variables

Required `.env` file:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
GOOGLE_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_key
```

## WebSocket API

The server expects JSON messages with this structure:
```json
{
  "type": "message_type",
  "data": { /* message-specific data */ }
}
```

Supported message types:
- `save_path`: Store user navigation sequences
- `check_graph`: Get graph statistics
- `visualize_paths`: Query domain-specific paths
- `find_popular_paths`: Get weighted popular navigation routes

Detailed API documentation: `docs/WEBSOCKET_API.md`

## Code Quality Guidelines

### Context7 Integration
Always use Context7 to reference up-to-date library documentation when working with external dependencies. This ensures:
- Version-compatible code that works with the specific library versions in this project
- Best practices aligned with current documentation
- Proper API usage patterns

Example workflow:
1. Before modifying FastAPI, LangChain, Neo4j, or Pydantic code, query Context7 for the latest documentation
2. Verify compatibility with versions specified in `pyproject.toml` and `requirements.txt`
3. Use recommended patterns from official documentation rather than outdated examples

Key libraries to always check:
- FastAPI (WebSocket implementation)
- LangChain (AI service integration)
- Neo4j Python driver (graph operations)
- Pydantic (data validation models)

## Learning Examples

The `learn/` folder contains comprehensive Knowledge Graph and RAG implementation examples that demonstrate advanced patterns relevant to this project:

### Available Examples
- `KG_P2_01_news_analysis.ipynb`: News data analysis using Neo4j + LangChain
  - Shows how to extract entities from text using LLM
  - Demonstrates graph construction with semantic relationships
  - Implements hybrid RAG (vector search + graph traversal)
  - Text2Cypher for natural language querying

- `KG_P2_02_etf_recommendation.ipynb`: ETF recommendation system
  - Entity extraction from structured financial data
  - Complex graph ontology with multiple node types
  - Full-text search indexing with CJK analyzer for Korean
  - Few-shot prompting for Text2Cypher
  - Semantic similarity-based example selection

- `KG_P2_03_10K_report.ipynb`: Corporate document analysis
- `KG_P2_04_law_qa.ipynb`: Legal Q&A system

### Key Patterns to Reference
When implementing new features or debugging existing functionality, refer to these examples for:

1. **Entity Extraction**: See news analysis notebook for LLM-based entity extraction patterns
2. **Graph Schema Design**: ETF notebook shows comprehensive ontology design
3. **Vector Indexing**: Both examples demonstrate proper vector embedding setup
4. **Text2Cypher**: Advanced prompting techniques with few-shot examples
5. **Hybrid RAG**: Combining vector similarity with graph traversal
6. **Error Handling**: Robust error handling in graph operations
7. **Performance Optimization**: Batch processing and indexing strategies

### Usage Guidelines
- Study these patterns before implementing similar functionality
- Adapt the ontology and relationship patterns to web navigation domain
- Use the Text2Cypher prompting strategies for natural language queries
- Reference the vector indexing setup for embedding-based search

## Testing Strategy

- `test_single.py`: Comprehensive individual message type testing
- `test/fixtures/test_data.py`: Centralized test data with multiple YouTube navigation scenarios
- `websocket_test.html`: Browser-based visual testing interface
- Always test with `python test_single.py` after changes - expect "5/5 성공"