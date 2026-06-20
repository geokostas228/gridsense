from datetime import datetime
from pydantic import BaseModel


class SensorReadingCreate(BaseModel):
    sensor_id: str
    district_id: str
    ts: datetime
    voltage: float
    current: float
    power_factor: float
    temperature: float