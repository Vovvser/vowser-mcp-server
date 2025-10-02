"""
NEW DB 내의 정보만으로 ROOT와 STEP을 연결하는 스크립트

STEP의 domain 속성을 기반으로 해당 ROOT와 연결합니다.
"""

import os
from dotenv import load_dotenv, find_dotenv
from langchain_neo4j import Neo4jGraph

# 환경변수 로드
load_dotenv(find_dotenv())

# NEW DB 연결
NEW_NEO4J_URI = os.getenv("NEO4J_URI")
NEW_NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEW_NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

print("=== NEW DB 내에서 ROOT-STEP 연결 ===\n")
print(f"NEW DB: {NEW_NEO4J_URI}\n")

# DB 연결
try:
    graph = Neo4jGraph(
        url=NEW_NEO4J_URI,
        username=NEW_NEO4J_USERNAME,
        password=NEW_NEO4J_PASSWORD
    )
    print("✓ NEW DB 연결 성공\n")
except Exception as e:
    print(f"✗ NEW DB 연결 실패: {e}")
    exit(1)


def check_current_state():
    """현재 상태 확인"""
    print("📊 현재 상태 확인...\n")

    # ROOT 개수
    root_count = graph.query("""
        MATCH (r:ROOT)
        RETURN count(r) as count
    """)
    print(f"   ROOT 노드: {root_count[0]['count']}개")

    # STEP 개수
    step_count = graph.query("""
        MATCH (s:STEP)
        RETURN count(s) as count
    """)
    print(f"   STEP 노드: {step_count[0]['count']}개")

    # 기존 HAS_STEP 관계
    has_step = graph.query("""
        MATCH ()-[r:HAS_STEP]->()
        RETURN count(r) as count
    """)
    print(f"   기존 HAS_STEP 관계: {has_step[0]['count']}개")

    # STEP의 domain 분포
    step_domains = graph.query("""
        MATCH (s:STEP)
        RETURN s.domain as domain, count(s) as count
        ORDER BY count DESC
    """)

    print(f"\n   STEP의 domain 분포:")
    for item in step_domains:
        print(f"     • {item['domain']}: {item['count']}개")

    # ROOT domain 목록
    root_domains = graph.query("""
        MATCH (r:ROOT)
        RETURN r.domain as domain
        ORDER BY domain
    """)

    print(f"\n   ROOT domain 목록:")
    for item in root_domains:
        print(f"     • {item['domain']}")

    print()


def connect_steps_to_root():
    """경로의 시작 STEP만 ROOT와 연결"""
    print("🔗 경로 시작점을 ROOT와 연결 중...\n")

    # 먼저 기존 잘못된 HAS_STEP 관계 삭제
    print("   기존 HAS_STEP 관계 삭제 중...")
    graph.query("""
        MATCH ()-[r:HAS_STEP]->()
        DELETE r
    """)
    print("   ✓ 기존 관계 삭제 완료")

    # NEXT_STEP으로 들어오는 관계가 없는 STEP만 ROOT와 연결
    # (= 경로의 시작점)
    result = graph.query("""
        MATCH (s:STEP)
        WHERE NOT ()-[:NEXT_STEP]->(s)
        MATCH (r:ROOT {domain: s.domain})
        WITH r, s
        MERGE (r)-[rel:HAS_STEP]->(s)
        ON CREATE SET
            rel.weight = 1,
            rel.order = 0,
            rel.taskIntent = '경로 시작점',
            rel.createdAt = datetime(),
            rel.lastUpdated = datetime()
        RETURN count(rel) as createdCount
    """)

    created = result[0]['createdCount'] if result else 0
    print(f"   ✓ {created}개의 경로 시작점을 ROOT와 연결 완료\n")

    return created


def verify_results():
    """결과 확인"""
    print("📊 연결 결과 확인...\n")

    # ROOT별 연결된 STEP 개수
    root_stats = graph.query("""
        MATCH (r:ROOT)
        OPTIONAL MATCH (r)-[rel:HAS_STEP]->(s:STEP)
        RETURN r.domain as domain,
               count(s) as stepCount
        ORDER BY stepCount DESC
    """)

    print("   ROOT별 연결된 STEP 개수:")
    for stat in root_stats:
        print(f"     • {stat['domain']}: {stat['stepCount']}개")

    # 연결되지 않은 STEP 확인
    orphan_steps = graph.query("""
        MATCH (s:STEP)
        WHERE NOT ()-[:HAS_STEP]->(s)
        RETURN s.domain as domain, count(s) as count
    """)

    if orphan_steps and orphan_steps[0]['count'] > 0:
        print(f"\n   ⚠ 연결되지 않은 STEP:")
        for item in orphan_steps:
            print(f"     • {item['domain']}: {item['count']}개")

        # 연결되지 않은 이유 확인
        print(f"\n   연결 실패 원인 분석:")
        missing_roots = graph.query("""
            MATCH (s:STEP)
            WHERE NOT ()-[:HAS_STEP]->(s)
            WITH DISTINCT s.domain as stepDomain
            OPTIONAL MATCH (r:ROOT {domain: stepDomain})
            WHERE r IS NULL
            RETURN stepDomain
        """)

        if missing_roots:
            print(f"     • 다음 domain의 ROOT가 없음:")
            for item in missing_roots:
                if item['stepDomain']:
                    print(f"       - {item['stepDomain']}")

    # 예시 경로
    sample = graph.query("""
        MATCH (r:ROOT)-[has:HAS_STEP]->(s:STEP)
        RETURN r.domain as domain,
               s.description as stepDescription
        LIMIT 3
    """)

    if sample:
        print(f"\n   📌 연결 예시:")
        for item in sample:
            print(f"     • {item['domain']} → {item['stepDescription']}")


def main():
    try:
        # 현재 상태 확인
        check_current_state()

        # 연결 확인
        response = input("STEP을 ROOT와 연결하시겠습니까? (yes/no): ")
        if response.lower() != 'yes':
            print("취소됨.")
            return

        print()

        # 연결 실행
        created = connect_steps_to_root()

        # 결과 확인
        verify_results()

        print("\n✅ 완료!\n")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
