from pydantic import BaseModel
from typing import Any, Dict, Optional


class EquipmentCreate(BaseModel):
    equipment_id: str
    type: str
    manufacturer: str
    district: Optional[str] = None
    metadata: Dict[str, Any] = {}