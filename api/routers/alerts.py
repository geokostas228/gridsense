import json
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from db.redis import redis_client


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)


class FaultAlertCreate(BaseModel):
    alert_id: str
    node_id: str
    severity: str
    message: str


@router.get("/active")
def active_alerts():
    alert_ids = redis_client.lrange("active_alerts", 0, 99)
    alerts = []

    for alert_id in alert_ids:
        value = redis_client.get(f"alert:{alert_id}")
        if value:
            alerts.append(json.loads(value))

    return {
        "active_alerts": alerts
    }


@router.post("/publish")
def publish_alert(alert: FaultAlertCreate):
    value = {
        "alert_id": alert.alert_id,
        "node_id": alert.node_id,
        "severity": alert.severity,
        "message": alert.message,
        "created_at": datetime.utcnow().isoformat()
    }

    redis_client.set(
        f"alert:{alert.alert_id}",
        json.dumps(value),
        ex=300
    )

    redis_client.lpush("active_alerts", alert.alert_id)
    redis_client.ltrim("active_alerts", 0, 99)

    return {
        "published": True,
        "alert_id": alert.alert_id,
        "ttl_seconds": 300
    }