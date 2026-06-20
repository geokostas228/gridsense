import csv
import os
import statistics
import time

import requests
import matplotlib.pyplot as plt


BASE_URL = "http://localhost:8000"
NODE_ID = "SEED-SUB-1"
ITERATIONS_PER_DEPTH = 30
MAX_DEPTHS = range(1, 9)


def percentile(values, p):
    values = sorted(values)
    index = int((p / 100) * (len(values) - 1))
    return values[index]


def main():
    os.makedirs("results", exist_ok=True)

    results = []

    for depth in MAX_DEPTHS:
        latencies = []
        errors = 0

        print(f"Testing max_depth={depth}")

        for _ in range(ITERATIONS_PER_DEPTH):
            start = time.perf_counter()

            try:
                response = requests.get(
                    f"{BASE_URL}/grid/fault-impact/{NODE_ID}",
                    params={"max_depth": depth},
                    timeout=10
                )

                if response.status_code != 200:
                    errors += 1

            except Exception:
                errors += 1

            end = time.perf_counter()
            latencies.append((end - start) * 1000)

        median_ms = statistics.median(latencies)
        p95_ms = percentile(latencies, 95)

        row = {
            "max_depth": depth,
            "iterations": ITERATIONS_PER_DEPTH,
            "median_latency_ms": round(median_ms, 3),
            "p95_latency_ms": round(p95_ms, 3),
            "errors": errors
        }

        results.append(row)
        print(row)

    csv_path = "results/neo4j_depth_results.csv"

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "max_depth",
                "iterations",
                "median_latency_ms",
                "p95_latency_ms",
                "errors"
            ]
        )
        writer.writeheader()
        writer.writerows(results)

    depths = [r["max_depth"] for r in results]
    medians = [r["median_latency_ms"] for r in results]
    p95s = [r["p95_latency_ms"] for r in results]

    plt.figure()
    plt.plot(depths, medians, marker="o", label="Median")
    plt.plot(depths, p95s, marker="o", label="P95")
    plt.xlabel("Traversal max_depth")
    plt.ylabel("Latency (ms)")
    plt.title("Neo4j Fault Impact Latency by Traversal Depth")
    plt.legend()
    plt.grid(True)
    plt.savefig("results/neo4j_depth_latency.png")

    print(f"Saved CSV to {csv_path}")
    print("Saved chart to results/neo4j_depth_latency.png")


if __name__ == "__main__":
    main()