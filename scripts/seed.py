import os
import random
from datetime import datetime, timedelta

from dotenv import load_dotenv
import psycopg2
from pymongo import MongoClient
from neo4j import GraphDatabase
from cassandra.cluster import Cluster


load_dotenv()

POSTGRES_DB = os.getenv("POSTGRES_DB", "gridsense_billing")
POSTGRES_USER = os.getenv("POSTGRES_USER", "gridsense_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "gridsense_pass")
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5433

MONGO_URI = "mongodb://gridsense_admin:gridsense_pass@localhost:27017"

NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "gridsense_pass")
NEO4J_URI = "bolt://localhost:7687"

CASSANDRA_HOST = "localhost"
CASSANDRA_PORT = 9042
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "gridsense")


def seed_postgres():
    print("Seeding PostgreSQL...")

    conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
    )
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO tariffs (tariff_name, price_per_kwh)
        VALUES ('Seed Residential', 0.1800)
        ON CONFLICT DO NOTHING;
    """)

    cur.execute("""
        SELECT tariff_id FROM tariffs
        WHERE tariff_name = 'Seed Residential';
    """)
    tariff_id = cur.fetchone()[0]

    cur.execute("""
        DELETE FROM invoices
        WHERE account_id IN (
            SELECT account_id FROM billing_accounts
            WHERE meter_id LIKE 'SEED-MTR-%'
        );
    """)

    for i in range(1, 101):
        email = f"consumer{i:03d}@example.com"
        meter_id = f"SEED-MTR-{i:03d}"

        cur.execute("""
            INSERT INTO customers (full_name, email, address)
            VALUES (%s, %s, %s)
            ON CONFLICT (email) DO UPDATE
            SET full_name = EXCLUDED.full_name,
                address = EXCLUDED.address
            RETURNING customer_id;
        """, (
            f"Seed Consumer {i:03d}",
            email,
            f"District {((i - 1) % 10) + 1}, Thessaly"
        ))

        customer_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO billing_accounts (customer_id, tariff_id, meter_id, active)
            VALUES (%s, %s, %s, TRUE)
            ON CONFLICT (meter_id) DO UPDATE
            SET customer_id = EXCLUDED.customer_id,
                tariff_id = EXCLUDED.tariff_id,
                active = TRUE
            RETURNING account_id;
        """, (customer_id, tariff_id, meter_id))

        account_id = cur.fetchone()[0]

        kwh = round(250 + (i % 40) * 7.5, 2)
        amount = round(kwh * 0.18, 2)

        cur.execute("""
            INSERT INTO invoices (
                account_id,
                billing_period_start,
                billing_period_end,
                total_kwh,
                amount_due
            )
            VALUES (%s, '2026-05-01', '2026-05-31', %s, %s);
        """, (account_id, kwh, amount))

    conn.commit()
    cur.close()
    conn.close()

    print("PostgreSQL seeded: 100 consumers and invoices.")


def seed_mongo():
    print("Seeding MongoDB...")

    client = MongoClient(MONGO_URI)
    db = client["gridsense_catalog"]
    collection = db["equipment"]

    for i in range(1, 31):
        equipment_type = ["Transformer", "SmartMeter", "Switchgear"][i % 3]
        equipment_id = f"EQ-{i:03d}"

        if equipment_type == "Transformer":
            doc = {
                "equipment_id": equipment_id,
                "type": equipment_type,
                "manufacturer": "Siemens",
                "district": f"District {((i - 1) % 10) + 1}",
                "specifications": {
                    "capacity_kva": 250 + i * 10,
                    "voltage_primary": 20000,
                    "voltage_secondary": 400
                },
                "oil_test": {
                    "last_test_date": "2026-03-01",
                    "status": "normal"
                }
            }

        elif equipment_type == "SmartMeter":
            doc = {
                "equipment_id": equipment_id,
                "type": equipment_type,
                "manufacturer": "Landis+Gyr",
                "district": f"District {((i - 1) % 10) + 1}",
                "firmware": {
                    "version": f"2.{i % 5}.1",
                    "last_update": "2026-04-10"
                },
                "communication": {
                    "protocol": "LoRaWAN",
                    "signal_strength": -70 + (i % 10)
                }
            }

        else:
            doc = {
                "equipment_id": equipment_id,
                "type": equipment_type,
                "manufacturer": "ABB",
                "district": f"District {((i - 1) % 10) + 1}",
                "protection_settings": {
                    "relay_curve": "IEC Normal Inverse",
                    "trip_current_amp": 300 + i
                },
                "maintenance_history": [
                    {
                        "date": "2026-01-15",
                        "notes": "Routine inspection completed"
                    }
                ]
            }

        collection.replace_one(
            {"equipment_id": equipment_id},
            doc,
            upsert=True
        )

    print("MongoDB seeded: 30 equipment records.")


def seed_neo4j():
    print("Seeding Neo4j...")

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )

    query = """
    UNWIND range(1, 10) AS sid
    MERGE (s:Substation {id: 'SEED-SUB-' + toString(sid)})
    SET s.name = 'Seed Substation ' + toString(sid),
        s.district = 'District ' + toString(sid)

    WITH collect(s) AS substations
    UNWIND range(1, 40) AS tid
    WITH substations, tid,
         substations[(tid - 1) % size(substations)] AS s
    MERGE (t:Transformer {id: 'SEED-TX-' + toString(tid)})
    SET t.name = 'Seed Transformer ' + toString(tid),
        t.capacity_kva = 250 + tid * 10,
        t.district = s.district
    MERGE (s)-[:FEEDS]->(t)

    WITH collect(t) AS transformers
    UNWIND range(1, 200) AS mid
    WITH transformers, mid,
         transformers[(mid - 1) % size(transformers)] AS t
    MERGE (m:SmartMeter {id: 'SEED-SM-' + toString(mid)})
    SET m.customer = 'Seed Consumer ' + toString(mid),
        m.status = 'ACTIVE'
    MERGE (t)-[:SUPPLIES]->(m)
    """

    with driver.session() as session:
        session.run(query)

    driver.close()

    print("Neo4j seeded: 10 substations, 40 transformers, 200 meters.")


def seed_cassandra():
    print("Seeding Cassandra...")

    cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
    session = cluster.connect()

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

    insert_by_sensor = session.prepare("""
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """)

    insert_by_minute = session.prepare("""
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """)

    base_time = datetime(2026, 6, 1, 0, 0, 0)
    sensor_ids = [f"SEED-SENSOR-{i:02d}" for i in range(1, 21)]

    total = 0

    for sensor_index, sensor_id in enumerate(sensor_ids):
        district_id = f"District {(sensor_index % 10) + 1}"

        for j in range(2500):
            ts = base_time + timedelta(seconds=j)
            reading_day = ts.date()
            minute_bucket = ts.replace(second=0, microsecond=0)

            voltage = round(random.uniform(220.0, 240.0), 2)
            current = round(random.uniform(5.0, 60.0), 2)
            power_factor = round(random.uniform(0.85, 1.00), 3)
            temperature = round(random.uniform(25.0, 75.0), 2)

            session.execute(
                insert_by_sensor,
                (
                    sensor_id,
                    reading_day,
                    ts,
                    voltage,
                    current,
                    power_factor,
                    temperature,
                    district_id
                )
            )

            session.execute(
                insert_by_minute,
                (
                    minute_bucket,
                    district_id,
                    sensor_id,
                    ts,
                    voltage,
                    current,
                    power_factor,
                    temperature
                )
            )

            total += 1

    cluster.shutdown()

    print(f"Cassandra seeded: {total} sensor readings across 20 sensors.")


def main():
    seed_postgres()
    seed_mongo()
    seed_neo4j()
    seed_cassandra()
    print("All seed data inserted successfully.")


if __name__ == "__main__":
    main()