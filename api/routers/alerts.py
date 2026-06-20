import json
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

from db.redis import redis_client

router = APIRouter(
    prefix="/cache",
    tags=["Redis Cache & Alerts"]
)


class DashboardCacheCreate(BaseModel):
    district_id: str
    total_load_mw: float
    overloaded_transformers: int
    active_faults: int


class FaultAlertCreate(BaseModel):
    alert_id: str
    node_id: str
    severity: str
    message: str


@router.get("/test")
def test_redis():
    redis_client.set("healthcheck", "ok", ex=30)
    value = redis_client.get("healthcheck")

    return {
        "redis_connected": value == "ok",
        "value": value
    }


@router.post("/dashboard")
def cache_dashboard_view(payload: DashboardCacheCreate):
    key = f"dashboard:{payload.district_id}"

    value = {
        "district_id": payload.district_id,
        "total_load_mw": payload.total_load_mw,
        "overloaded_transformers": payload.overloaded_transformers,
        "active_faults": payload.active_faults,
        "cached_at": datetime.utcnow().isoformat()
    }

    redis_client.set(
        key,
        json.dumps(value),
        ex=30
    )

    return {
        "cached": True,
        "key": key,
        "ttl_seconds": 30
    }


@router.get("/dashboard/{district_id}")
def get_cached_dashboard_view(district_id: str):
    key = f"dashboard:{district_id}"
    value = redis_client.get(key)

    if value is None:
        return {
            "cache_hit": False,
            "message": "Dashboard cache expired or not found"
        }

    return {
        "cache_hit": True,
        "dashboard": json.loads(value)
    }


@router.post("/alerts")
def publish_fault_alert(alert: FaultAlertCreate):
    key = f"alert:{alert.alert_id}"

    value = {
        "alert_id": alert.alert_id,
        "node_id": alert.node_id,
        "severity": alert.severity,
        "message": alert.message,
        "created_at": datetime.utcnow().isoformat()
    }

    redis_client.set(
        key,
        json.dumps(value),
        ex=300
    )

    redis_client.lpush("active_alerts", alert.alert_id)
    redis_client.ltrim("active_alerts", 0, 99)

    return {
        "alert_stored": True,
        "alert_id": alert.alert_id,
        "ttl_seconds": 300
    }


@router.get("/alerts")
def list_active_alerts():
    alert_ids = redis_client.lrange("active_alerts", 0, 99)

    alerts = []

    for alert_id in alert_ids:
        value = redis_client.get(f"alert:{alert_id}")
        if value:
            alerts.append(json.loads(value))

    return {
        "active_alerts": alerts
    }