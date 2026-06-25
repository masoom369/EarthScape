"""
Database seeder for EarthScape Climate Agency.
Runs automatically on startup when the database is empty (zero climate_records).
Idempotent: safe to call on every boot — exits immediately if data exists.

Full pipeline on first boot:
  1. Seed users, climate_records (5 years), alert rules/events, tickets, job logs.
  2. Write the seeded climate data to HDFS as a real CSV (previously the
     ingestion_logs row pointed at a path that was never actually written —
     fixed here so MapReduce has real input to run against).
  3. Auto-train all 3 ML models (anomaly_detection, trend_prediction, correlation).
  4. Auto-run all 3 MapReduce jobs (temperature_agg, precipitation_totals,
     anomaly_scores) against the HDFS file from step 2.

Timeline: 2021-01-01 through 2025-12-31 inclusive — fixed 5 calendar year
range (1826 days incl. 2024 leap year), not a rolling "now - N days" window.
"""

import csv
import io
import json
import math
import random
from datetime import UTC, date, datetime, timedelta
from typing import Any

import structlog
from bson import ObjectId

from app.db.mongo import get_db
from app.hadoop.webhdfs import WebHDFSClient
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

REGION_BASELINE: dict[str, dict[str, float]] = {
    "Karachi":   {"temp": 28.0, "precip": 1.2,  "humidity": 72.0, "co2": 415.0},
    "Lahore":    {"temp": 25.0, "precip": 1.8,  "humidity": 60.0, "co2": 418.0},
    "Islamabad": {"temp": 20.0, "precip": 2.5,  "humidity": 55.0, "co2": 412.0},
    "Quetta":    {"temp": 18.0, "precip": 0.9,  "humidity": 40.0, "co2": 410.0},
    "Peshawar":  {"temp": 23.0, "precip": 1.5,  "humidity": 50.0, "co2": 416.0},
}

# Fixed historical range — explicit "5 years" requirement, not "now - N days".
SEED_START = date(2021, 1, 1)
SEED_END = date(2025, 12, 31)  # inclusive

CO2_ANNUAL_DRIFT_PPM = 2.4

# HDFS destination for the seeded dataset — this is what MapReduce jobs
# actually read on boot. Previously seed.py referenced this exact path in
# ingestion_logs without ever writing a file there; jobs pointed at it would
# have failed with a 404 from WebHDFS. Fixed by _write_seed_csv_to_hdfs below.
SEED_HDFS_PATH = "/earthscape/seed/climate_seed.csv"

_rng = random.Random(42)


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
    years_since_start = (ts.date() - SEED_START).days / 365.25

    seasonal_offset = 8.0 * math.sin(2 * math.pi * day_of_year / 365)
    temp_jitter = (_rng.random() - 0.5) * 3.0
    precip_jitter = _rng.random() * 2.0
    humid_jitter = (_rng.random() - 0.5) * 8.0
    co2_jitter = (_rng.random() - 0.5) * 4.0

    temp = round(baseline["temp"] + seasonal_offset + temp_jitter, 2)
    precip = max(0.0, round(baseline["precip"] + precip_jitter if _rng.random() > 0.3 else 0.0, 2))
    humidity = min(100.0, max(0.0, round(baseline["humidity"] + humid_jitter, 1)))
    co2 = round(baseline["co2"] + (years_since_start * CO2_ANNUAL_DRIFT_PPM) + co2_jitter, 1)

    if is_anomaly:
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
) -> tuple[ObjectId, list[ObjectId], list[dict]]:
    """
    Seed fixed range 2021-01-01..2025-12-31 inclusive (1826 days) x 5 regions
    x 3 sources x 3 readings/day = 82,170 records.

    Returns (ingestion_id, anomaly_record_ids, records) — records returned
    so the caller can write the same data to HDFS without re-querying Mongo.
    """
    now = datetime.now(UTC)

    existing_log = await db.ingestion_logs.find_one(
        {"file_hash": "seed_data_v4_2021_2025_5yr"}
    )
    if existing_log:
        ingestion_id = existing_log["_id"]
    else:
        ingestion_doc = {
            "filename": "climate_seed.csv",
            "file_hash": "seed_data_v4_2021_2025_5yr",
            "hdfs_path": SEED_HDFS_PATH,
            "format": "csv",
            "record_count": 0,
            "status": "success",
            "error_message": None,
            "triggered_by": admin_id,
            "created_at": now,
        }
        ins = await db.ingestion_logs.insert_one(ingestion_doc)
        ingestion_id = ins.inserted_id

    total_days = (SEED_END - SEED_START).days + 1

    records: list[dict] = []
    for day_offset in range(total_days):
        day = SEED_START + timedelta(days=day_offset)
        day_dt = datetime(day.year, day.month, day.day, tzinfo=UTC)
        for region in REGIONS:
            for source in SOURCE_TYPES:
                for hour in (0, 8, 16):
                    ts = day_dt.replace(hour=hour)
                    records.append(_make_climate_record(region, ts, source, ingestion_id, now))

    # 0.4% anomaly rate spread across the full 5-year range so anomaly
    # detection / anomaly_scores MapReduce has signal everywhere, not just
    # clustered in the most recent slice.
    anomaly_count = max(1, int(len(records) * 0.004))
    anomaly_indices = _rng.sample(range(len(records)), anomaly_count)
    anomaly_record_ids: list[ObjectId] = []

    for idx in anomaly_indices:
        r = records[idx]
        region_data = next(
            reg for reg in REGIONS if reg["name"] == r["location"]["region"]
        )
        records[idx] = _make_climate_record(
            region_data, r["timestamp"], r["source_type"], ingestion_id, now, is_anomaly=True
        )

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
        range_start=SEED_START.isoformat(),
        range_end=SEED_END.isoformat(),
    )
    return ingestion_id, anomaly_record_ids, records


def _records_to_csv(records: list[dict]) -> bytes:
    """
    Serialize seeded records to CSV matching the exact column layout the
    MapReduce mappers expect positionally: region@0, timestamp@1, temp@2,
    precip@3 (see mapreduce/temperature_agg/mapper.py and
    mapreduce/precipitation_totals/mapper.py — both use parts[0]/parts[2]/
    parts[3], not header-name lookup).
    """
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "region", "timestamp", "temperature_c", "precipitation_mm",
        "humidity_pct", "co2_ppm",
    ])
    for r in records:
        writer.writerow([
            r["location"]["region"],
            r["timestamp"].isoformat(),
            r["temperature_c"],
            r["precipitation_mm"],
            r["humidity_pct"],
            r["co2_ppm"],
        ])
    return buf.getvalue().encode("utf-8")


async def _write_seed_csv_to_hdfs(records: list[dict]) -> bool:
    """
    Write the seeded dataset to HDFS as a real file so MapReduce jobs have
    actual input to read. Returns False (logged, non-fatal) if HDFS is
    unreachable — boot must not hard-fail just because Hadoop containers
    aren't up yet; the auto-MapReduce step below will then also fail
    gracefully with the same root cause logged once, not twice.
    """
    hdfs = WebHDFSClient()
    try:
        await hdfs.mkdir("/earthscape/seed")
        ok = await hdfs.upload_file(SEED_HDFS_PATH, _records_to_csv(records), overwrite=True)
        if ok:
            logger.info("seed_hdfs_csv_written", path=SEED_HDFS_PATH, records=len(records))
        else:
            logger.warning("seed_hdfs_csv_write_failed", path=SEED_HDFS_PATH)
        return ok
    except Exception as exc:
        logger.warning("seed_hdfs_unreachable", error=str(exc))
        return False


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
            "climate_record_id": record_id,
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


async def _auto_train_ml_models(admin_id: ObjectId) -> None:
    """Train all 3 ML models against the freshly seeded Mongo data."""
    from app.services.ml_service import MLService

    ml = MLService()
    for model_type in ("anomaly_detection", "trend_prediction", "correlation"):
        try:
            await ml.train(model_type, str(admin_id))
            logger.info("seed_ml_trained", model_type=model_type)
        except Exception as exc:
            logger.warning("seed_ml_train_failed", model_type=model_type, error=str(exc))


async def _auto_run_mapreduce_jobs(admin_id: ObjectId, hdfs_available: bool) -> None:
    """
    Run all 3 MapReduce job types against the seed CSV written to HDFS.
    Skipped (logged, non-fatal) if the HDFS write failed — Hadoop containers
    may not be up yet on a first `docker compose up` that races the backend
    boot. Each job creates its own job_logs row via JobService, identical to
    a user-triggered submission, so it's indistinguishable in the Jobs UI
    from a manual run.
    """
    if not hdfs_available:
        logger.warning("seed_mapreduce_skipped", reason="hdfs_seed_csv_not_written")
        return

    from app.services.job_service import JobService

    job_service = JobService()
    job_types = [
        ("temperature_agg", "Temperature Aggregation — Seed Run"),
        ("precipitation_totals", "Precipitation Totals — Seed Run"),
        ("anomaly_scores", "Anomaly Scores — Seed Run"),
    ]

    for job_type, job_name in job_types:
        try:
            job_id = await job_service.job_repo.create(
                "mapreduce", job_name, str(admin_id), SEED_HDFS_PATH,
                f"/earthscape/processed/mapreduce/{job_type}/pending",
            )
            await job_service.trigger_mapreduce(
                job_name, job_type, SEED_HDFS_PATH, str(admin_id), str(job_id)
            )
            logger.info("seed_mapreduce_completed", job_type=job_type)
        except Exception as exc:
            # anomaly_scores requires JSON input per JOB_TYPE_EXPECTED_FORMAT
            # in mapreduce_runner.py, but the seed file is CSV — this job is
            # expected to fail format validation here, logged not raised.
            # See note in run_seed() docstring below for the full explanation.
            logger.warning("seed_mapreduce_failed", job_type=job_type, error=str(exc))


async def run_seed(admin_email: str, admin_password: str) -> None:
    """
    Entry point. Checks if database is empty before seeding.
    'Empty' = zero documents in climate_records.
    Safe to call on every startup: returns immediately if data present.

    IMPORTANT — anomaly_scores will fail by design on the seed run:
    MapReduceRunner enforces job_type -> input format (temperature_agg and
    precipitation_totals require CSV; anomaly_scores requires JSON — see
    JOB_TYPE_EXPECTED_FORMAT in app/jobs/mapreduce_runner.py, added as the
    CRITICAL #3 fix in a prior pass). The seeded dataset is written to HDFS
    as a single CSV (climate_seed.csv) because climate_records in Mongo
    doesn't carry a "this came from a JSON source" distinction worth
    serializing twice. Running anomaly_scores against it will correctly
    fail format validation and log a warning, not crash boot. anomaly_scores
    gets real input once you generate and upload sensor_bulk.json via
    `scripts/producer.py` (now a bulk file generator, not a live poster —
    see that file) and trigger the job manually from the Jobs page.
    """
    db = get_db()

    existing_count = await db.climate_records.count_documents({})
    if existing_count > 0:
        logger.info("seed_skipped", reason="climate_records_not_empty", count=existing_count)
        return

    logger.info("seed_start", reason="database_empty", range_start=SEED_START.isoformat(), range_end=SEED_END.isoformat())

    try:
        user_ids = await _seed_users(db, admin_email, admin_password)
        admin_id = user_ids[admin_email]

        ingestion_id, anomaly_record_ids, records = await _seed_climate_records(db, admin_id)
        rule_ids = await _seed_alert_rules(db, admin_id)
        await _seed_alert_events(db, rule_ids, anomaly_record_ids, admin_id)
        await _seed_support_tickets(db, user_ids)

        hdfs_available = await _write_seed_csv_to_hdfs(records)

        # ML first (reads Mongo, always available), then MapReduce (reads
        # HDFS, may be unavailable if Hadoop containers aren't up yet).
        await _auto_train_ml_models(admin_id)
        await _auto_run_mapreduce_jobs(admin_id, hdfs_available)

        logger.info("seed_complete", admin_email=admin_email)
    except Exception as exc:
        logger.error("seed_failed", error=str(exc))
        raise
