"""Seed climate data via the ingestion API."""

import argparse
import asyncio
import sys
from pathlib import Path

import httpx

API_BASE = "http://localhost:8000/api/v1"
DEFAULT_EMAIL = "admin@earthscape.local"
DEFAULT_PASSWORD = "Admin123!"


async def seed_file(filepath: Path, email: str, password: str) -> None:
    async with httpx.AsyncClient(timeout=120.0) as client:
        login = await client.post(
            f"{API_BASE}/auth/login",
            json={"email": email, "password": password},
        )
        if login.status_code != 200:
            print(f"Login failed: {login.text}")
            sys.exit(1)

        content = filepath.read_bytes()
        ext = filepath.suffix.lower()
        mime = {
            ".csv": "text/csv",
            ".json": "application/json",
            ".geojson": "application/geo+json",
        }.get(ext, "application/octet-stream")

        source_type = None
        if "weather" in filepath.name:
            source_type = "weather_station"
        elif "sensor" in filepath.name:
            source_type = "sensor"
        elif "satellite" in filepath.name:
            source_type = "satellite"

        files = {"file": (filepath.name, content, mime)}
        data = {}
        if source_type:
            data["source_type"] = source_type

        resp = await client.post(f"{API_BASE}/ingest/upload", files=files, data=data)
        print(f"Seed {filepath.name}: {resp.status_code} — {resp.text}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--email", default=DEFAULT_EMAIL)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    args = parser.parse_args()
    asyncio.run(seed_file(args.file, args.email, args.password))
