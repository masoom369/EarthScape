#!/usr/bin/env python3
"""
Seed MongoDB and HDFS from a local file.
Usage: python scripts/seed.py --file seed_data/weather_stations_2023.csv
Requires backend .env present and MongoDB + HDFS running.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.db.mongo import connect, create_indexes, disconnect
from app.services.auth_service import AuthService
from app.services.ingestion_service import IngestionService


async def seed(filepath: str) -> None:
    await connect()
    await create_indexes()
    settings = get_settings()
    await AuthService().ensure_default_admin(
        settings.default_admin_email, settings.default_admin_password
    )

    from app.repositories.user_repo import UserRepository
    from app.db.mongo import get_db
    admin = await UserRepository(get_db()).find_by_email(settings.default_admin_email)
    if not admin:
        print("ERROR: admin user not found")
        return

    path = Path(filepath)
    content = path.read_bytes()
    service = IngestionService()
    try:
        result = await service.ingest_file(
            path.name,
            content,
            "text/csv" if path.suffix == ".csv" else "application/json",
            str(admin["_id"]),
        )
        print(f"Seeded {result['record_count']} records from {path.name}")
    except ValueError as exc:
        print(f"Skipped {path.name}: {exc}")
    finally:
        await disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(description="EarthScape seed loader")
    parser.add_argument("--file", required=True, help="Path to seed file")
    args = parser.parse_args()
    asyncio.run(seed(args.file))


if __name__ == "__main__":
    main()