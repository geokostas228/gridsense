from pydantic import BaseModel
from typing import Optional


class GridNodeCreate(BaseModel):
    node_id: str
    node_type: str
    name: Optional[str] = None
    district: Optional[str] = None


class FaultImpactRequest(BaseModel):
    node_id: str