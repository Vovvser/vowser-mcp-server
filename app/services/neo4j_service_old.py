import os
import json
import hashlib

from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv, find_dotenv
from langchain_neo4j import Neo4jGraph
from app.services.embedding_service import generate_embedding, create_embedding_text

load_dotenv(find_dotenv())

# Neo4j 그래프 객체 초기화
try:
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD"),
    )
    print("Neo4j Service: Database connection successful.")
except Exception as e:
    print(f"Neo4j Service: Database connection failed. Error: {e}")
    graph = None


def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.replace('www.', '')

def is_base_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.path in ['', '/'] and not parsed.query and not parsed.fragment

def create_page_id(url: str, element_data: dict) -> str:
    element_key = (
        element_data.get('primarySelector', '') +
        '_' +
        str(element_data.get('textLabels', []))
    )
    return hashlib.md5(f"{url}_{element_key}".encode()).hexdigest()

def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if normalized.endswith('/') and parsed.path != '/':
        normalized = normalized[:-1]
    return normalized

def add_metadata_to_path(path_json):
    """
    경로 JSON에 메타데이터 추가
    """
    path_string = json.dumps(path_json['completePath'], sort_keys=True)
    
    path_id = hashlib.md5(
        f"{path_json['startCommand']}_{path_string}".encode()
    ).hexdigest()
    
    path_json['metadata'] = {
        'pathId': path_id,
        'createdAt': datetime.now().isoformat(),
        'lastUsed': datetime.now().isoformat(),
        'usageCount': 1,
        'successRate': 1.0,
        'avgExecutionTime': None,
        'createdBy': 'user_001',
        'status': 'active'  # active, deprecated, broken
    }
    
    for step in path_json['completePath']:
        if step['order'] > 0:
            semantic_text = ' '.join([
                ' '.join(step['semanticData'].get('textLabels', [])),
                step['semanticData'].get('contextText', {}).get('immediate', ''),
                step['semanticData'].get('contextText', {}).get('section', ''),
            ])
            neighbor_text = ' '.join(step['semanticData'].get('contextText', {}).get('neighbor', []))
            if neighbor_text:
                semantic_text = f"{semantic_text} {neighbor_text}"

            page_title = step['semanticData'].get('pageInfo', {}).get('title', '')
            if page_title:
                semantic_text = f"{semantic_text} {page_title}"

            semantic_text = ' '.join(semantic_text.split())
            
            step['embeddingText'] = semantic_text
    
    return path_json

def save_path_to_neo4j(path_data):
    """
    경로 데이터를 받아서 Neo4j에 저장
    """
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")

    if hasattr(path_data, 'model_dump'):
        path_json = path_data.model_dump()
    else:
        path_json = path_data

    clicks = [step for step in path_json['completePath'] if step['order'] > 0]

    if not clicks:
        print("클릭 데이터가 없습니다")
        return {"status": "noop", "reason": "No clickable steps found."}

    previous_node_id = None
    previous_node_type = None
    previous_domain = None

    for i, step in enumerate(clicks):
        current_url = step['url']
        current_domain = extract_domain(current_url)
        domain_changed = previous_domain and previous_domain != current_domain

        has_click_element = 'locationData' in step and 'semanticData' in step

        if has_click_element:
            page_id = create_page_id(current_url, step['locationData'])
            embedding_text = step.get('embeddingText', '')
            embedding = generate_embedding(embedding_text)

            create_page_query = """
            MERGE (p:PAGE {pageId: $pageId})
            SET p.url = $url,
                p.domain = $domain,
                p.primarySelector = $primarySelector,
                p.fallbackSelectors = $fallbackSelectors,
                p.anchorPoint = $anchorPoint,
                p.relativePathFromAnchor = $relativePathFromAnchor,
                p.elementSnapshot = $elementSnapshot,
                p.textLabels = $textLabels,
                p.contextText = $contextText,
                p.actionType = $actionType,
                p.embedding = $embedding,
                p.lastUpdated = datetime()
            RETURN p
            """
            page_params = {
                'pageId': page_id,
                'url': current_url,
                'domain': current_domain,
                'primarySelector': step['locationData']['primarySelector'],
                'fallbackSelectors': step['locationData']['fallbackSelectors'],
                'anchorPoint': step['locationData'].get('anchorPoint', ''),
                'relativePathFromAnchor': step['locationData'].get('relativePathFromAnchor', ''),
                'elementSnapshot': json.dumps(step['locationData'].get('elementSnapshot', {})),
                'textLabels': step['semanticData']['textLabels'],
                'contextText': json.dumps(step['semanticData']['contextText']),
                'actionType': step['semanticData']['actionType'],
                'embedding': embedding
            }

            graph.query(create_page_query, page_params)
            print(f"PAGE: {step['semanticData']['textLabels'][0]} ({current_domain})")

            try:
                if i == 0 or domain_changed:
                    create_root_if_needed = """
                    MERGE (r:ROOT {domain: $domain})
                    SET r.baseURL = $baseURL,
                        r.lastVisited = datetime()
                    RETURN r
                    """
                    graph.query(create_root_if_needed, {
                        'domain': current_domain,
                        'baseURL': f"https://{current_domain}"
                    })

                    connect_to_root = """
                    MATCH (r:ROOT {domain: $domain})
                    MATCH (p:PAGE {pageId: $pageId})
                    MERGE (r)-[rel:HAS_PAGE]->(p)
                    SET rel.weight = coalesce(rel.weight, 0) + 1,
                        rel.createdAt = coalesce(rel.createdAt, datetime()),
                        rel.lastUpdated = datetime()
                    """
                    graph.query(connect_to_root, {
                        'domain': current_domain,
                        'pageId': page_id
                    })

                    if previous_node_type == 'PAGE' and domain_changed:
                        cross_connect = """
                        MATCH (p1:PAGE {pageId: $prevId})
                        MATCH (p2:PAGE {pageId: $currId})
                        MERGE (p1)-[rel:NAVIGATES_TO_CROSS_DOMAIN]->(p2)
                        SET rel.weight = coalesce(rel.weight, 0) + 1,
                            rel.createdAt = coalesce(rel.createdAt, datetime()),
                            rel.lastUpdated = datetime()
                        """
                        graph.query(cross_connect, {
                            'prevId': previous_node_id,
                            'currId': page_id
                        })

                elif previous_node_type == 'PAGE':
                    connect_pages = """
                    MATCH (p1:PAGE {pageId: $prevId})
                    MATCH (p2:PAGE {pageId: $currId})
                    MERGE (p1)-[rel:NAVIGATES_TO]->(p2)
                    SET rel.weight = coalesce(rel.weight, 0) + 1,
                        rel.createdAt = coalesce(rel.createdAt, datetime()),
                        rel.lastUpdated = datetime()
                    """
                    graph.query(connect_pages, {
                        'prevId': previous_node_id,
                        'currId': page_id
                    })
            except Exception as e:
                print(f"관계 생성 실패: {e}")

            previous_node_type = 'PAGE'
            previous_node_id = page_id

        elif is_base_url(current_url):
            print(f"ROOT: {current_domain} (클릭 요소 없음)")

        previous_domain = current_domain

    # PATH 엔티티 생성
    if path_json:
        path_id = create_path_entity(path_json)
        if path_id:
            print(f"PATH 엔티티 생성됨: {path_id}")

    print("\n경로 저장 완료!")
    return {"status": "success", "saved_steps": len(clicks)}


def save_page_analysis_to_neo4j(url: str, page_structure):
    """
    페이지 분석 결과를 Neo4j에 저장
    
    Args:
        url (str): 분석한 페이지 URL
        page_structure: PageStructure 객체 (Pydantic 모델)
    """
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")
    
    domain = extract_domain(url)
    
    try:
        analysis_id = hashlib.md5(f"{url}_{page_structure.page_title}".encode()).hexdigest()
        
        create_analysis_query = """
        MERGE (pa:PAGE_ANALYSIS {analysisId: $analysisId})
        SET pa.url = $url,
            pa.domain = $domain,
            pa.pageTitle = $pageTitle,
            pa.analyzedAt = datetime(),
            pa.sectionsCount = $sectionsCount
        RETURN pa
        """
        
        analysis_params = {
            'analysisId': analysis_id,
            'url': url,
            'domain': domain,
            'pageTitle': page_structure.page_title,
            'sectionsCount': len(page_structure.sections)
        }
        
        graph.query(create_analysis_query, analysis_params)
        print(f"PAGE_ANALYSIS: {page_structure.page_title} ({domain})")
        
        graph.query(
            "MERGE (r:ROOT {domain: $domain}) SET r.lastAnalyzed = datetime()",
            {'domain': domain}
        )
        
        graph.query(
            """
            MATCH (r:ROOT {domain: $domain})
            MATCH (pa:PAGE_ANALYSIS {analysisId: $analysisId})
            MERGE (r)-[rel:HAS_ANALYSIS]->(pa)
            SET rel.weight = coalesce(rel.weight, 0) + 1,
                rel.createdAt = coalesce(rel.createdAt, datetime()),
                rel.lastUpdated = datetime()
            """,
            {'domain': domain, 'analysisId': analysis_id}
        )
        
        for i, section in enumerate(page_structure.sections):
            section_id = f"{analysis_id}_section_{i}"
            
            create_section_query = """
            MERGE (s:SECTION {sectionId: $sectionId})
            SET s.sectionName = $sectionName,
                s.elementCount = $elementCount,
                s.order = $order
            RETURN s
            """
            
            section_params = {
                'sectionId': section_id,
                'sectionName': section.section_name,
                'elementCount': len(section.elements),
                'order': i
            }
            
            graph.query(create_section_query, section_params)
            
            graph.query(
                """
                MATCH (pa:PAGE_ANALYSIS {analysisId: $analysisId})
                MATCH (s:SECTION {sectionId: $sectionId})
                MERGE (pa)-[rel:HAS_SECTION]->(s)
                SET rel.order = $order
                """,
                {'analysisId': analysis_id, 'sectionId': section_id, 'order': i}
            )
            
            for j, element in enumerate(section.elements):
                element_id = f"{section_id}_element_{j}"
                
                embedding = generate_embedding(element.text)
                
                create_element_query = """
                MERGE (e:ELEMENT {elementId: $elementId})
                SET e.text = $text,
                    e.actionType = $actionType,
                    e.embedding = $embedding,
                    e.order = $order
                RETURN e
                """
                
                element_params = {
                    'elementId': element_id,
                    'text': element.text,
                    'actionType': element.action_type,
                    'embedding': embedding,
                    'order': j
                }
                
                graph.query(create_element_query, element_params)
                
                graph.query(
                    """
                    MATCH (s:SECTION {sectionId: $sectionId})
                    MATCH (e:ELEMENT {elementId: $elementId})
                    MERGE (s)-[rel:HAS_ELEMENT]->(e)
                    SET rel.order = $order
                    """,
                    {'sectionId': section_id, 'elementId': element_id, 'order': j}
                )
        
        print(f"분석 결과 저장 완료: {len(page_structure.sections)}개 섹션, "
              f"{sum(len(s.elements) for s in page_structure.sections)}개 요소")
        
        return {
            "status": "success", 
            "analysisId": analysis_id,
            "sectionsCount": len(page_structure.sections),
            "elementsCount": sum(len(s.elements) for s in page_structure.sections)
        }
        
    except Exception as e:
        print(f"페이지 분석 결과 저장 실패: {e}")
        return {"status": "error", "message": str(e)}


def check_graph_structure():
    if not graph:
        print("Neo4j database is not connected.")
        return
        
    stats_query = """
    OPTIONAL MATCH (r:ROOT)
    OPTIONAL MATCH (p:PAGE)
    OPTIONAL MATCH (path:PATH)
    OPTIONAL MATCH (r)-[hp:HAS_PAGE]->()
    OPTIONAL MATCH ()-[nt:NAVIGATES_TO]->()
    OPTIONAL MATCH ()-[ntcd:NAVIGATES_TO_CROSS_DOMAIN]->()
    RETURN
        count(DISTINCT r) as root_count,
        count(DISTINCT p) as page_count,
        count(DISTINCT path) as path_count,
        count(DISTINCT hp) as has_page_count,
        count(DISTINCT nt) as navigates_to_count,
        count(DISTINCT ntcd) as cross_domain_count
    """

    try:
        result = graph.query(stats_query)
        print("그래프 통계:")
        for r in result:
            print(f"  - ROOT 노드: {r['root_count']}")
            print(f"  - PAGE 노드: {r['page_count']}")
            print(f"  - PATH 노드: {r['path_count']}")
            print(f"  - HAS_PAGE 관계: {r['has_page_count']}")
            print(f"  - NAVIGATES_TO 관계: {r['navigates_to_count']}")
            print(f"  - CROSS_DOMAIN 관계: {r['cross_domain_count']}")
        return result[0] if result else None
    except Exception as e:
        print(f"그래프 구조 확인 실패: {e}")
        return None

def visualize_paths(domain: str):
    """특정 도메인의 경로 시각화"""
    if not graph:
        print("Neo4j database is not connected.")
        return
        
    query = """
    MATCH path = (r:ROOT {domain: $domain})-[:HAS_PAGE|NAVIGATES_TO*]->(p:PAGE)
    WITH r, p, length(path) as depth
    RETURN
        depth,
        p.url as url,
        p.textLabels as labels,
        p.primarySelector as selector
    ORDER BY depth
    LIMIT 20
    """

    try:
        results = graph.query(query, {'domain': domain})

        print(f"\n{domain}에서 시작하는 경로:")
        if not results:
            print("경로가 없습니다.")
            return

        current_depth = 0
        for r in results:
            if r['depth'] != current_depth:
                current_depth = r['depth']
                print(f"\n{'  ' * (current_depth-1)}깊이 {current_depth}:")
            labels = r['labels'] if r['labels'] else ['N/A']
            print(f"{'  ' * current_depth}→ {labels[0]}")
            print(f"{'  ' * current_depth}  URL: {r['url']}")
            
        return results
    except Exception as e:
        print(f"경로 시각화 실패: {e}")
        return None



def find_popular_paths(domain: str = None, limit: int = 10):
    """인기 경로 찾기"""
    if not graph:
        print("Neo4j database is not connected.")
        return
        
    if domain:
        query = """
        MATCH (r:ROOT {domain: $domain})-[rel:HAS_PAGE]->(p:PAGE)
        RETURN 
            p.textLabels as labels,
            p.url as url,
            rel.weight as popularity,
            rel.lastUsed as lastUsed
        ORDER BY rel.weight DESC
        LIMIT $limit
        """
        params = {'domain': domain, 'limit': limit}
    else:
        query = """
        MATCH (r:ROOT)-[rel:HAS_PAGE]->(p:PAGE)
        RETURN 
            r.domain as domain,
            p.textLabels as labels,
            p.url as url,
            rel.weight as popularity,
            rel.lastUsed as lastUsed
        ORDER BY rel.weight DESC
        LIMIT $limit
        """
        params = {'limit': limit}

    try:
        results = graph.query(query, params)
        
        domain_text = f" ({domain})" if domain else ""
        print(f"\n인기 경로{domain_text}:")
        if not results:
            print("인기 경로가 없습니다.")
            return

        for i, r in enumerate(results, 1):
            labels = r['labels'] if r['labels'] else ['N/A']
            domain_info = f" - {r['domain']}" if not domain else ""
            print(f"  {i}. {labels[0]}{domain_info}")
            print(f"     인기도: {r['popularity']}, 마지막 사용: {r['lastUsed']}")
            print(f"     URL: {r['url']}")
            print()
            
        return results
    except Exception as e:
        print(f"인기 경로 조회 실패: {e}")
        return None


def run_overlap_test(test_cases: list = None):
    if not graph:
        print("Neo4j database is not connected.")
        return
        
    print("경로 겹침 테스트 시작\n")

    if test_cases:
        for i, test_case in enumerate(test_cases, 1):
            print(f"테스트 케이스 {i}: {test_case['startCommand']}")
            test_with_metadata = add_metadata_to_path(test_case.copy())
            save_path_to_neo4j(test_with_metadata)
            print()

    print("\n테스트 결과 분석:")

    try:
        # 1. 공유되는 노드 확인
        shared_nodes = graph.query("""
        MATCH (p:PAGE)<-[:HAS_PAGE|NAVIGATES_TO*]-(r:ROOT)
        WITH p, count(DISTINCT r) as root_count
        WHERE root_count > 0
        MATCH (p)<-[rel:HAS_PAGE|NAVIGATES_TO]-()
        WITH p, count(rel) as incoming_count
        WHERE incoming_count > 1
        RETURN p.textLabels[0] as page, p.url as url, incoming_count
        """)

        print("\n공유되는 PAGE 노드:")
        if shared_nodes:
            for node in shared_nodes:
                print(f"  - {node['page']}: {node['incoming_count']}개 경로에서 사용")
        else:
            print("  공유되는 노드가 없습니다.")

        # 2. 경로 가중치 확인
        weights = graph.query("""
        MATCH ()-[rel:HAS_PAGE|NAVIGATES_TO]->()
        WHERE rel.weight > 1
        MATCH (from)-[rel]->(to)
        RETURN
            labels(from)[0] as from_type,
            CASE
                WHEN from:ROOT THEN from.domain
                ELSE from.textLabels[0]
            END as from_name,
            labels(to)[0] as to_type,
            CASE
                WHEN to:ROOT THEN to.domain
                ELSE to.textLabels[0]
            END as to_name,
            rel.weight as weight
        ORDER BY rel.weight DESC
        """)

        print("\n증가된 가중치 (2회 이상 사용된 경로):")
        if weights:
            for w in weights:
                print(f"  - {w['from_name']} → {w['to_name']}: 가중치 {w['weight']}")
        else:
            print("  가중치가 증가된 경로가 없습니다.")

        # 3. 전체 경로 시각화 (YouTube 기준)
        print("\n전체 경로 구조:")
        all_paths = graph.query("""
        MATCH (r:ROOT {domain: 'youtube.com'})
        MATCH path = (r)-[:HAS_PAGE|NAVIGATES_TO*..5]->(end:PAGE)
        WHERE NOT (end)-[:NAVIGATES_TO]->()
        RETURN [n in nodes(path) |
            CASE
                WHEN n:ROOT THEN n.domain
                ELSE n.textLabels[0]
            END
        ] as path_nodes
        LIMIT 10
        """)

        if all_paths:
            for i, path in enumerate(all_paths, 1):
                print(f"  경로 {i}: {' → '.join(path['path_nodes'])}")
        else:
            print("  YouTube 도메인의 경로가 없습니다.")

        return {
            "shared_nodes": shared_nodes,
            "weighted_paths": weights,
            "path_visualizations": all_paths
        }

    except Exception as e:
        print(f"테스트 결과 분석 실패: {e}")
        return None


# PATH 엔티티 관련 함수들 추가

def create_path_entity(path_json):
    """
    경로 저장 후 PATH 엔티티 생성
    """
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")
    
    try:
        # 경로의 모든 노드 정보를 결합하여 설명 생성
        clicks = [step for step in path_json['completePath'] if step['order'] > 0]
        if not clicks:
            return None
            
        # 노드 시퀀스 생성
        node_sequence = ["root_" + extract_domain(clicks[0]['url'])]
        descriptions = []
        
        for step in clicks:
            if 'locationData' in step and 'semanticData' in step:
                page_id = create_page_id(step['url'], step['locationData'])
                node_sequence.append("page_" + page_id)
                
                # 텍스트 라벨로 설명 생성
                labels = step['semanticData'].get('textLabels', [])
                if labels:
                    descriptions.append(labels[0])
        
        # PATH 설명 생성
        path_description = " → ".join(descriptions)
        
        # 전체 경로의 임베딩 생성
        full_text = path_json.get('startCommand', '') + " " + path_description
        path_embedding = generate_embedding(full_text)
        
        # PATH ID 생성
        path_id = "path_" + hashlib.md5("_".join(node_sequence).encode()).hexdigest()
        
        # PATH 엔티티 생성
        create_path_query = """
        MERGE (path:PATH {pathId: $pathId})
        SET path.description = $description,
            path.nodeSequence = $nodeSequence,
            path.startDomain = $startDomain,
            path.targetPageId = $targetPageId,
            path.embedding = $embedding,
            path.startCommand = $startCommand,
            path.startUrl = $startUrl,
            path.pathId = $originalPathId,
            path.totalWeight = coalesce(path.totalWeight, 0) + 1,
            path.usageCount = coalesce(path.usageCount, 0) + 1,
            path.createdAt = coalesce(path.createdAt, datetime()),
            path.lastUsed = datetime(),
            path.lastUpdated = datetime()
        RETURN path
        """
        
        path_params = {
            'pathId': path_id,
            'description': path_description,
            'nodeSequence': node_sequence,
            'startDomain': extract_domain(clicks[0]['url']),
            'targetPageId': node_sequence[-1] if node_sequence else None,
            'embedding': path_embedding,
            'startCommand': path_json.get('startCommand', ''),
            'startUrl': clicks[0]['url'] if clicks else '',
            'originalPathId': path_json.get('metadata', {}).get('pathId', path_id)
        }
        
        result = graph.query(create_path_query, path_params)
        
        # PATH와 PAGE 노드 연결
        if len(node_sequence) > 1:  # ROOT 제외하고 PAGE들만
            page_ids = [nid.replace("page_", "") for nid in node_sequence[1:]]
            connect_query = """
            MATCH (path:PATH {pathId: $pathId})
            MATCH (p:PAGE) WHERE p.pageId IN $pageIds
            MERGE (path)-[:CONTAINS]->(p)
            """
            graph.query(connect_query, {'pathId': path_id, 'pageIds': page_ids})
        
        print(f"PATH 엔티티 생성: {path_description}")
        return path_id
        
    except Exception as e:
        print(f"PATH 엔티티 생성 실패: {e}")
        return None


def search_paths_by_query(query_text, limit=3, domain_hint=None):
    """
    자연어 쿼리로 관련 경로 검색
    """
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")
    
    import time
    start_time = time.time()
    
    try:
        # 쿼리 임베딩 생성
        query_embedding = generate_embedding(query_text)
        if not query_embedding:
            return None
        
        # 도메인 힌트 처리
        domain_filter = ""
        if domain_hint:
            domain_filter = f"AND path.startDomain = '{domain_hint}'"
        elif "유튜브" in query_text or "youtube" in query_text.lower():
            domain_filter = "AND path.startDomain = 'youtube.com'"
        elif "네이버" in query_text or "naver" in query_text.lower():
            domain_filter = "AND path.startDomain = 'comic.naver.com'"
        
        # 1. PATH 엔티티에서 벡터 검색 (Python에서 코사인 유사도 계산)
        path_search_query = f"""
        MATCH (path:PATH)
        WHERE path.embedding IS NOT NULL {domain_filter}
        RETURN path
        """

        all_paths = graph.query(path_search_query)
        print(f"[DEBUG] 찾은 PATH 수: {len(all_paths)}")
        
        # Python에서 코사인 유사도 계산
        import numpy as np
        
        def cosine_similarity(vec1, vec2):
            try:
                vec1 = np.array(vec1)
                vec2 = np.array(vec2)
                if vec1.shape != vec2.shape:
                    return 0.0
                dot_product = np.dot(vec1, vec2)
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                if norm1 == 0 or norm2 == 0:
                    return 0.0
                return dot_product / (norm1 * norm2)
            except Exception as e:
                return 0.0
        
        path_results = []
        for i, path_data in enumerate(all_paths):
            try:
                path = path_data['path']
                
                # Node 객체 속성 접근 방식 시도
                path_id = getattr(path, 'pathId', None) or path.get('pathId', 'unknown') if hasattr(path, 'get') else 'unknown'
                embedding = getattr(path, 'embedding', None) or path.get('embedding', None) if hasattr(path, 'get') else None
                
                if embedding and len(embedding) > 0:
                    similarity = cosine_similarity(query_embedding, embedding)
                    if similarity > 0.1:
                        path_results.append({
                            'path': path,
                            'similarity': similarity
                        })
            except Exception as e:
                pass
        
        # 유사도 순으로 정렬
        path_results = sorted(path_results, key=lambda x: x['similarity'], reverse=True)[:limit]

        # 2. PATH가 없으면 PAGE 노드에서 검색
        if not path_results:
            page_search_query = f"""
            MATCH (page:PAGE)
            WHERE page.embedding IS NOT NULL
            RETURN page
            """
            
            all_pages = graph.query(page_search_query)
            
            # Python에서 코사인 유사도 계산
            page_results = []
            for page_data in all_pages:
                try:
                    page = page_data['page']
                    if page.get('embedding') and page['embedding'] is not None:
                        similarity = cosine_similarity(query_embedding, page['embedding'])
                        if similarity > 0.1:
                            page_results.append({
                                'page': page,
                                'similarity': similarity
                            })
                except Exception as e:
                    pass
            
            # 유사도 순으로 정렬
            page_results = sorted(page_results, key=lambda x: x['similarity'], reverse=True)[:5]
            print(f"[DEBUG] 0.1 이상 PAGE 수: {len(page_results)}")
            
            if page_results:
                # 찾은 PAGE를 포함하는 경로 구성
                path_results = []
                for page_result in page_results:
                    page = page_result['page']
                    # 해당 PAGE까지의 경로 찾기
                    path_query = """
                    MATCH path = (root:ROOT)-[:HAS_PAGE|NAVIGATES_TO*]->(target:PAGE {pageId: $pageId})
                    RETURN path, $similarity as similarity
                    LIMIT 1
                    """
                    paths = graph.query(path_query, {
                        'pageId': page['pageId'],
                        'similarity': page_result['similarity']
                    })
                    if paths:
                        path_results.extend(paths)
        
        # 3. 결과 포맷팅
        matched_paths = []
        for result in path_results[:limit]:
            if 'path' in result and hasattr(result['path'], 'nodes'):
                # 경로에서 노드 추출
                nodes = result['path'].nodes
                steps = []
                
                for i, node in enumerate(nodes):
                    if 'domain' in node and 'baseURL' in node:  # ROOT 노드
                        steps.append({
                            'order': i,
                            'type': 'ROOT',
                            'domain': node['domain'],
                            'url': node.get('baseURL', f"https://{node['domain']}"),
                            'action': f"{node['domain']} 접속"
                        })
                    elif 'pageId' in node:  # PAGE 노드
                        action = f"{node.get('textLabels', ['작업'])[0]} 클릭"
                        steps.append({
                            'order': i,
                            'type': 'PAGE',
                            'pageId': node['pageId'],
                            'url': node.get('url', ''),
                            'selector': node.get('primarySelector', ''),
                            'anchorPoint': node.get('anchorPoint', ''),
                            'action': action,
                            'textLabels': node.get('textLabels', [])
                        })
                
                if steps:
                    # 시간 감쇠 계산
                    time_decay = 1.0
                    if 'lastUsed' in result.get('path', {}):
                        days_old = (datetime.now() - result['path']['lastUsed']).days
                        time_decay = max(0.5, 1.0 - (days_old / 30) * 0.5)
                    
                    # 최종 점수 계산
                    total_weight = result.get('path', {}).get('totalWeight', 1)
                    relevance_score = (
                        result['similarity'] * 0.5 +
                        min(total_weight / 100, 1.0) * 0.3 +
                        time_decay * 0.2
                    )
                    
                    matched_paths.append({
                        'pathId': result.get('path', {}).get('pathId', 'unknown'),
                        'relevance_score': round(relevance_score, 3),
                        'total_weight': total_weight,
                        'last_used': result.get('path', {}).get('lastUsed'),
                        'estimated_time': result.get('path', {}).get('avgExecutionTime'),
                        'steps': steps
                    })
            elif 'path' in result:
                # PATH 엔티티에서 직접 가져온 경우
                path_entity = result['path']
                # 노드 시퀀스로부터 경로 재구성
                steps = reconstruct_path_from_sequence(path_entity['nodeSequence'])
                
                if steps:
                    matched_paths.append({
                        'pathId': path_entity['pathId'],
                        'description': path_entity.get('description', ''),
                        'startCommand': path_entity.get('startCommand', ''),
                        'startUrl': path_entity.get('startUrl', ''),
                        'relevance_score': round(result['similarity'], 3),
                        'total_weight': path_entity.get('totalWeight', 1),
                        'last_used': path_entity.get('lastUsed'),
                        'estimated_time': path_entity.get('avgExecutionTime'),
                        'steps': steps
                    })
        
        search_time_ms = int((time.time() - start_time) * 1000)
        
        # 응답 형식 맞추기
        formatted_paths = []
        for path in matched_paths:
            formatted_path = {
                'pathId': path.get('pathId', 'unknown'),
                'description': path.get('description', ''),
                'score': path.get('relevance_score', 0),
                'startCommand': path.get('startCommand', ''),
                'startUrl': path.get('startUrl', ''),
                'total_weight': path.get('total_weight', 1),
                'steps': []
            }
            
            # steps 형식 변환
            for step in path.get('steps', []):
                if step['type'] == 'ROOT':
                    formatted_path['steps'].append({
                        'title': f"{step['domain']} 메인",
                        'action': 'navigate',
                        'url': step['url'],
                        'selector': ''
                    })
                elif step['type'] == 'PAGE':
                    formatted_path['steps'].append({
                        'title': step.get('textLabels', [''])[0] if step.get('textLabels') else '페이지',
                        'action': 'click',
                        'url': step.get('url', ''),
                        'selector': step.get('selector', '')
                    })
            
            formatted_paths.append(formatted_path)
        
        return {
            'query': query_text,
            'total_matched': len(formatted_paths),
            'matched_paths': formatted_paths,
            'performance': {
                'query_time': search_time_ms,
                'search_time': search_time_ms
            }
        }
        
    except Exception as e:
        print(f"경로 검색 실패: {e}")
        return None


def reconstruct_path_from_sequence(node_sequence):
    """
    노드 시퀀스로부터 경로 재구성
    """
    if not graph or not node_sequence:
        return []
    
    steps = []
    for i, node_id in enumerate(node_sequence):
        if node_id.startswith("root_"):
            domain = node_id.replace("root_", "")
            steps.append({
                'order': i,
                'type': 'ROOT',
                'title': f"{domain} 메인",
                'domain': domain,
                'url': f"https://{domain}",
                'action': f"{domain} 접속"
            })
        elif node_id.startswith("page_"):
            page_id = node_id.replace("page_", "")
            # PAGE 노드 정보 조회
            page_query = """
            MATCH (p:PAGE {pageId: $pageId})
            RETURN p
            """
            page_results = graph.query(page_query, {'pageId': page_id})
            
            if page_results:
                page = page_results[0]['p']
                action = f"{page.get('textLabels', ['작업'])[0]} 클릭"
                title = page.get('textLabels', [''])[0] if page.get('textLabels') else action.replace(' 클릭', '')
                steps.append({
                    'order': i,
                    'type': 'PAGE',
                    'title': title,
                    'pageId': page_id,
                    'url': page.get('url', ''),
                    'selector': page.get('primarySelector', ''),
                    'anchorPoint': page.get('anchorPoint', ''),
                    'action': action,
                    'textLabels': page.get('textLabels', [])
                })
    
    return steps


def update_path_usage(path_id):
    """
    경로 사용 시 가중치 업데이트
    """
    if not graph:
        return
    
    try:
        # PATH 엔티티 업데이트
        update_path_query = """
        MATCH (path:PATH {pathId: $pathId})
        SET path.totalWeight = path.totalWeight + 1,
            path.usageCount = path.usageCount + 1,
            path.lastUsed = datetime()
        """
        graph.query(update_path_query, {'pathId': path_id})
        
        # 경로상의 모든 관계 업데이트
        update_relations_query = """
        MATCH (path:PATH {pathId: $pathId})-[:CONTAINS]->(page:PAGE)
        MATCH paths = (:ROOT)-[rels:HAS_PAGE|NAVIGATES_TO*]->(page)
        FOREACH (rel IN rels |
            SET rel.weight = coalesce(rel.weight, 0) + 1,
                rel.lastUpdated = datetime()
        )
        """
        graph.query(update_relations_query, {'pathId': path_id})
        
        print(f"경로 사용 추적 완료: {path_id}")
        
    except Exception as e:
        print(f"경로 사용 추적 실패: {e}")


def cleanup_old_paths():
    """
    30일 이상 미사용 경로 정리
    """
    if not graph:
        return
    
    try:
        # 1. 30일 이상 미사용 PATH weight 감소
        decay_query = """
        MATCH (path:PATH)
        WHERE path.lastUsed < datetime() - duration('P30D')
        SET path.totalWeight = CASE 
            WHEN path.totalWeight > 0 THEN path.totalWeight - 1
            ELSE 0
        END
        RETURN count(path) as decayed_count
        """
        decay_result = graph.query(decay_query)
        
        # 2. weight가 0인 PATH 삭제
        delete_paths_query = """
        MATCH (path:PATH)
        WHERE path.totalWeight <= 0
        WITH path, path.pathId as pathId
        DETACH DELETE path
        RETURN count(pathId) as deleted_paths
        """
        delete_result = graph.query(delete_paths_query)
        
        # 3. weight가 0인 관계 삭제
        delete_relations_query = """
        MATCH ()-[rel:HAS_PAGE|NAVIGATES_TO|NAVIGATES_TO_CROSS_DOMAIN]->()
        WHERE rel.weight <= 0
        DELETE rel
        RETURN count(rel) as deleted_relations
        """
        rel_result = graph.query(delete_relations_query)
        
        # 4. 고립된 PAGE 노드 삭제
        cleanup_pages_query = """
        MATCH (page:PAGE)
        WHERE NOT (page)<-[:HAS_PAGE|NAVIGATES_TO]-()
          AND NOT (page)-[:NAVIGATES_TO]->()
          AND NOT (:PATH)-[:CONTAINS]->(page)
        DELETE page
        RETURN count(page) as deleted_pages
        """
        page_result = graph.query(cleanup_pages_query)
        
        print(f"정리 완료:")
        print(f"  - 가중치 감소: {decay_result[0]['decayed_count']}개 경로")
        print(f"  - 삭제된 PATH: {delete_result[0]['deleted_paths']}개")
        print(f"  - 삭제된 관계: {rel_result[0]['deleted_relations']}개")
        print(f"  - 삭제된 PAGE: {page_result[0]['deleted_pages']}개")
        
        return {
            'decayed_paths': decay_result[0]['decayed_count'],
            'deleted_paths': delete_result[0]['deleted_paths'],
            'deleted_relations': rel_result[0]['deleted_relations'],
            'deleted_pages': page_result[0]['deleted_pages']
        }
        
    except Exception as e:
        print(f"경로 정리 실패: {e}")
        return None


def create_vector_indexes():
    """
    벡터 인덱스 생성
    """
    if not graph:
        return
    
    try:
        # PAGE 노드 벡터 인덱스
        page_index_query = """
        CREATE VECTOR INDEX page_embedding IF NOT EXISTS
        FOR (p:PAGE) ON (p.embedding)
        OPTIONS {indexConfig: {
            `vector.dimensions`: 1536,
            `vector.similarity_function`: 'cosine'
        }}
        """
        graph.query(page_index_query)
        print("PAGE 벡터 인덱스 생성 완료")
        
        # PATH 노드 벡터 인덱스
        path_index_query = """
        CREATE VECTOR INDEX path_embedding IF NOT EXISTS
        FOR (p:PATH) ON (p.embedding)
        OPTIONS {indexConfig: {
            `vector.dimensions`: 1536,
            `vector.similarity_function`: 'cosine'
        }}
        """
        graph.query(path_index_query)
        print("PATH 벡터 인덱스 생성 완료")
        
        # 전문 검색 인덱스
        text_indexes = [
            """CREATE FULLTEXT INDEX page_text_search IF NOT EXISTS
               FOR (p:PAGE) ON EACH [p.textLabels]""",
            """CREATE FULLTEXT INDEX path_description_search IF NOT EXISTS
               FOR (p:PATH) ON EACH [p.description]"""
        ]
        
        for index_query in text_indexes:
            graph.query(index_query)
        print("전문 검색 인덱스 생성 완료")
        
        return True
        
    except Exception as e:
        print(f"인덱스 생성 실패: {e}")
        return False