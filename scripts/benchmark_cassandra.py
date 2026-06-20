import os
import time
import statistics
from datetime import datetime, timedelta

from dotenv import load_dotenv
from cassandra.cluster import Cluster
from cassandra import ConsistencyLevel
from cassandra.query import SimpleStatement


load_dotenv()

CASSANDRA_HOST = "localhost"
CASSANDRA_PORT = 9042
KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "gridsense")

CONSISTENCY_LEVELS = {
    "ONE": ConsistencyLevel.ONE,
    "LOCAL_QUORUM": ConsistencyLevel.LOCAL_QUORUM,
    "ALL": ConsistencyLevel.ALL,
}

EVENTS_PER_LEVEL = 3000


def percentile(values, p):
    values = sorted(values)
    index = int((p / 100) * (len(values) - 1))
    return values[index]


def run_benchmark():
    cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
    session = cluster.connect(KEYSPACE)

    insert_cql = """
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
    """

    prepared = session.prepare(insert_cql)

    results = []

    for level_name, level_value in CONSISTENCY_LEVELS.items():
        print(f"Testing consistency level: {level_name}")

        statement = prepared
        statement.consistency_level = level_value

        latencies_ms = []
        errors = 0

        start = time.perf_counter()
        base_time = datetime.utcnow()

        for i in range(EVENTS_PER_LEVEL):
            ts = base_time + timedelta(milliseconds=i)
            reading_day = ts.date()

            params = (
                f"BENCH-SENSOR-{level_name}",
                reading_day,
                ts,
                230.0 + (i % 5),
                10.0 + (i % 3),
                0.95,
                40.0 + (i % 10),
                "Benchmark"
            )

            op_start = time.perf_counter()

            try:
                session.execute(statement, params)
            except Exception as exc:
                errors += 1

            op_end = time.perf_counter()
            latencies_ms.append((op_end - op_start) * 1000)

        end = time.perf_counter()
        total_time = end - start
        throughput = EVENTS_PER_LEVEL / total_time

        result = {
            "consistency_level": level_name,
            "events": EVENTS_PER_LEVEL,
            "throughput_events_per_sec": round(throughput, 2),
            "p50_latency_ms": round(percentile(latencies_ms, 50), 3),
            "p95_latency_ms": round(percentile(latencies_ms, 95), 3),
            "errors": errors
        }

        results.append(result)
        print(result)

    cluster.shutdown()

    os.makedirs("results", exist_ok=True)

    with open("results/cassandra_results.csv", "w") as f:
        f.write("consistency_level,events,throughput_events_per_sec,p50_latency_ms,p95_latency_ms,errors\n")
        for r in results:
            f.write(
                f"{r['consistency_level']},{r['events']},"
                f"{r['throughput_events_per_sec']},"
                f"{r['p50_latency_ms']},"
                f"{r['p95_latency_ms']},"
                f"{r['errors']}\n"
            )

    print("Saved results to results/cassandra_results.csv")


if __name__ == "__main__":
    run_benchmark()