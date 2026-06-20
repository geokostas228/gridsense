import csv
import json
import os
import statistics
import time

from dotenv import load_dotenv
from pymongo import MongoClient
import psycopg2
from psycopg2.extras import Json


load_dotenv()

MONGO_URI = "mongodb://gridsense_admin:gridsense_pass@localhost:27017"
MONGO_DB = "gridsense_catalog"

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5433

RUNS = 10


def mean_ms(times):
    return round(statistics.mean(times), 4)


def setup_postgres_jsonb():
    mongo = MongoClient(MONGO_URI)
    equipment = list(mongo[MONGO_DB]["equipment"].find({"equipment_id": {"$regex": "^EQ-"}}))

    conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    )

    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS equipment_jsonb (
            asset_id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            metadata JSONB NOT NULL
        );
    """)

    cur.execute("DELETE FROM equipment_jsonb;")

    for doc in equipment:
        doc.pop("_id", None)

        asset_id = doc.get("equipment_id")
        equipment_type = doc.get("type")

        cur.execute("""
            INSERT INTO equipment_jsonb (asset_id, type, metadata)
            VALUES (%s, %s, %s)
            ON CONFLICT (asset_id) DO UPDATE
            SET type = EXCLUDED.type,
                metadata = EXCLUDED.metadata;
        """, (asset_id, equipment_type, Json(doc)))

    conn.commit()
    cur.close()
    conn.close()

    print(f"Copied {len(equipment)} MongoDB equipment records into PostgreSQL JSONB.")


def time_mongo_query(query_name, query_fn):
    times = []

    for _ in range(RUNS):
        start = time.perf_counter()
        list(query_fn())
        end = time.perf_counter()
        times.append((end - start) * 1000)

    return {
        "query": query_name,
        "backend": "MongoDB",
        "mean_latency_ms": mean_ms(times)
    }


def time_postgres_query(query_name, sql):
    times = []

    conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    )

    cur = conn.cursor()

    for _ in range(RUNS):
        start = time.perf_counter()
        cur.execute(sql)
        cur.fetchall()
        end = time.perf_counter()
        times.append((end - start) * 1000)

    cur.close()
    conn.close()

    return {
        "query": query_name,
        "backend": "PostgreSQL JSONB",
        "mean_latency_ms": mean_ms(times)
    }


def main():
    os.makedirs("results", exist_ok=True)

    setup_postgres_jsonb()

    mongo = MongoClient(MONGO_URI)
    collection = mongo[MONGO_DB]["equipment"]

    results = []

    results.append(time_mongo_query(
        "firmware_version starts with 3",
        lambda: collection.find({
            "firmware.version": {"$regex": "^3"}
        })
    ))

    results.append(time_postgres_query(
        "firmware_version starts with 3",
        """
        SELECT *
        FROM equipment_jsonb
        WHERE metadata #>> '{firmware,version}' LIKE '3%';
        """
    ))

    results.append(time_mongo_query(
        "SmartMeter rated_voltage > 230",
        lambda: collection.find({
            "type": "SmartMeter",
            "specifications.rated_voltage": {"$gt": 230}
        })
    ))

    results.append(time_postgres_query(
        "SmartMeter rated_voltage > 230",
        """
        SELECT *
        FROM equipment_jsonb
        WHERE type = 'SmartMeter'
        AND (metadata #>> '{specifications,rated_voltage}')::numeric > 230;
        """
    ))

    results.append(time_mongo_query(
        "count grouped by type",
        lambda: collection.aggregate([
            {"$group": {"_id": "$type", "count": {"$sum": 1}}}
        ])
    ))

    results.append(time_postgres_query(
        "count grouped by type",
        """
        SELECT type, COUNT(*)
        FROM equipment_jsonb
        GROUP BY type;
        """
    ))

    path = "results/mongo_vs_postgres_results.csv"

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["query", "backend", "mean_latency_ms"]
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"Saved results to {path}")

    for row in results:
        print(row)


if __name__ == "__main__":
    main()