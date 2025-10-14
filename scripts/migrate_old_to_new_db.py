"""
Neo4j 데이터 마이그레이션 스크립트

OLD DB (OLD_NEO4J_URI):
- ROOT 노드: 도메인 정보
- PAGE 노드: 클릭 가능한 요소
- PATH 노드: 완전한 경로 정보
- 관계: ROOT-[HAS_PAGE]->PAGE, PAGE-[NAVIGATES_TO]->PAGE, PATH-[CONTAINS]->PAGE

NEW DB (NEO4J_URI):
- ROOT 노드: 도메인 정보 (embedding, visitCount 추가)
- STEP 노드: 개별 액션 (PAGE 확장)
- 관계: ROOT-[HAS_STEP {taskIntent}]->STEP, STEP-[NEXT_STEP]->STEP

마이그레이션 전략:
1. OLD DB에서 ROOT, PAGE, PATH 노드 읽기
2. NEW DB에 ROOT 노드 생성 (embedding, visitCount 추가)
3. PAGE → STEP 변환 (필드 매핑)
4. PATH → HAS_STEP + NEXT_STEP 관계 생성
"""

import os
import sys
import hashlib
from dotenv import load_dotenv, find_dotenv
from typing import List, Dict, Any

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_neo4j import Neo4jGraph
from app.services.embedding_service import generate_embedding

# 환경변수 로드
load_dotenv(find_dotenv())

# OLD DB 연결
OLD_NEO4J_URI = os.getenv("OLD_NEO4J_URI")
OLD_NEO4J_USERNAME = os.getenv("OLD_NEO4J_USERNAME") or os.getenv("NEO4J_USERNAME")
OLD_NEO4J_PASSWORD = os.getenv("OLD_NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")

# NEW DB 연결
NEW_NEO4J_URI = os.getenv("NEO4J_URI")
NEW_NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEW_NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

print("=== Neo4j 데이터 마이그레이션 시작 ===\n")
print(f"OLD DB: {OLD_NEO4J_URI}")
print(f"NEW DB: {NEW_NEO4J_URI}\n")

# 두 DB 연결
try:
    old_graph = Neo4jGraph(
        url=OLD_NEO4J_URI,
        username=OLD_NEO4J_USERNAME,
        password=OLD_NEO4J_PASSWORD
    )
    print("✓ OLD DB 연결 성공")
except Exception as e:
    print(f"✗ OLD DB 연결 실패: {e}")
    sys.exit(1)

try:
    new_graph = Neo4jGraph(
        url=NEW_NEO4J_URI,
        username=NEW_NEO4J_USERNAME,
        password=NEW_NEO4J_PASSWORD
    )
    print("✓ NEW DB 연결 성공\n")
except Exception as e:
    print(f"✗ NEW DB 연결 실패: {e}")
    sys.exit(1)


def normalize_domain(domain: str) -> str:
    """
    서브도메인을 메인 도메인으로 정규화
    예: finance.naver.com -> naver.com
        www.youtube.com -> youtube.com
    """
    if not domain:
        return domain

    # 특수 케이스: gov.kr, co.kr 등
    special_tlds = ['.gov.kr', '.co.kr', '.or.kr', '.ac.kr', '.go.kr']
    for tld in special_tlds:
        if domain.endswith(tld):
            parts = domain.replace(tld, '').split('.')
            if len(parts) > 0:
                return parts[-1] + tld
            return domain

    # 일반적인 경우: 마지막 두 부분만 사용
    parts = domain.split('.')
    if len(parts) >= 2:
        return '.'.join(parts[-2:])

    return domain


def create_step_id(url: str, selector: str, action: str = "click") -> str:
    """STEP ID 생성 (고유성 보장)"""
    key = f"{url}_{selector}_{action}"
    return hashlib.md5(key.encode()).hexdigest()


def migrate_root_nodes():
    """OLD DB의 ROOT 노드를 NEW DB로 마이그레이션"""
    print("1️⃣  ROOT 노드 마이그레이션 중...")

    # OLD DB에서 ROOT 노드 가져오기
    old_roots = old_graph.query("""
        MATCH (r:ROOT)
        RETURN r.domain as domain,
               r.baseURL as baseURL,
               r.lastVisited as lastVisited
    """)

    migrated_count = 0

    for root_data in old_roots:
        domain = root_data.get('domain', '')
        base_url = root_data.get('baseURL', f"https://{domain}")
        display_name = domain.replace('.com', '').replace('.', ' ').title()

        # 임베딩 생성
        embedding = generate_embedding(f"{domain} {display_name}")

        # NEW DB에 ROOT 노드 생성
        new_graph.query("""
            MERGE (r:ROOT {domain: $domain})
            ON CREATE SET
                r.baseURL = $baseURL,
                r.displayName = $displayName,
                r.embedding = $embedding,
                r.visitCount = 0,
                r.lastVisited = $lastVisited
            ON MATCH SET
                r.visitCount = r.visitCount + 1
            RETURN r
        """, {
            'domain': domain,
            'baseURL': base_url,
            'displayName': display_name,
            'embedding': embedding,
            'lastVisited': root_data.get('lastVisited')
        })

        migrated_count += 1

    print(f"   ✓ ROOT 노드 {migrated_count}개 마이그레이션 완료\n")
    return migrated_count


def migrate_page_to_step():
    """OLD DB의 PAGE 노드를 NEW DB의 STEP 노드로 변환"""
    print("2️⃣  PAGE → STEP 노드 변환 중...")

    # OLD DB에서 PAGE 노드 가져오기
    old_pages = old_graph.query("""
        MATCH (p:PAGE)
        RETURN p.pageId as pageId,
               p.url as url,
               p.domain as domain,
               p.primarySelector as primarySelector,
               p.fallbackSelectors as fallbackSelectors,
               p.anchorPoint as anchorPoint,
               p.relativePathFromAnchor as relativePathFromAnchor,
               p.textLabels as textLabels,
               p.contextText as contextText,
               p.actionType as actionType,
               p.embedding as embedding,
               p.lastUpdated as lastUpdated
    """)

    migrated_count = 0

    for page_data in old_pages:
        page_id = page_data.get('pageId')
        url = page_data.get('url', '')
        domain = normalize_domain(page_data.get('domain', ''))
        primary_selector = page_data.get('primarySelector', '')
        fallback_selectors = page_data.get('fallbackSelectors', [])

        # 셀렉터 배열 생성
        selectors = [primary_selector] + (fallback_selectors if fallback_selectors else [])

        # action 매핑 (actionType이 없으면 'click'으로 기본값)
        action_type = page_data.get('actionType', 'click')
        action = 'click' if action_type in ['click', 'navigate'] else action_type

        # STEP ID 생성
        step_id = create_step_id(url, primary_selector, action)

        # textLabels 처리
        text_labels = page_data.get('textLabels', [])
        if isinstance(text_labels, str):
            text_labels = [text_labels]

        # description 생성
        description = text_labels[0] if text_labels else f"{action} on {domain}"

        # 임베딩 (기존 임베딩이 있으면 사용, 없으면 생성)
        embedding = page_data.get('embedding')
        if not embedding or len(embedding) == 0:
            embedding_text = f"{description} {' '.join(text_labels)}"
            embedding = generate_embedding(embedding_text)

        # NEW DB에 STEP 노드 생성
        new_graph.query("""
            MERGE (s:STEP {stepId: $stepId})
            SET s.url = $url,
                s.domain = $domain,
                s.selectors = $selectors,
                s.anchorPoint = $anchorPoint,
                s.relativePathFromAnchor = $relativePathFromAnchor,
                s.action = $action,
                s.isInput = false,
                s.shouldWait = false,
                s.description = $description,
                s.textLabels = $textLabels,
                s.contextText = $contextText,
                s.embedding = $embedding,
                s.createdAt = $lastUpdated,
                s.lastUsed = $lastUpdated,
                s.usageCount = 1,
                s.successRate = 1.0,
                s.oldPageId = $oldPageId
            RETURN s
        """, {
            'stepId': step_id,
            'url': url,
            'domain': domain,
            'selectors': selectors,
            'anchorPoint': page_data.get('anchorPoint'),
            'relativePathFromAnchor': page_data.get('relativePathFromAnchor'),
            'action': action,
            'description': description,
            'textLabels': text_labels,
            'contextText': page_data.get('contextText'),
            'embedding': embedding,
            'lastUpdated': page_data.get('lastUpdated'),
            'oldPageId': page_id
        })

        migrated_count += 1

    print(f"   ✓ STEP 노드 {migrated_count}개 생성 완료\n")
    return migrated_count


def migrate_navigates_to_relationships():
    """OLD DB의 NAVIGATES_TO 관계를 NEW DB의 NEXT_STEP으로 변환"""
    print("3️⃣  NAVIGATES_TO → NEXT_STEP 관계 변환 중...")

    # OLD DB에서 NAVIGATES_TO 관계 가져오기
    navigations = old_graph.query("""
        MATCH (p1:PAGE)-[nav:NAVIGATES_TO]->(p2:PAGE)
        RETURN p1.pageId as fromPageId,
               p2.pageId as toPageId,
               nav.weight as weight,
               nav.createdAt as createdAt
    """)

    migrated_count = 0

    for nav in navigations:
        from_page_id = nav.get('fromPageId')
        to_page_id = nav.get('toPageId')
        weight = nav.get('weight', 1)
        created_at = nav.get('createdAt')

        # NEW DB에서 해당 STEP 찾아서 NEXT_STEP 관계 생성
        result = new_graph.query("""
            MATCH (s1:STEP {oldPageId: $fromPageId})
            MATCH (s2:STEP {oldPageId: $toPageId})
            MERGE (s1)-[r:NEXT_STEP]->(s2)
            ON CREATE SET
                r.weight = $weight,
                r.createdAt = $createdAt,
                r.lastUpdated = datetime()
            ON MATCH SET
                r.weight = r.weight + $weight
            RETURN count(r) as created
        """, {
            'fromPageId': from_page_id,
            'toPageId': to_page_id,
            'weight': weight,
            'createdAt': created_at
        })

        if result and result[0].get('created', 0) > 0:
            migrated_count += 1

    print(f"   ✓ NEXT_STEP 관계 {migrated_count}개 생성 완료\n")
    return migrated_count


def migrate_path_sequences_to_next_step():
    """PATH의 nodeSequence를 기반으로 NEXT_STEP 관계 생성"""
    print("3️⃣-B  PATH nodeSequence → NEXT_STEP 관계 생성 중...")

    # OLD DB에서 PATH의 nodeSequence 가져오기
    paths = old_graph.query("""
        MATCH (path:PATH)
        WHERE path.nodeSequence IS NOT NULL AND size(path.nodeSequence) > 1
        RETURN path.nodeSequence as sequence,
               path.usageCount as weight,
               path.createdAt as createdAt
    """)

    migrated_count = 0

    for path_data in paths:
        sequence = path_data.get('sequence', [])
        weight = path_data.get('weight', 1)
        created_at = path_data.get('createdAt')

        # nodeSequence에서 연속된 PAGE 쌍을 찾아 NEXT_STEP 관계 생성
        for i in range(len(sequence) - 1):
            from_page_id = sequence[i]
            to_page_id = sequence[i + 1]

            # root 노드는 건너뛰기
            if from_page_id.startswith('root_') or to_page_id.startswith('root_'):
                continue

            # NEW DB에서 해당 STEP 찾아서 NEXT_STEP 관계 생성
            result = new_graph.query("""
                MATCH (s1:STEP {oldPageId: $fromPageId})
                MATCH (s2:STEP {oldPageId: $toPageId})
                MERGE (s1)-[r:NEXT_STEP]->(s2)
                ON CREATE SET
                    r.weight = $weight,
                    r.createdAt = $createdAt,
                    r.lastUpdated = datetime()
                ON MATCH SET
                    r.weight = r.weight + $weight
                RETURN count(r) as created
            """, {
                'fromPageId': from_page_id,
                'toPageId': to_page_id,
                'weight': weight,
                'createdAt': created_at
            })

            if result and result[0].get('created', 0) > 0:
                migrated_count += 1

    print(f"   ✓ nodeSequence 기반 NEXT_STEP 관계 {migrated_count}개 생성 완료\n")
    return migrated_count


def migrate_path_to_has_step():
    """OLD DB의 PATH 노드를 NEW DB의 HAS_STEP 관계로 변환"""
    print("4️⃣  PATH → HAS_STEP 관계 생성 중...")

    # OLD DB에서 PATH 노드 가져오기 (nodeSequence에서 첫 번째 PAGE ID 추출)
    paths = old_graph.query("""
        MATCH (path:PATH)
        WHERE path.nodeSequence IS NOT NULL AND size(path.nodeSequence) > 1
        WITH path,
             path.nodeSequence[1] as firstPageId
        RETURN path.pathId as pathId,
               path.startCommand as taskIntent,
               path.startDomain as domain,
               firstPageId,
               path.embedding as pathEmbedding,
               path.createdAt as createdAt,
               path.lastUsed as lastUsed
        ORDER BY path.createdAt
    """)

    migrated_count = 0
    skipped_no_domain = 0
    skipped_no_step = 0
    skipped_no_root = 0

    print(f"   총 {len(paths)}개의 PATH 처리 중...")

    for path_data in paths:
        domain = normalize_domain(path_data.get('domain', ''))
        if not domain:
            skipped_no_domain += 1
            continue

        task_intent = path_data.get('taskIntent', '알 수 없는 작업')
        first_page_id = path_data.get('firstPageId')
        path_embedding = path_data.get('pathEmbedding', [])

        # taskIntent 임베딩 생성
        if not path_embedding or len(path_embedding) == 0:
            intent_embedding = generate_embedding(task_intent)
        else:
            intent_embedding = path_embedding

        # NEW DB에서 첫 번째 STEP 찾기
        first_step = new_graph.query("""
            MATCH (s:STEP {oldPageId: $firstPageId})
            RETURN s.stepId as stepId, s.domain as stepDomain
            LIMIT 1
        """, {'firstPageId': first_page_id})

        if not first_step:
            skipped_no_step += 1
            if skipped_no_step <= 3:  # 처음 3개만 출력
                print(f"   ⚠ STEP 못 찾음: firstPageId={first_page_id}, domain={domain}")
            continue

        step_id = first_step[0]['stepId']
        step_domain = first_step[0].get('stepDomain', '')

        # HAS_STEP 관계 생성
        result = new_graph.query("""
            MATCH (r:ROOT {domain: $domain})
            MATCH (s:STEP {stepId: $stepId})
            MERGE (r)-[rel:HAS_STEP]->(s)
            ON CREATE SET
                rel.weight = 1,
                rel.order = 0,
                rel.taskIntent = $taskIntent,
                rel.intentEmbedding = $intentEmbedding,
                rel.createdAt = $createdAt,
                rel.lastUpdated = $lastUsed
            ON MATCH SET
                rel.weight = rel.weight + 1
            RETURN rel, r.domain as rootDomain
        """, {
            'domain': domain,
            'stepId': step_id,
            'taskIntent': task_intent,
            'intentEmbedding': intent_embedding,
            'createdAt': path_data.get('createdAt'),
            'lastUsed': path_data.get('lastUsed')
        })

        if result and len(result) > 0:
            migrated_count += 1
        else:
            skipped_no_root += 1
            if skipped_no_root <= 3:  # 처음 3개만 출력
                print(f"   ⚠ ROOT 못 찾음: domain={domain}, stepId={step_id[:8]}...")

    print(f"   ✓ HAS_STEP 관계 {migrated_count}개 생성 완료")
    print(f"   ⚠ 건너뜀 - domain 없음: {skipped_no_domain}개, STEP 못 찾음: {skipped_no_step}개, ROOT 못 찾음: {skipped_no_root}개\n")
    return migrated_count


def create_new_indexes():
    """NEW DB에 필요한 인덱스 생성"""
    print("5️⃣  NEW DB 인덱스 생성 중...")

    # STEP.stepId 고유 제약
    try:
        new_graph.query("""
            CREATE CONSTRAINT step_id_unique IF NOT EXISTS
            FOR (s:STEP) REQUIRE s.stepId IS UNIQUE
        """)
        print("   ✓ STEP.stepId 고유 제약 생성")
    except Exception as e:
        print(f"   ⚠ STEP.stepId 제약 생성 실패: {e}")

    # ROOT.domain 고유 제약
    try:
        new_graph.query("""
            CREATE CONSTRAINT root_domain_unique IF NOT EXISTS
            FOR (r:ROOT) REQUIRE r.domain IS UNIQUE
        """)
        print("   ✓ ROOT.domain 고유 제약 생성")
    except Exception as e:
        print(f"   ⚠ ROOT.domain 제약 생성 실패: {e}")

    # STEP.domain 인덱스
    try:
        new_graph.query("""
            CREATE INDEX step_domain_idx IF NOT EXISTS
            FOR (s:STEP) ON (s.domain)
        """)
        print("   ✓ STEP.domain 인덱스 생성")
    except Exception as e:
        print(f"   ⚠ STEP.domain 인덱스 생성 실패: {e}")

    # STEP.action 인덱스
    try:
        new_graph.query("""
            CREATE INDEX step_action_idx IF NOT EXISTS
            FOR (s:STEP) ON (s.action)
        """)
        print("   ✓ STEP.action 인덱스 생성")
    except Exception as e:
        print(f"   ⚠ STEP.action 인덱스 생성 실패: {e}")

    # STEP 벡터 인덱스 (Neo4j 5.x)
    try:
        new_graph.query("""
            CREATE VECTOR INDEX step_embedding IF NOT EXISTS
            FOR (s:STEP) ON (s.embedding)
            OPTIONS {indexConfig: {
              `vector.dimensions`: 1536,
              `vector.similarity_function`: 'cosine'
            }}
        """)
        print("   ✓ STEP.embedding 벡터 인덱스 생성")
    except Exception as e:
        print(f"   ⚠ STEP 벡터 인덱스 생성 실패 (Neo4j 5.x 이상 필요): {e}")

    # ROOT 벡터 인덱스
    try:
        new_graph.query("""
            CREATE VECTOR INDEX root_embedding IF NOT EXISTS
            FOR (r:ROOT) ON (r.embedding)
            OPTIONS {indexConfig: {
              `vector.dimensions`: 1536,
              `vector.similarity_function`: 'cosine'
            }}
        """)
        print("   ✓ ROOT.embedding 벡터 인덱스 생성")
    except Exception as e:
        print(f"   ⚠ ROOT 벡터 인덱스 생성 실패: {e}")

    # 전문 검색 인덱스
    try:
        new_graph.query("""
            CREATE FULLTEXT INDEX step_text_search IF NOT EXISTS
            FOR (s:STEP) ON EACH [s.description, s.textLabels]
        """)
        print("   ✓ STEP 전문 검색 인덱스 생성")
    except Exception as e:
        print(f"   ⚠ 전문 검색 인덱스 생성 실패: {e}")

    print()


def cleanup_temp_fields():
    """임시 필드 제거 (oldPageId)"""
    print("6️⃣  임시 필드 정리 중...")

    result = new_graph.query("""
        MATCH (s:STEP)
        WHERE s.oldPageId IS NOT NULL
        REMOVE s.oldPageId
        RETURN count(s) as cleaned
    """)

    cleaned_count = result[0]['cleaned'] if result else 0
    print(f"   ✓ oldPageId 필드 {cleaned_count}개 제거\n")


def verify_migration():
    """마이그레이션 결과 확인"""
    print("7️⃣  마이그레이션 결과 확인...\n")

    # ROOT 통계
    root_stats = new_graph.query("""
        MATCH (r:ROOT)
        RETURN count(r) as total,
               count(r.embedding) as with_embedding,
               count(r.visitCount) as with_visitCount
    """)

    if root_stats:
        stats = root_stats[0]
        print(f"   ROOT 노드:")
        print(f"     - 전체: {stats['total']}개")
        print(f"     - 임베딩 있음: {stats['with_embedding']}개")
        print(f"     - visitCount 있음: {stats['with_visitCount']}개")

    # STEP 통계
    step_stats = new_graph.query("""
        MATCH (s:STEP)
        RETURN count(s) as total,
               count(s.embedding) as with_embedding
    """)

    if step_stats:
        stats = step_stats[0]
        print(f"\n   STEP 노드:")
        print(f"     - 전체: {stats['total']}개")
        print(f"     - 임베딩 있음: {stats['with_embedding']}개")

    # HAS_STEP 관계 통계
    has_step_count = new_graph.query("""
        MATCH ()-[r:HAS_STEP]->()
        RETURN count(r) as count
    """)

    if has_step_count:
        print(f"\n   HAS_STEP 관계: {has_step_count[0]['count']}개")

    # NEXT_STEP 관계 통계
    next_step_count = new_graph.query("""
        MATCH ()-[r:NEXT_STEP]->()
        RETURN count(r) as count
    """)

    if next_step_count:
        print(f"   NEXT_STEP 관계: {next_step_count[0]['count']}개")

    # 예시 경로 출력
    sample_path = new_graph.query("""
        MATCH (r:ROOT)-[has:HAS_STEP]->(first:STEP)
        OPTIONAL MATCH path = (first)-[:NEXT_STEP*0..5]->(last:STEP)
        RETURN r.domain as domain,
               has.taskIntent as taskIntent,
               [node in nodes(path) | node.description][0..5] as steps
        LIMIT 1
    """)

    if sample_path and len(sample_path) > 0:
        print(f"\n   📌 예시 경로:")
        print(f"      도메인: {sample_path[0]['domain']}")
        print(f"      작업: {sample_path[0]['taskIntent']}")
        steps = sample_path[0].get('steps', [])
        if steps:
            print(f"      단계: {' → '.join([s for s in steps if s])}")

    print()


def add_missing_fields_manually():
    """
    마이그레이션 후 누락된 필드를 수동으로 추가하는 함수들

    이 함수들은 마이그레이션 후 필요에 따라 별도로 실행할 수 있습니다.
    """
    print("\n" + "="*60)
    print("📝 수동 필드 추가 함수 가이드")
    print("="*60)

    print("""
다음 함수들을 사용하여 추가 필드를 수동으로 업데이트할 수 있습니다:

1. add_input_types_to_steps()
   - STEP 노드에 inputType, inputPlaceholder 추가
   - HTML type 속성이나 placeholder로 추론

2. add_wait_steps_manually()
   - 대기 STEP 추가 (로그인 후 2단계 인증 등)

3. enrich_task_intents()
   - HAS_STEP 관계의 taskIntent를 더 의미있게 변경

4. update_step_descriptions()
   - STEP description을 AI로 생성

5. add_step_sequence_order()
   - NEXT_STEP 관계에 sequenceOrder 추가

사용 예시:
  python scripts/migrate_old_to_new_db.py --add-input-types
  python scripts/migrate_old_to_new_db.py --add-wait-steps
    """)


def add_input_types_to_steps():
    """STEP 노드에 inputType 추가 (HTML type 기반 추론)"""
    print("\n🔧 inputType 필드 추가 중...")

    # 패턴 기반 inputType 추론
    result = new_graph.query("""
        MATCH (s:STEP)
        WHERE s.action = 'input' AND s.inputType IS NULL
        WITH s,
             CASE
                 WHEN any(label IN s.textLabels WHERE toLower(label) CONTAINS 'password' OR toLower(label) CONTAINS '비밀번호')
                     THEN 'password'
                 WHEN any(label IN s.textLabels WHERE toLower(label) CONTAINS 'email' OR toLower(label) CONTAINS '이메일')
                     THEN 'email'
                 WHEN any(label IN s.textLabels WHERE toLower(label) CONTAINS 'search' OR toLower(label) CONTAINS '검색')
                     THEN 'search'
                 WHEN any(label IN s.textLabels WHERE toLower(label) CONTAINS 'id' OR toLower(label) CONTAINS '아이디')
                     THEN 'id'
                 ELSE 'text'
             END as inferredType
        SET s.inputType = inferredType
        RETURN count(s) as updated
    """)

    if result:
        print(f"   ✓ {result[0]['updated']}개 STEP에 inputType 추가됨")


def add_step_sequence_order():
    """NEXT_STEP 관계에 sequenceOrder 추가"""
    print("\n🔧 NEXT_STEP sequenceOrder 추가 중...")

    result = new_graph.query("""
        MATCH path = (first:STEP)-[:NEXT_STEP*]->(last:STEP)
        WHERE NOT ()-[:NEXT_STEP]->(first)
        WITH path, relationships(path) as rels
        UNWIND range(0, size(rels)-1) as idx
        WITH rels[idx] as rel, idx
        SET rel.sequenceOrder = idx + 1
        RETURN count(DISTINCT rel) as updated
    """)

    if result:
        print(f"   ✓ {result[0]['updated']}개 관계에 sequenceOrder 추가됨")


def main():
    """메인 마이그레이션 실행"""
    try:
        # 확인 프롬프트
        print(f"OLD DB: {OLD_NEO4J_URI}")
        print(f"NEW DB: {NEW_NEO4J_URI}\n")

        response = input("⚠️  NEW DB의 기존 데이터가 모두 삭제됩니다. 계속하시겠습니까? (yes/no): ")
        if response.lower() != 'yes':
            print("마이그레이션 취소됨.")
            return

        print("\n마이그레이션 시작...\n")

        # NEW DB 초기화
        print("0️⃣  NEW DB 초기화 중...")
        new_graph.query("MATCH (n) DETACH DELETE n")
        print("   ✓ 기존 데이터 삭제 완료\n")

        # 1. ROOT 노드 마이그레이션
        migrate_root_nodes()

        # 2. PAGE → STEP 변환
        migrate_page_to_step()

        # 3. NAVIGATES_TO → NEXT_STEP 변환
        migrate_navigates_to_relationships()

        # 3-B. PATH nodeSequence → NEXT_STEP 변환
        migrate_path_sequences_to_next_step()

        # 4. PATH → HAS_STEP 변환
        migrate_path_to_has_step()

        # 5. 인덱스 생성
        create_new_indexes()

        # 6. 임시 필드 정리
        cleanup_temp_fields()

        # 7. 결과 확인
        verify_migration()

        print("✅ 마이그레이션 완료!\n")

        # 추가 작업 안내
        add_missing_fields_manually()

    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys

    # 커맨드라인 인자 처리
    if len(sys.argv) > 1:
        if '--add-input-types' in sys.argv:
            add_input_types_to_steps()
        elif '--add-sequence-order' in sys.argv:
            add_step_sequence_order()
        else:
            print("사용법:")
            print("  python migrate_old_to_new_db.py              # 전체 마이그레이션")
            print("  python migrate_old_to_new_db.py --add-input-types  # inputType 추가")
            print("  python migrate_old_to_new_db.py --add-sequence-order  # sequenceOrder 추가")
    else:
        main()
