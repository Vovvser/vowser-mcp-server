# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a vowser-mcp-server project—a Neo4j GraphRAG-based MCP (Model Context Protocol) server designed to automatically structure websites for efficient navigation, particularly for users who have difficulty using hands.

## Development Environment Setup

### Package Management
This project uses UV package manager. Commands:
```bash
# Install dependencies
uv sync

# Add new dependency
uv add <package>

# Activate virtual environment
source .venv/bin/activate

# Run the main script
python main.py
```

### Environment Variables
Create a `.env` file with:
```
NEO4J_URL=<your_neo4j_url>
NEO4J_USERNAME=<your_username>
NEO4J_PASSWORD=<your_password>
```

## Architecture

### Key Technologies
- **Database**: Neo4j (Graph database for storing website structures)
- **AI/LLM**: LangChain with support for OpenAI and Google Genai
- **Package Manager**: UV (Python 3.11)
- **Web Automation**: Playwright (planned)
- **HTML Parsing**: BeautifulSoup4 (planned)
- **Framework**: FastAPI (planned for HTTP REST API)

### Project Structure
- `main.py`: Entry point (currently placeholder)
- `test/test.ipynb`: Jupyter notebook for Neo4j connection testing
- `.claude/`: Project documentation
  - `PRD.md`: Comprehensive product requirements document
  - `plan.md`: Implementation planning (in progress)

### Planned Architecture (from PRD)
The system will have:
1. **Hybrid API Layer**: Both MCP Protocol and REST API support
2. **Service Layer**: Crawling, Parsing, Structuring, and LangChain services
3. **Data Layer**: Neo4j for graph storage, Redis for caching (planned)

### Neo4j Schema (Planned)
- **Nodes**: ROOT, SUBROOT, DEPTH, SECTION, ELEMENT, CONTENT
- **Relationships**: HAS_SECTION, HAS_ELEMENT, HAS_CONTENT, LINKS_TO, etc.
- Special handling for paginated content with sampling strategies

## Testing

Currently using Jupyter notebooks for testing:
```bash
# Run test notebook
jupyter notebook test/test.ipynb
```

The test notebook includes:
- Neo4j connection testing
- Database reset functionality
- Basic node count queries

## Common Development Tasks

### Database Operations
```python
# Connect to Neo4j
from langchain_neo4j import Neo4jGraph
from dotenv import load_dotenv
import os

load_dotenv()
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URL"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD")
)

# Reset database (from test notebook)
# See test/test.ipynb for reset_database() function
```

### Key Features to Implement
1. **Web Crawling**: Playwright-based dynamic content loading
2. **Structure Analysis**: BeautifulSoup for HTML parsing
3. **Pagination Handling**: Smart sampling strategies for large paginated content
4. **API Endpoints**: FastAPI routes for crawling, status, structure queries
5. **MCP Protocol**: JSON-RPC message handling

## Important Considerations

### Pagination Strategy
The system uses adaptive crawling strategies based on total pages:
- ≤5 pages: Crawl all
- 6-20 pages: Representative sampling
- >20 pages: Smart sampling with first, middle, and last pages

### Performance Requirements
- Single page processing: <10 seconds
- Neo4j query response: <100ms
- API response time: <500ms (cached data)
- Concurrent crawling: Up to 10 tasks

### Security
- Rate limiting implementation required
- robots.txt compliance
- Sensitive information filtering
- CORS policy configuration

## Development Guidelines & Workflow

### MCP Tools Usage
**MANDATORY**: Always leverage these MCP tools effectively:
- **context7**: For retrieving up-to-date library documentation and code examples
- **zen mcp**: For enhanced AI capabilities including deep thinking, analysis, debugging, and consensus building

### Documentation Standards
**MANDATORY**: All technical documentation must follow these standards:

#### File Organization
- **Technical Documentation**: All detailed technical docs go in the `docs/` folder
- **Project Documentation**: Keep CLAUDE.md and plan.md in `.claude/` folder, PRD.md in `docs/` folder
- **User Documentation**: README.md and user guides in the root directory

#### Documentation Types and Location
- **Architecture & Design**: `docs/architecture/` or `docs/` (e.g., `async-architecture.md`)
- **API Documentation**: `docs/api/` or auto-generated from code
- **Implementation Guides**: `docs/implementation/` or `docs/` (e.g., `crawling-guide.md`)
- **Performance & Optimization**: `docs/performance/` or `docs/` (e.g., `optimization-guide.md`)
- **Security Guidelines**: `docs/security/` or `docs/` (e.g., `security-practices.md`)

#### File Naming Convention
- Use kebab-case: `async-architecture.md`, `crawling-guide.md`
- Be descriptive: `neo4j-schema-design.md` instead of `database.md`
- Include version when needed: `api-v1-specification.md`

#### Content Structure
1. **Title**: Clear, descriptive H1 header
2. **Overview**: Brief purpose and scope
3. **Numbered Sections**: Logical flow with clear headings
4. **Code Examples**: Practical, runnable code blocks
5. **Cross-references**: Link to related PRD sections and other docs

#### Creation Process
**REQUIRED**: When creating new documentation:
1. Always place in `docs/` folder unless it's core project documentation
2. Follow the naming convention and structure guidelines
3. Update this CLAUDE.md file if new documentation patterns emerge
4. Ensure consistency with PRD.md requirements and specifications

### Documentation Consistency
**CRITICAL**: Before making any changes to the codebase:
1. Always check if your changes align with the direction outlined in this CLAUDE.md file
2. If your implementation differs from the guidance here, **MUST** update CLAUDE.md accordingly
3. Ensure consistency between code changes and documentation
4. **NEW**: Place all technical documentation in the `docs/` folder following the standards above

### Reference Documents
**MANDATORY**: Always consult these documents before starting work:
- **PRD.md** (`docs/PRD.md`): Comprehensive product requirements and technical specifications
- **taskList** (coming soon): Current task priorities and implementation status
- **plan.md** (`.claude/plan.md`): Implementation planning and progress tracking

### New Task Workflow
**REQUIRED PROCESS** for any new work:
1. **Check existing documentation**: Verify if the task is already defined in PRD.md or taskList
2. **If task is NOT documented**:
   - **STOP** and ask the user: "This task is not in the PRD or taskList. Should I add it?"
   - Wait for user approval
   - **Only after approval**: Add the task to both PRD.md and taskList
3. **Then proceed** with implementation

### Task Execution Order
1. Consult PRD.md for requirements and specifications
2. Check taskList for current priorities
3. Use context7 for library documentation
4. Use zen mcp for complex analysis and decision-making
5. Implement with documentation updates
6. Verify CLAUDE.md alignment