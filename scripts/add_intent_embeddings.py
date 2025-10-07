"""
HAS_STEP 관계에 누락된 intentEmbedding을 추가하는 스크립트

기능:
1. Neo4j 데이터베이스에 연결합니다.
2. (r:ROOT)-[rel:HAS_STEP]->(s:STEP) 관계 중에서
   `rel.intentEmbedding` 속성이 없는 관계를 모두 찾습니다.
3. 각 관계에서 `rel.taskIntent` 값을 가져옵니다.
4. `taskIntent` 값으로 임베딩을 생성합니다.
5. 해당 관계에 `intentEmbedding` 속성을 추가하여 업데이트합니다.
"""

import os
import sys
from dotenv import load_dotenv, find_dotenv

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from langchain_neo4j import Neo4jGraph
    from app.services.embedding_service import generate_embedding
except ImportError as e:
    print(f"필요한 라이브러리를 import하는 데 실패했습니다: {e}")
    print("가상 환경이 활성화되었는지, requirements.txt의 모든 패키지가 설치되었는지 확인하세요.")
    sys.exit(1)

# 환경변수 로드
load_dotenv(find_dotenv())

# NEW DB 연결
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

print("=== 누락된 intentEmbedding 추가 스크립트 시작 ===\n")
print(f"대상 DB: {NEO4J_URI}\n")

# DB 연결
try:
    graph = Neo4jGraph(
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD
    )
    print("✓ DB 연결 성공\n")
except Exception as e:
    print(f"✗ DB 연결 실패: {e}")
    sys.exit(1)

def add_missing_intent_embeddings():
    """
    `intentEmbedding`이 누락된 HAS_STEP 관계를 찾아 임베딩을 추가합니다.
    """
    print("1️⃣ `intentEmbedding`이 누락된 HAS_STEP 관계를 검색 중...")

    # `intentEmbedding`이 없는 HAS_STEP 관계 찾기
    # elementId()를 사용하여 각 관계를 고유하게 식별합니다.
    query_find_missing = """
    MATCH ()-[rel:HAS_STEP]->()
    WHERE rel.intentEmbedding IS NULL AND rel.taskIntent IS NOT NULL
    RETURN elementId(rel) AS relId, rel.taskIntent AS taskIntent
    """
    
    try:
        missing_relations = graph.query(query_find_missing)
    except Exception as e:
        print(f"✗ 관계 검색 중 오류 발생: {e}")
        return

    if not missing_relations:
        print("   ✓ 모든 HAS_STEP 관계에 `intentEmbedding`이 이미 존재합니다. 작업을 종료합니다.\n")
        return

    print(f"   - 총 {len(missing_relations)}개의 관계에서 `intentEmbedding`이 누락되었습니다. 업데이트를 시작합니다.\n")

    updated_count = 0
    failed_count = 0

    for i, rel_data in enumerate(missing_relations):
        rel_id = rel_data.get('relId')
        task_intent = rel_data.get('taskIntent')

        if not rel_id or not task_intent:
            print(f"   - ({i+1}/{len(missing_relations)}) 건너뛰기: 관계 ID 또는 taskIntent가 없습니다.")
            failed_count += 1
            continue

        print(f"   - ({i+1}/{len(missing_relations)}) 처리 중: taskIntent = '{task_intent}'")

        try:
            # 2. taskIntent로 임베딩 생성
            intent_embedding = generate_embedding(task_intent)

            # 3. 관계에 intentEmbedding 속성 업데이트
            query_update = """
            MATCH ()-[rel:HAS_STEP]->()
            WHERE elementId(rel) = $relId
            SET rel.intentEmbedding = $intentEmbedding
            """
            graph.query(query_update, {
                'relId': rel_id,
                'intentEmbedding': intent_embedding
            })
            
            print(f"     ✓ 임베딩 추가 완료")
            updated_count += 1

        except Exception as e:
            print(f"     ✗ 오류 발생: {e}")
            failed_count += 1

    print("\n=== 작업 완료 ===\n")
    print(f"✓ 성공적으로 업데이트된 관계: {updated_count}개")
    if failed_count > 0:
        print(f"✗ 실패 또는 건너뛴 관계: {failed_count}개")
    print()


if __name__ == "__main__":
    response = input("⚠️  이 스크립트는 DB의 HAS_STEP 관계에 `intentEmbedding`을 추가합니다. 계속하시겠습니까? (yes/no): ")
    if response.lower() != 'yes':
        print("작업이 취소되었습니다.")
    else:
        add_missing_intent_embeddings()
