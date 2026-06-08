"""
Database seeder for EarthScape Climate Agency.
Runs automatically on startup when the database is empty (zero climate_records).
Idempotent: safe to call on every boot — exits immediately if data exists.
Auto-trains all three ML models after seeding so dashboard charts populate immediately.
"""

import math
import random
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from bson import ObjectId

from app.db.mongo import get_db
from app.middleware.auth import hash_password

logger = structlog.get_logger()

REGIONS = [
    {"name": "Karachi",    "lat": 24.8607, "lon": 67.0011},
    {"name": "Lahore",     "lat": 31.5204, "lon": 74.3587},
    {"name": "Islamabad",  "lat": 33.6844, "lon": 73.0479},
    {"name": "Quetta",     "lat": 30.1798, "lon": 66.9750},
    {"name": "Peshawar",   "lat": 34.0151, "lon": 71.5249},
]

SOURCE_TYPES = ["weather_station", "satellite", "sensor"]

# Realistic baselines: temp_c, precip_mm per reading (not per month), humidity_pct, co2_ppm
REGION_BASELINE: dict[str, dict[str, float]] = {
    "Karachi":   {"temp": 28.0, "precip": 1.2,  "humidity": 72.0, "co2": 415.0},
    "Lahore":    {"temp": 25.0, "precip": 1.8,  "humidity": 60.0, "co2": 418.0},
    "Islamabad": {"temp": 20.0, "precip": 2.5,  "humidity": 55.0, "co2": 412.0},
    "Quetta":    {"temp": 18.0, "precip": 0.9,  "humidity": 40.0, "co2": 410.0},
    "Peshawar":  {"temp": 23.0, "precip": 1.5,  "humidity": 50.0, "co2": 416.0},
}

_rng = random.Random(42)  # seeded for reproducibility


def _make_climate_record(
    region: dict[str, Any],
    ts: datetime,
    source_type: str,
    ingestion_id: ObjectId,
    now: datetime,
    is_anomaly: bool = False,
) -> dict:
    baseline = REGION_BASELINE[region["name"]]
    day_of_year = ts.timetuple().tm_yday

    # Seasonal sine wave ±8°C over the year
    seasonal_offset = 8.0 * math.sin(2 * math.pi * day_of_year / 365)
    # Gaussian jitter via Box-Muller approximation using seeded rng
    temp_jitter = (_rng.random() - 0.5) * 3.0
    precip_jitter = _rng.random() * 2.0
    humid_jitter = (_rng.random() - 0.5) * 8.0
    co2_jitter = (_rng.random() - 0.5) * 4.0

    temp = round(baseline["temp"] + seasonal_offset + temp_jitter, 2)
    # Realistic per-reading precipitation: 0–6 mm, occasionally 0 on dry days
    precip = max(0.0, round(baseline["precip"] + precip_jitter if _rng.random() > 0.3 else 0.0, 2))
    humidity = min(100.0, max(0.0, round(baseline["humidity"] + humid_jitter, 1)))
    co2 = round(baseline["co2"] + co2_jitter, 1)

    if is_anomaly:
        # Realistic heat anomaly: +18°C spike, humidity drop
        temp = round(temp + 18.0, 2)
        humidity = max(0.0, round(humidity - 25.0, 1))

    return {
        "source_type": source_type,
        "location": {
            "region": region["name"],
            "lat": region["lat"],
            "lon": region["lon"],
        },
        "timestamp": ts,
        "temperature_c": temp,
        "precipitation_mm": precip,
        "humidity_pct": humidity,
        "co2_ppm": co2,
        "is_anomaly": is_anomaly,
        "is_archived": False,
        "ingestion_id": ingestion_id,
        "created_at": now,
    }


async def _seed_users(db: Any, admin_email: str, admin_password: str) -> dict[str, ObjectId]:
    users_to_seed = [
        {"email": admin_email,               "password": admin_password, "role": "admin"},
        {"email": "analyst@earthscape.com",  "password": "Analyst123!", "role": "analyst"},
        {"email": "viewer@earthscape.com",   "password": "Viewer123!",  "role": "viewer"},
    ]
    result: dict[str, ObjectId] = {}
    now = datetime.now(UTC)
    for u in users_to_seed:
        existing = await db.users.find_one({"email": u["email"]})
        if existing:
            result[u["email"]] = existing["_id"]
            continue
        doc = {
            "email": u["email"],
            "password_hash": hash_password(u["password"]),
            "role": u["role"],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        ins = await db.users.insert_one(doc)
        result[u["email"]] = ins.inserted_id
        logger.info("seed_user_created", email=u["email"], role=u["role"])
    return result


async def _seed_climate_records(
    db: Any, admin_id: ObjectId
) -> tuple[ObjectId, list[ObjectId]]:
    """Seed 365 days × 5 regions × 3 sources × 3 readings/day = 16,425 records."""
    now = datetime.now(UTC)

    existing_log = await db.ingestion_logs.find_one(
        {"file_hash": "seed_data_v2_realistic_precip"}
    )
    if existing_log:
        ingestion_id = existing_log["_id"]
    else:
        ingestion_doc = {
            "filename": "seed_data.csv",
            "file_hash": "seed_data_v2_realistic_precip",
            "hdfs_path": "/earthscape/seed/climate_seed.csv",
            "format": "csv",
            "record_count": 0,
            "status": "success",
            "error_message": None,
            "triggered_by": admin_id,
            "created_at": now,
        }
        ins = await db.ingestion_logs.insert_one(ingestion_doc)
        ingestion_id = ins.inserted_id

    records: list[dict] = []
    base_date = now - timedelta(days=365)

    for day_offset in range(365):
        day = base_date + timedelta(days=day_offset)
        for region in REGIONS:
            for source in SOURCE_TYPES:
                for hour in (0, 8, 16):
                    ts = day.replace(hour=hour, minute=0, second=0, microsecond=0)
                    records.append(_make_climate_record(region, ts, source, ingestion_id, now))

    # Inject 25 realistic anomalies in the most recent 500 records
    anomaly_indices = _rng.sample(range(len(records) - 500, len(records)), 25)
    anomaly_record_ids: list[ObjectId] = []

    for idx in anomaly_indices:
        r = records[idx]
        region_data = next(
            reg for reg in REGIONS if reg["name"] == r["location"]["region"]
        )
        records[idx] = _make_climate_record(
            region_data, r["timestamp"], r["source_type"], ingestion_id, now, is_anomaly=True
        )

    # Batch insert in chunks of 1000
    inserted_ids: list[ObjectId] = []
    for i in range(0, len(records), 1000):
        chunk = records[i : i + 1000]
        result = await db.climate_records.insert_many(chunk)
        inserted_ids.extend(result.inserted_ids)

    for idx in anomaly_indices:
        anomaly_record_ids.append(inserted_ids[idx])

    await db.ingestion_logs.update_one(
        {"_id": ingestion_id},
        {"$set": {"record_count": len(records)}},
    )

    logger.info(
        "seed_climate_records_inserted",
        total=len(records),
        anomalies=len(anomaly_record_ids),
    )
    return ingestion_id, anomaly_record_ids


async def _seed_alert_rules(db: Any, admin_id: ObjectId) -> list[ObjectId]:
    rules = [
        {"name": "High Temperature Warning", "metric": "temperature_c",    "operator": ">",  "threshold": 40.0, "severity": "high"},
        {"name": "Low Temperature Alert",    "metric": "temperature_c",    "operator": "<",  "threshold": 5.0,  "severity": "medium"},
        {"name": "Heavy Precipitation",      "metric": "precipitation_mm", "operator": ">",  "threshold": 50.0, "severity": "medium"},
        {"name": "Elevated CO₂",             "metric": "co2_ppm",          "operator": ">",  "threshold": 430.0,"severity": "low"},
        {"name": "Low Humidity",             "metric": "humidity_pct",     "operator": "<",  "threshold": 20.0, "severity": "low"},
    ]
    now = datetime.now(UTC)
    inserted_ids: list[ObjectId] = []
    for rule in rules:
        existing = await db.alert_rules.find_one({"name": rule["name"]})
        if existing:
            inserted_ids.append(existing["_id"])
            continue
        doc = {**rule, "is_active": True, "created_by": admin_id, "created_at": now}
        ins = await db.alert_rules.insert_one(doc)
        inserted_ids.append(ins.inserted_id)
    logger.info("seed_alert_rules_inserted", count=len(inserted_ids))
    return inserted_ids


async def _seed_alert_events(
    db: Any,
    rule_ids: list[ObjectId],
    anomaly_record_ids: list[ObjectId],
    admin_id: ObjectId,
) -> None:
    now = datetime.now(UTC)
    events: list[dict] = []
    for i, record_id in enumerate(anomaly_record_ids[:15]):
        rule_id = rule_ids[i % len(rule_ids)]
        triggered_at = now - timedelta(hours=i * 3)
        acknowledged = i < 5
        events.append({
            "rule_id": rule_id,
            "climate_record_id": record_id,  # ObjectId — CRITICAL #1 fix
            "triggered_value": round(45.5 + float(i), 2),
            "severity": "high" if i % 3 == 0 else ("medium" if i % 3 == 1 else "low"),
            "acknowledged": acknowledged,
            "acknowledged_by": admin_id if acknowledged else None,
            "triggered_at": triggered_at,
            "notification_log": {
                "rule_name": f"Seed Alert {i}",
                "metric": "temperature_c",
                "triggered_value": round(45.5 + float(i), 2),
                "severity": "high",
                "record_id": str(record_id),
            },
        })
    if events:
        await db.alert_events.insert_many(events)
        logger.info("seed_alert_events_inserted", count=len(events))


async def _seed_support_tickets(db: Any, user_ids: dict[str, ObjectId]) -> None:
    viewer_id = user_ids.get("viewer@earthscape.com")
    analyst_id = user_ids.get("analyst@earthscape.com")
    admin_id = user_ids.get(next(iter(user_ids)))
    if not viewer_id or not analyst_id:
        return
    now = datetime.now(UTC)
    tickets = [
        {
            "subject": "Dashboard charts not loading",
            "description": "The temperature trend chart shows empty state even after training ML models.",
            "screenshot_url": None,
            "status": "resolved",
            "response": "Ensure at least 90 days of climate records are ingested before training.",
            "responded_by": admin_id,
            "responded_at": now - timedelta(days=1),
            "submitted_by": viewer_id,
            "created_at": now - timedelta(days=3),
            "updated_at": now - timedelta(days=1),
        },
        {
            "subject": "Export CSV cap exceeded",
            "description": "Trying to export all records but getting a cap exceeded error.",
            "screenshot_url": None,
            "status": "in-progress",
            "response": "Apply region and date filters to stay under the 10k cap.",
            "responded_by": admin_id,
            "responded_at": now - timedelta(hours=4),
            "submitted_by": analyst_id,
            "created_at": now - timedelta(days=1),
            "updated_at": now - timedelta(hours=4),
        },
        {
            "subject": "Request access to Jobs page",
            "description": "I am a viewer role but need to run ML training.",
            "screenshot_url": None,
            "status": "open",
            "response": None,
            "responded_by": None,
            "responded_at": None,
            "submitted_by": viewer_id,
            "created_at": now - timedelta(hours=6),
            "updated_at": now - timedelta(hours=6),
        },
    ]
    for ticket in tickets:
        existing = await db.support_tickets.find_one({"subject": ticket["subject"]})
        if not existing:
            await db.support_tickets.insert_one(ticket)
    logger.info("seed_support_tickets_inserted", count=len(tickets))


async def _seed_job_logs(db: Any, admin_id: ObjectId) -> list[ObjectId]:
    now = datetime.now(UTC)
    jobs = [
        {
            "job_type": "mapreduce",
            "job_name": "Temperature Aggregation — Seed Run",
            "status": "completed",
            "hdfs_input": "/earthscape/seed/climate_seed.csv",
            "hdfs_output": "/earthscape/processed/mapreduce/temperature_agg/seed",
            "duration_seconds": 12,
            "triggered_by": admin_id,
            "started_at": now - timedelta(hours=2),
            "completed_at": now - timedelta(hours=1, minutes=48),
            "error": None,
        },
        {
            "job_type": "mapreduce",
            "job_name": "Precipitation Totals — Seed Run",
            "status": "completed",
            "hdfs_input": "/earthscape/seed/climate_seed.csv",
            "hdfs_output": "/earthscape/processed/mapreduce/precipitation_totals/seed",
            "duration_seconds": 9,
            "triggered_by": admin_id,
            "started_at": now - timedelta(hours=1, minutes=30),
            "completed_at": now - timedelta(hours=1, minutes=21),
            "error": None,
        },
    ]
    inserted_ids: list[ObjectId] = []
    for job in jobs:
        existing = await db.job_logs.find_one({"job_name": job["job_name"]})
        if not existing:
            ins = await db.job_logs.insert_one(job)
            inserted_ids.append(ins.inserted_id)
        else:
            inserted_ids.append(existing["_id"])
    logger.info("seed_job_logs_inserted", count=len(jobs))
    return inserted_ids


async def _auto_train_ml_models(admin_id: ObjectId) -> None:
    """
    Run all three ML models synchronously after seeding so dashboard charts
    are populated on first boot. Failures are logged but never re-raised —
    the app starts regardless.
    """
    # Import here to avoid circular import at module level
    from app.services.ml_service import MLService

    ml = MLService()
    for model_type in ("anomaly_detection", "trend_prediction", "correlation"):
        try:
            await ml.train(model_type, str(admin_id))
            logger.info("seed_ml_trained", model_type=model_type)
        except Exception as exc:
            # Insufficient data, sklearn issue, etc — log and continue
            logger.warning("seed_ml_train_failed", model_type=model_type, error=str(exc))


async def run_seed(admin_email: str, admin_password: str) -> None:
    """
    Entry point. Checks if database is empty before seeding.
    'Empty' = zero documents in climate_records.
    Safe to call on every startup: returns immediately if data present.
    After seeding, auto-trains all ML models so dashboard charts have data.
    """
    db = get_db()

    existing_count = await db.climate_records.count_documents({})
    if existing_count > 0:
        logger.info("seed_skipped", reason="climate_records_not_empty", count=existing_count)
        return

    logger.info("seed_start", reason="database_empty")

    try:
        user_ids = await _seed_users(db, admin_email, admin_password)
        admin_id = user_ids[admin_email]

        ingestion_id, anomaly_record_ids = await _seed_climate_records(db, admin_id)
        rule_ids = await _seed_alert_rules(db, admin_id)
        await _seed_alert_events(db, rule_ids, anomaly_record_ids, admin_id)
        await _seed_support_tickets(db, user_ids)
        await _seed_job_logs(db, admin_id)

        # Auto-train ML models so dashboard charts are populated immediately
        await _auto_train_ml_models(admin_id)

        logger.info("seed_complete", admin_email=admin_email)
    except Exception as exc:
        logger.error("seed_failed", error=str(exc))
        # Never re-raise — seeding failure must not block app startup