import argparse
import os
import statistics
import sys
import time

from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.main import app
from app.database import engine
from app.models import Base


def _seed(client: TestClient, token: str) -> int:
    auth = {"Authorization": f"Bearer {token}"}
    region_resp = client.post(
        "/regions/",
        headers=auth,
        json={"name": "Leeds", "ons_code": "E08000035", "average_income": 30000},
    )
    if region_resp.status_code != 201:
        raise RuntimeError(f"Failed to seed region: {region_resp.status_code} {region_resp.text}")
    region_id = region_resp.json()["id"]
    prices = [800, 900, 1000, 1100, 1200]
    for i, price in enumerate(prices):
        resp = client.post(
            "/listings/",
            headers=auth,
            json={
                "region_id": region_id,
                "price": price,
                "bedrooms": 1 + (i % 3),
                "listing_type": "rent",
            },
        )
        if resp.status_code != 201:
            raise RuntimeError(f"Failed to seed listing: {resp.status_code} {resp.text}")
    return region_id


def _bench(client: TestClient, path: str, iterations: int) -> dict:
    durations = []
    for _ in range(iterations):
        start = time.perf_counter()
        resp = client.get(path)
        end = time.perf_counter()
        if resp.status_code >= 400:
            raise RuntimeError(f"Endpoint {path} failed with status {resp.status_code}")
        durations.append((end - start) * 1000)

    return {
        "endpoint": path,
        "iterations": iterations,
        "p50_ms": round(statistics.median(durations), 3),
        "p95_ms": round(sorted(durations)[int(iterations * 0.95) - 1], 3),
        "mean_ms": round(statistics.mean(durations), 3),
        "max_ms": round(max(durations), 3),
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark key read endpoints.")
    parser.add_argument("--iterations", type=int, default=50)
    args = parser.parse_args()

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    client = TestClient(app)
    token_resp = client.post("/auth/token", data={"username": "admin", "password": "adminpass"})
    if token_resp.status_code != 200:
        raise RuntimeError(f"Failed to issue token: {token_resp.status_code} {token_resp.text}")
    token = token_resp.json()["access_token"]
    region_id = _seed(client, token)

    endpoints = [
        "/regions/",
        "/listings/?listing_type=rent",
        f"/analytics/regions/{region_id}/median-rent",
        f"/analytics/regions/{region_id}/affordability",
        f"/analytics/regions/{region_id}/price-trend",
    ]

    print("Endpoint benchmark (milliseconds):")
    for path in endpoints:
        result = _bench(client, path, args.iterations)
        print(
            f"- {result['endpoint']}: "
            f"mean={result['mean_ms']}ms p50={result['p50_ms']}ms "
            f"p95={result['p95_ms']}ms max={result['max_ms']}ms"
        )


if __name__ == "__main__":
    main()
