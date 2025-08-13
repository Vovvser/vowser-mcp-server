import os
from dotenv import load_dotenv, find_dotenv
from langchain_neo4j import Neo4jGraph

load_dotenv(find_dotenv())

def get_neo4j_graph():
    try:
        graph = Neo4jGraph(
            url=os.getenv("NEO4J_URI"),
            username=os.getenv("NEO4J_USERNAME"),
            password=os.getenv("NEO4J_PASSWORD"),
        )
        print("Neo4j DB Setup: Database connection successful.")
        return graph
    except Exception as e:
        print(f"Neo4j DB Setup: Database connection failed. Error: {e}")
        return None

def reset_database(graph):
    """
    데이터베이스 초기화
    """
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")
    
    graph.query("MATCH (n) DETACH DELETE n")

    constraints = graph.query("SHOW CONSTRAINTS")
    for constraint in constraints:
        constraint_name = constraint.get("name")
        if constraint_name:
            try:
                graph.query(f"DROP CONSTRAINT {constraint_name}")
            except:
                pass

    indexes = graph.query("SHOW INDEXES")
    for index in indexes:
        index_name = index.get("name")
        index_type = index.get("type")
        if index_name and index_type != "CONSTRAINT":
            try:
                graph.query(f"DROP INDEX {index_name}")
            except:
                pass

    print("데이터베이스가 초기화되었습니다.")

def create_constraints(graph):
    """제약조건 생성"""
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")
    
    constraints = [
        "CREATE CONSTRAINT root_domain_unique IF NOT EXISTS FOR (r:ROOT) REQUIRE r.domain IS UNIQUE",
        "CREATE CONSTRAINT page_id_unique IF NOT EXISTS FOR (p:PAGE) REQUIRE p.pageId IS UNIQUE"
    ]

    for constraint in constraints:
        try:
            graph.query(constraint)
            constraint_name = constraint.split('CREATE CONSTRAINT')[1].split('IF')[0].strip()
            print(f"제약조건 생성: {constraint_name}")
        except Exception as e:
            print(f"제약조건 생성 실패: {e}")

def create_indexes(graph):
    """인덱스 생성"""
    if not graph:
        raise ConnectionError("Neo4j database is not connected.")
    
    indexes = [
        "CREATE INDEX page_url_index IF NOT EXISTS FOR (p:PAGE) ON (p.url)",
        "CREATE INDEX page_domain_index IF NOT EXISTS FOR (p:PAGE) ON (p.domain)",
        "CREATE FULLTEXT INDEX page_search IF NOT EXISTS FOR (p:PAGE) ON EACH [p.textLabels]"
    ]

    for index in indexes:
        try:
            graph.query(index)
            index_name = index.split('CREATE')[1].split('INDEX')[1].split('IF')[0].strip()
            print(f"인덱스 생성: {index_name}")
        except Exception as e:
            print(f"Warning: 인덱스 생성 실패: {e}")

def setup_database(reset=False):
    """
    데이터베이스 초기 설정
    
    Args:
        reset (bool): True이면 기존 데이터를 모두 삭제하고 초기화
    """
    graph = get_neo4j_graph()
    
    if not graph:
        print("데이터베이스 연결 실패로 설정을 완료할 수 없습니다.")
        return False
    
    try:
        if reset:
            print("데이터베이스 초기화 중...")
            reset_database(graph)
        
        print("제약조건 생성 중...")
        create_constraints(graph)
        
        print("인덱스 생성 중...")
        create_indexes(graph)
        
        print("데이터베이스 설정 완료!")
        return True
        
    except Exception as e:
        print(f"데이터베이스 설정 실패: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    reset = "--reset" in sys.argv
    if reset:
        print("WARNING: 모든 기존 데이터가 삭제됩니다!")
        confirm = input("계속하시겠습니까? (yes/no): ")
        if confirm.lower() != 'yes':
            print("취소되었습니다.")
            sys.exit(0)
    
    setup_database(reset=reset)