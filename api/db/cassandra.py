import os
import time
from cassandra.cluster import Cluster
from cassandra.query import dict_factory

CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "timeseries-db")
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "gridsense")


def get_session():
    cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)

    for _ in range(20):
        try:
            session = cluster.connect()
            session.row_factory = dict_factory
            return session
        except Exception:
            time.sleep(3)

    raise RuntimeError("Could not connect to Cassandra")


session = get_session()


def init_cassandra_schema():
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE}
        WITH replication = {{
            'class': 'SimpleStrategy',
            'replication_factor': 1
        }};
    """)

    session.set_keyspace(CASSANDRA_KEYSPACE)

    session.execute("""
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
    """)

    session.execute("""
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
    """)


init_cassandra_schema()