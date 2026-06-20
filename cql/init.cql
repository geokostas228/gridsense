CREATE KEYSPACE IF NOT EXISTS gridsense
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE gridsense;

CREATE TABLE IF NOT EXISTS sensor_readings_by_sensor (
    sensor_id text,
    reading_day date,
    ts timestamp,
    voltage double,
    current double,
    power_factor double,
    temperature double,
    district_id text,
    PRIMARY KEY ((sensor_id, reading_day), ts)
) WITH CLUSTERING ORDER BY (ts DESC);

CREATE TABLE IF NOT EXISTS sensor_readings_by_minute (
    minute_bucket timestamp,
    district_id text,
    sensor_id text,
    ts timestamp,
    voltage double,
    current double,
    power_factor double,
    temperature double,
    PRIMARY KEY ((minute_bucket, district_id), ts, sensor_id)
) WITH CLUSTERING ORDER BY (ts DESC);