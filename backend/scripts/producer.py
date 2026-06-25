#!/usr/bin/env python3
"""
Synthetic sensor data producer.
Posts JSON climate records to the ingest endpoint at a configurable interval.
Usage: python scripts/producer.py --interval 10 --url http://localhost:8000/api/ingest/upload
"""

import argparse
import json
import random
import time
from datetime import UTC, datetime

import httpx

REGIONS = ["Karachi", "Lahore", "Islamabad", "Quetta", "Peshawar"]

BASE_TEMP: dict[str, float] = {
    "Karachi": 28.0,
    "Lahore": 24.0,
    "Islamabad": 18.0,
    "Quetta": 15.0,
    "Peshawar": 20.0,
}


def generate_record(region: str) -> dict:
    base = BASE_TEMP[region]
    return {
        "region": region,
        "source_type": "sensor",
        "timestamp": datetime.now(UTC).isoformat(),
        "temperature_c": round(base + random.uniform(-5.0, 5.0), 2),
        "humidity_pct": round(random.uniform(30.0, 90.0), 2),
        "co2_ppm": round(random.uniform(380.0, 450.0), 2),
        "precipitation_mm": round(random.uniform(0.0, 20.0), 2),
    }


def post_record(url: str, token: str, record: dict) -> None:
    payload = json.dumps([record]).encode("utf-8")
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(
            url,
            files={"file": ("realtime.json", payload, "application/json")},
            data={"source_type": "sensor"},
            headers={"Cookie": f"access_token={token}"},
        )
    if resp.status_code not in (200, 201):
        print(f"[producer] warn: {resp.status_code} {resp.text[:120]}")
    else:
        print(f"[producer] posted region={record['region']} ts={record['timestamp']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="EarthScape synthetic sensor producer")
    parser.add_argument("--interval", type=int, default=10, help="Seconds between records")
    parser.add_argument(
        "--url",
        default="http://localhost:8000/api/ingest/upload",
        help="Ingest endpoint URL",
    )
    parser.add_argument("--token", required=True, help="JWT access_token cookie value")
    args = parser.parse_args()

    print(f"[producer] starting — interval={args.interval}s url={args.url}")
    while True:
        region = random.choice(REGIONS)
        record = generate_record(region)
        try:
            post_record(args.url, args.token, record)
        except Exception as exc:
            print(f"[producer] error: {exc}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()