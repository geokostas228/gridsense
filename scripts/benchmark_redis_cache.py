import csv
import os
import statistics
import time

import requests
import redis
from dotenv import load_dotenv


load_dotenv()

BASE_URL = "http://localhost:8000"
SENSOR_ID = "SEED-SENSOR-01"
REQUESTS_PER_BATCH = 500

REDIS_HOST = "localhost"
REDIS_PORT = 6380
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")


def percentile(values, p):
    values = sorted(values)
    index = int((p / 100) * (len(values) - 1))
    return values[index]


def run_batch(label, clear_cache_before_each_request=False):
    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True
    )

    latencies = []
    cache_hits = 0
    errors = 0

    for _ in range(REQUESTS_PER_BATCH):
        if clear_cache_before_each_request:
            r.delete(f"sensor:summary:{SENSOR_ID}")

        start = time.perf_counter()

        try:
            response = requests.get(
                f"{BASE_URL}/sensors/{SENSOR_ID}/summary",
                timeout=10
            )

            if response.status_code != 200:
                errors += 1
            else:
                data = response.json()
                if data.get("cache_hit") is True:
                    cache_hits += 1

        except Exception:
            errors += 1

        end = time.perf_counter()
        latencies.append((end - start) * 1000)

    return {
        "batch": label,
        "requests": REQUESTS_PER_BATCH,
        "p50_latency_ms": round(statistics.median(latencies), 3),
        "p95_latency_ms": round(percentile(latencies, 95), 3),
        "p99_latency_ms": round(percentile(latencies, 99), 3),
        "cache_hit_rate": round(cache_hits / REQUESTS_PER_BATCH, 3),
        "errors": errors
    }


def main():
    os.makedirs("results", exist_ok=True)

    print("Running cold-cache batch...")
    cold = run_batch(
        label="cold_cache",
        clear_cache_before_each_request=True
    )
    print(cold)

    print("Running warm-cache batch...")
    warm = run_batch(
        label="warm_cache",
        clear_cache_before_each_request=False
    )
    print(warm)

    path = "results/redis_cache_results.csv"

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "batch",
                "requests",
                "p50_latency_ms",
                "p95_latency_ms",
                "p99_latency_ms",
                "cache_hit_rate",
                "errors"
            ]
        )
        writer.writeheader()
        writer.writerow(cold)
        writer.writerow(warm)

    print(f"Saved results to {path}")


if __name__ == "__main__":
    main()