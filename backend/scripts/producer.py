"""Synthetic climate sensor data producer — posts JSON to ingestion API."""

import argparse
import asyncio
import os
import random
import uuid
from datetime import UTC, datetime

import httpx

REGIONS = ["Karachi", "Lahore", "Islamabad"]
API_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1/ingest/upload")
INTERVAL = int(os.getenv("REALTIME_PRODUCER_INTERVAL", "10"))


def generate_record() -> dict:
    region = random.choice(REGIONS)
    return {
        "record_id": str(uuid.uuid4()),
        "region": region,
        "timestamp": datetime.now(UTC).isoformat(),
        "temperature_c": round(random.gauss(30, 5), 2),
        "humidity_pct": round(random.uniform(40, 85), 2),
        "co2_ppm": round(random.gauss(415, 20), 2),
        "precipitation_mm": round(max(0, random.gauss(1, 3)), 2),
    }


async def post_record(client: httpx.AsyncClient, email: str, password: str) -> None:
    import json

    record = generate_record()
    content = (json.dumps(record) + "\n").encode()
    login_resp = await client.post(
        f"{API_URL.rsplit('/ingest', 1)[0]}/auth/login",
        json={"email": email, "password": password},
    )
    if login_resp.status_code != 200:
        print(f"Login failed: {login_resp.text}")
        return
    files = {"file": ("sensor_event.json", content, "application/json")}
    data = {"source_type": "sensor"}
    resp = await client.post(API_URL, files=files, data=data)
    print(f"[{datetime.now(UTC).isoformat()}] Posted sensor record — status {resp.status_code}")


async def run(interval: int, email: str, password: str) -> None:
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            try:
                await post_record(client, email, password)
            except Exception as exc:
                print(f"Error: {exc}")
            await asyncio.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=INTERVAL)
    parser.add_argument("--email", default="admin@earthscape.local")
    parser.add_argument("--password", default="Admin123!")
    args = parser.parse_args()
    asyncio.run(run(args.interval, args.email, args.password))
