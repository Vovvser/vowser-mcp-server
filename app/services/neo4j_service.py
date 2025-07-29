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
                    SET rel.weight = coalesce(rel.weight, 0) + 1
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
                        SET rel.weight = coalesce(rel.weight, 0) + 1
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
                    SET rel.weight = coalesce(rel.weight, 0) + 1
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
            SET rel.weight = coalesce(rel.weight, 0) + 1
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
    MATCH (r:ROOT)
    MATCH (p:PAGE)
    OPTIONAL MATCH (r)-[hp:HAS_PAGE]->()
    OPTIONAL MATCH ()-[nt:NAVIGATES_TO]->()
    OPTIONAL MATCH ()-[ntcd:NAVIGATES_TO_CROSS_DOMAIN]->()
    RETURN
        count(DISTINCT r) as root_count,
        count(DISTINCT p) as page_count,
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
                print(f"\n{'  ' * (current_depth-1)}📍 깊이 {current_depth}:")
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