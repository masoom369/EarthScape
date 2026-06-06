from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect() -> None:
    global _client, _db
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongo_uri)
    _db = _client[settings.mongo_db]
    await _client.admin.command("ping")


async def disconnect() -> None:
    global _client, _db
    if _client:
        _client.close()
    _client = None
    _db = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("MongoDB not connected")
    return _db


async def create_indexes() -> None:
    """Create all collection indexes programmatically on startup."""
    db = get_db()

    await db.users.create_index("email", unique=True)

    await db.climate_records.create_index([("timestamp", -1)])
    await db.climate_records.create_index([("location.region", 1), ("timestamp", -1)])
    await db.climate_records.create_index([("source_type", 1), ("timestamp", -1)])
    await db.climate_records.create_index("is_anomaly")
    await db.climate_records.create_index("is_archived")

    await db.ingestion_logs.create_index("file_hash", unique=True)

    await db.job_logs.create_index("status")
    await db.job_logs.create_index([("triggered_by", 1), ("started_at", -1)])

    await db.ml_results.create_index([("model_type", 1), ("trained_at", -1)])

    await db.alert_events.create_index([("acknowledged", 1), ("triggered_at", -1)])
    await db.alert_events.create_index("rule_id")

    await db.support_tickets.create_index([("submitted_by", 1), ("created_at", -1)])
    await db.support_tickets.create_index("status")

    await db.revoked_tokens.create_index("jti", unique=True)
    await db.revoked_tokens.create_index("expires_at", expireAfterSeconds=0)
