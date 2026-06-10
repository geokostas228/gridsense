from fastapi import APIRouter
from db.neo4j import get_driver

router = APIRouter(
    prefix="/grid",
    tags=["Grid Topology"]
)


@router.get("/nodes")
def list_grid_nodes():
    query = """
    MATCH (n)
    RETURN labels(n) AS labels, properties(n) AS properties
    ORDER BY properties.id
    """

    with get_driver().session() as session:
        result = session.run(query)
        nodes = [
            {
                "labels": record["labels"],
                "properties": record["properties"]
            }
            for record in result
        ]

    return {
        "nodes": nodes
    }


@router.get("/fault-impact/{node_id}")
def fault_impact(node_id: str):
    query = """
    MATCH path = (start {id: $node_id})-[:FEEDS|SUPPLIES*1..6]->(affected)
    RETURN
        affected.id AS affected_id,
        labels(affected) AS affected_type,
        length(path) AS distance
    ORDER BY distance, affected_id
    """

    with get_driver().session() as session:
        result = session.run(query, node_id=node_id)
        affected_nodes = [
            {
                "affected_id": record["affected_id"],
                "affected_type": record["affected_type"],
                "distance": record["distance"]
            }
            for record in result
        ]

    return {
        "fault_at": node_id,
        "affected_nodes": affected_nodes
    }


@router.get("/upstream/{node_id}")
def upstream_paths(node_id: str):
    query = """
    MATCH path = (upstream)-[:FEEDS|SUPPLIES*1..6]->(target {id: $node_id})
    RETURN
        upstream.id AS upstream_id,
        labels(upstream) AS upstream_type,
        length(path) AS distance
    ORDER BY distance, upstream_id
    """

    with get_driver().session() as session:
        result = session.run(query, node_id=node_id)
        upstream_nodes = [
            {
                "upstream_id": record["upstream_id"],
                "upstream_type": record["upstream_type"],
                "distance": record["distance"]
            }
            for record in result
        ]

    return {
        "target": node_id,
        "upstream_nodes": upstream_nodes
    }