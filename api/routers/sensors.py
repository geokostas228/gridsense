from datetime import datetime, date
from fastapi import APIRouter
from models.cassandra import SensorReadingCreate

from db.cassandra import session

router = APIRouter(
    prefix="/sensors",
    tags=["Sensors"]
)


@router.post("/readings")
def ingest_reading(reading: SensorReadingCreate):
    reading_day = reading.ts.date()
    minute_bucket = reading.ts.replace(second=0, microsecond=0)

    session.execute(
        """
        INSERT INTO sensor_readings_by_sensor (
            sensor_id,
            reading_day,
            ts,
            voltage,
            current,
            power_factor,
            temperature,
            district_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            reading.sensor_id,
            reading_day,
            reading.ts,
            reading.voltage,
            reading.current,
            reading.power_factor,
            reading.temperature,
            reading.district_id
        )
    )

    session.execute(
        """
        INSERT INTO sensor_readings_by_minute (
            minute_bucket,
            district_id,
            sensor_id,
            ts,
            voltage,
            current,
            power_factor,
            temperature
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            minute_bucket,
            reading.district_id,
            reading.sensor_id,
            reading.ts,
            reading.voltage,
            reading.current,
            reading.power_factor,
            reading.temperature
        )
    )

    return {
        "stored": True,
        "sensor_id": reading.sensor_id,
        "reading_day": str(reading_day),
        "minute_bucket": minute_bucket.isoformat()
    }


@router.get("/{sensor_id}/readings")
def get_sensor_readings(sensor_id: str, reading_day: date, limit: int = 10):
    rows = session.execute(
        """
        SELECT sensor_id, reading_day, ts, voltage, current, power_factor, temperature, district_id
        FROM sensor_readings_by_sensor
        WHERE sensor_id = %s
        AND reading_day = %s
        LIMIT %s
        """,
        (sensor_id, reading_day, limit)
    )

    return {
        "sensor_id": sensor_id,
        "readings": list(rows)
    }


@router.get("/dashboard/latest")
def get_dashboard_readings(minute_bucket: datetime, district_id: str):
    bucket = minute_bucket.replace(second=0, microsecond=0)

    rows = session.execute(
        """
        SELECT minute_bucket, district_id, sensor_id, ts, voltage, current, power_factor, temperature
        FROM sensor_readings_by_minute
        WHERE minute_bucket = %s
        AND district_id = %s
        """,
        (bucket, district_id)
    )

    return {
        "minute_bucket": bucket.isoformat(),
        "district_id": district_id,
        "readings": list(rows)
    }