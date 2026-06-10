import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)


def get_driver():
    return driver


def init_graph():
    query = """
    MERGE (s:Substation {
        id: 'SUB-1',
        name: 'North Substation',
        district: 'North'
    })

    MERGE (f:Feeder {
        id: 'FDR-1',
        name: 'North Feeder 1',
        district: 'North'
    })

    MERGE (t1:Transformer {
        id: 'TX-1001',
        name: 'Transformer 1001',
        district: 'North',
        capacity_kva: 500
    })

    MERGE (t2:Transformer {
        id: 'TX-1002',
        name: 'Transformer 1002',
        district: 'North',
        capacity_kva: 750
    })

    MERGE (m1:SmartMeter {
        id: 'SM-2045',
        customer: 'Maria Papadopoulou'
    })

    MERGE (m2:SmartMeter {
        id: 'SM-2046',
        customer: 'Nikos Ioannou'
    })

    MERGE (r:Relay {
        id: 'RLY-1',
        name: 'Relay North 1',
        status: 'ACTIVE'
    })

    MERGE (s)-[:FEEDS {
        capacity_amp: 800,
        state: 'CLOSED'
    }]->(f)

    MERGE (f)-[:FEEDS {
        capacity_amp: 500,
        state: 'CLOSED'
    }]->(t1)

    MERGE (f)-[:FEEDS {
        capacity_amp: 600,
        state: 'CLOSED'
    }]->(t2)

    MERGE (t1)-[:SUPPLIES]->(m1)
    MERGE (t2)-[:SUPPLIES]->(m2)

    MERGE (r)-[:PROTECTS]->(f)
    """

    with driver.session() as session:
        session.run(query)


init_graph()