from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.neo4j import get_driver


router = APIRouter(
    prefix="/grid",
    tags=["Grid Topology"]
)


class GridNodeCreate(BaseModel):
    node_id: str
    node_type: str
    name: str
    district: str | None = None


class GridRelationshipCreate(BaseModel):
    from_id: str
    to_id: str
    relationship_type: str
    feeder_id: str | None = None


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

    return {"nodes": nodes}


@router.post("/nodes")
def add_grid_node(node: GridNodeCreate):
    if node.node_type not in ["Substation", "Transformer", "SmartMeter", "Feeder", "Relay"]:
        raise HTTPException(status_code=400, detail="Unsupported node_type")

    query = f"""
    MERGE (n:{node.node_type} {{id: $node_id}})
    SET n.name = $name,
        n.district = $district
    RETURN labels(n) AS labels, properties(n) AS properties
    """

    with get_driver().session() as session:
        record = session.run(
            query,
            node_id=node.node_id,
            name=node.name,
            district=node.district
        ).single()

    return {
        "created_or_updated": True,
        "node": {
            "labels": record["labels"],
            "properties": record["properties"]
        }
    }


@router.post("/relationships")
def add_grid_relationship(rel: GridRelationshipCreate):
    allowed = ["FEEDS", "SUPPLIES", "CONNECTS_TO", "PROTECTS"]

    if rel.relationship_type not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported relationship_type")

    query = f"""
    MATCH (a {{id: $from_id}})
    MATCH (b {{id: $to_id}})
    MERGE (a)-[r:{rel.relationship_type}]->(b)
    SET r.feeder_id = $feeder_id
    RETURN a.id AS from_id, b.id AS to_id, type(r) AS relationship_type
    """

    with get_driver().session() as session:
        record = session.run(
            query,
            from_id=rel.from_id,
            to_id=rel.to_id,
            feeder_id=rel.feeder_id
        ).single()

    if record is None:
        raise HTTPException(status_code=404, detail="One or both nodes not found")

    return {
        "created_or_updated": True,
        "relationship": {
            "from_id": record["from_id"],
            "to_id": record["to_id"],
            "relationship_type": record["relationship_type"]
        }
    }


@router.get("/fault-impact/{node_id}")
def fault_impact(node_id: str, max_depth: int = 6):
    if max_depth > 10:
        raise HTTPException(status_code=400, detail="max_depth cannot exceed 10")

    exists_query = """
    MATCH (n {id: $node_id})
    RETURN n.id AS id
    """

    query = """
    MATCH path = (start {id: $node_id})-[:FEEDS|SUPPLIES|CONNECTS_TO*1..6]->(affected)
    RETURN
        affected.id AS affected_id,
        labels(affected) AS affected_type,
        length(path) AS distance
    ORDER BY distance, affected_id
    """

    with get_driver().session() as session:
        exists = session.run(exists_query, node_id=node_id).single()
        if exists is None:
            raise HTTPException(status_code=404, detail="Node not found")

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
        "affected_nodes": affected_nodes,
        "total_affected": len(affected_nodes)
    }


@router.get("/restore-paths/{node_id}")
def restore_paths(node_id: str):
    query = """
    MATCH (target {id: $node_id})
    MATCH path = (source:Substation)-[:FEEDS|SUPPLIES|CONNECTS_TO*1..6]->(target)
    RETURN
        source.id AS source_id,
        source.name AS source_name,
        length(path) AS path_length
    ORDER BY path_length
    """

    with get_driver().session() as session:
        result = session.run(query, node_id=node_id)
        paths = [
            {
                "source_id": record["source_id"],
                "source_name": record["source_name"],
                "path_length": record["path_length"]
            }
            for record in result
        ]

    return {
        "node_id": node_id,
        "restore_paths": paths
    }


@router.get("/upstream/{node_id}")
def upstream_paths(node_id: str):
    query = """
    MATCH path = (upstream)-[:FEEDS|SUPPLIES|CONNECTS_TO*1..6]->(target {id: $node_id})
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