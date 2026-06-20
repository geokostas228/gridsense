from datetime import datetime, date, timedelta
from typing import List, Union
from fastapi import APIRouter
from db.cassandra import session
from db.redis import redis_client
from models.cassandra import SensorReadingCreate

router = APIRouter(prefix="/sensors", tags=["Sensors"])


@router.post("/readings")
def ingest_readings(payload: Union[SensorReadingCreate, List[SensorReadingCreate]]):
    readings = payload if isinstance(payload, list) else [payload]

    for reading in readings:
        reading_day = reading.ts.date()
        minute_bucket = reading.ts.replace(second=0, microsecond=0)

        session.execute("""
            INSERT INTO sensor_readings_by_sensor (
                sensor_id, reading_day, ts, voltage, current,
                power_factor, temperature, district_id
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            reading.sensor_id, reading_day, reading.ts, reading.voltage,
            reading.current, reading.power_factor, reading.temperature,
            reading.district_id
        ))

        session.execute("""
            INSERT INTO sensor_readings_by_minute (
                minute_bucket, district_id, sensor_id, ts, voltage,
                current, power_factor, temperature
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            minute_bucket, reading.district_id, reading.sensor_id, reading.ts,
            reading.voltage, reading.current, reading.power_factor,
            reading.temperature
        ))

        redis_client.set(
            f"sensor:latest:{reading.sensor_id}",
            reading.model_dump_json(),
            ex=30
        )

    return {"stored": True, "count": len(readings)}


@router.get("/{sensor_id}/readings")
def get_sensor_readings(
    sensor_id: str,
    limit: int = 10,
    from_time: datetime | None = None
):
    day = from_time.date() if from_time else date.today()

    rows = session.execute("""
        SELECT sensor_id, reading_day, ts, voltage, current,
               power_factor, temperature, district_id
        FROM sensor_readings_by_sensor
        WHERE sensor_id = %s
        AND reading_day = %s
        LIMIT %s
    """, (sensor_id, day, limit))

    return {"sensor_id": sensor_id, "readings": list(rows)}


@router.get("/{sensor_id}/summary")
def get_sensor_summary(sensor_id: str):
    cached = redis_client.get(f"sensor:summary:{sensor_id}")

    if cached:
        return {"cache_hit": True, "summary": cached}

    latest = redis_client.get(f"sensor:latest:{sensor_id}")

    summary = {
        "sensor_id": sensor_id,
        "latest_reading": latest,
        "one_hour_stats": {
            "note": "Prototype summary; production version would aggregate Cassandra readings for last hour."
        }
    }

    redis_client.set(f"sensor:summary:{sensor_id}", str(summary), ex=30)

    return {
        "cache_hit": False,
        "summary": summary,
        "ttl_seconds": 30
    }


@router.get("/dashboard/latest")
def get_dashboard_readings(minute_bucket: datetime, district_id: str):
    bucket = minute_bucket.replace(second=0, microsecond=0)

    rows = session.execute("""
        SELECT minute_bucket, district_id, sensor_id, ts, voltage,
               current, power_factor, temperature
        FROM sensor_readings_by_minute
        WHERE minute_bucket = %s
        AND district_id = %s
    """, (bucket, district_id))

    return {
        "minute_bucket": bucket.isoformat(),
        "district_id": district_id,
        "readings": list(rows)
    }