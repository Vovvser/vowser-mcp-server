# UV 패키지 관리자
## UV 설치
### macOS and Linux

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows
```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

# Neo4j GraphRAG 프로젝트 설정
## 1. 프로젝트 디렉토리 생성 및 초기화

```shell
uv init vowser-mcp-server
cd vowser-mcp-server
```

## 2. 가상환경 생성

```shell
# Python 3.12 기반 가상환경 생성
uv venv .venv --python=3.12

# 가상환경 활성화 (macOS/Linux)
source .venv/bin/activate

# 가상환경 비활성화
deactivate
```

## 3. 필요한 패키지 설치
```shell
# langchain-neo4j 설치
uv add langchain-neo4j

# 추가 패키지
uv add python-dotenv langchain langchain-openai langchain-google-genai
```
