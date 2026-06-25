"""
Database seeder for EarthScape Climate Agency.
Runs automatically on startup when climate_records is empty. Idempotent.

Boot pipeline (first boot only):
  1. Seed users, 82,170 climate records (2021-01-01..2025-12-31), alert
     rules, alert events, support tickets.
  2. Write seed data to HDFS:
       /earthscape/seed/climate_seed.csv   <- temperature_agg, precipitation_totals
       /earthscape/seed/climate_seed.ndjson <- anomaly_scores (one JSON per line)
  3. Auto-train all 3 ML models (reads Mongo — no HDFS dependency).
  4. Auto-run all 3 MapReduce jobs against the appropriate HDFS file:
       temperature_agg      -> climate_seed.csv
       precipitation_totals -> climate_seed.csv
       anomaly_scores       -> climate_seed.ndjson

Steps 3 and 4 are independent: ML always runs, MapReduce only runs if
the corresponding HDFS file was written successfully in step 2.

Docker/Hadoop is assumed to be running before the backend starts.
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

# ── Constants ────────────────────────────────────────────────────────────────

REGIONS: list[dict[str, Any]] = [
    {"name": "Karachi",   "lat": 24.8607, "lon": 67.0011},
    {"name": "Lahore",    "lat": 31.5204, "lon": 74.3587},
    {"name": "Islamabad", "lat": 33.6844, "lon": 73.0479},
    {"name": "Quetta",    "lat": 30.1798, "lon": 66.9750},
    {"name": "Peshawar",  "lat": 34.0151, "lon": 71.5249},
]

SOURCE_TYPES = ["weather_station", "satellite", "sensor"]

REGION_BASELINE: dict[str, dict[str, float]] = {
    "Karachi":   {"temp": 28.0, "precip": 1.2, "humidity": 72.0, "co2": 415.0},
    "Lahore":    {"temp": 25.0, "precip": 1.8, "humidity": 60.0, "co2": 418.0},
    "Islamabad": {"temp": 20.0, "precip": 2.5, "humidity": 55.0, "co2": 412.0},
    "Quetta":    {"temp": 18.0, "precip": 0.9, "humidity": 40.0, "co2": 410.0},
    "Peshawar":  {"temp": 23.0, "precip": 1.5, "humidity": 50.0, "co2": 416.0},
}

SEED_START = date(2021, 1, 1)
SEED_END   = date(2025, 12, 31)  # inclusive — fixed 5-year window

# Atmospheric CO2 rises ~2.4 ppm/year — adds visible secular trend across 5
# years so the dashboard's correlation heatmap shows CO2 drift, not flatline.
CO2_ANNUAL_DRIFT = 2.4

SEED_HDFS_CSV   = "/earthscape/seed/climate_seed.csv"
SEED_HDFS_NDJSON = "/earthscape/seed/climate_seed.ndjson"

# Anomaly rate: 0.4% spread uniformly across the full range. Previously
# clustered in last 500 rows — 4+ years of the scatter plot showed nothing.
ANOMALY_RATE = 0.004

_rng = random.Random(42)  # fixed seed → reproducible data across re-seeds


# ── Record generation ────────────────────────────────────────────────────────

def _make_record(
    region: dict[str, Any],
    ts: datetime,
    source_type: str,
    ingestion_id: ObjectId,
    created_at: datetime,
    is_anomaly: bool = False,
) -> dict:
    b = REGION_BASELINE[region["name"]]
    doy = ts.timetuple().tm_yday
    years = (ts.date() - SEED_START).days / 365.25

    temp = round(
        b["temp"]
        + 8.0 * math.sin(2 * math.pi * doy / 365)   # seasonal swing ±8°C
        + (_rng.random() - 0.5) * 3.0,               # daily jitter
        2,
    )
    precip = max(
        0.0,
        round(b["precip"] + _rng.random() * 2.0 if _rng.random() > 0.3 else 0.0, 2),
    )
    humidity = min(100.0, max(0.0, round(b["humidity"] + (_rng.random() - 0.5) * 8.0, 1)))
    co2 = round(b["co2"] + years * CO2_ANNUAL_DRIFT + (_rng.random() - 0.5) * 4.0, 1)

    if is_anomaly:
        temp     = round(temp + 18.0, 2)          # heat spike
        humidity = max(0.0, round(humidity - 25.0, 1))

    return {
        "source_type": source_type,
        "location": {"region": region["name"], "lat": region["lat"], "lon": region["lon"]},
        "timestamp": ts,
        "temperature_c": temp,
        "precipitation_mm": precip,
        "humidity_pct": humidity,
        "co2_ppm": co2,
        "is_anomaly": is_anomaly,
        "is_archived": False,
        "ingestion_id": ingestion_id,
        "created_at": created_at,
    }


# ── Serializers ──────────────────────────────────────────────────────────────

def _to_csv_bytes(records: list[dict]) -> bytes:
    """
    Column order matches MapReduce mapper positional index:
      parts[0]=region  parts[1]=timestamp  parts[2]=temperature_c  parts[3]=precipitation_mm
    Both temperature_agg/mapper.py and precipitation_totals/mapper.py rely on
    this exact layout — IngestionService._parse_csv is header-name based
    (robust to order), the mappers are not.
    """
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["region", "timestamp", "temperature_c", "precipitation_mm",
                "humidity_pct", "co2_ppm"])
    for r in records:
        w.writerow([
            r["location"]["region"],
            r["timestamp"].isoformat(),
            r["temperature_c"],
            r["precipitation_mm"],
            r["humidity_pct"],
            r["co2_ppm"],
        ])
    return buf.getvalue().encode("utf-8")


def _to_ndjson_bytes(records: list[dict]) -> bytes:
    """
    One JSON object per line — the format anomaly_scores/mapper.py expects.
    MapReduceRunner._normalize_to_jsonl handles a JSON array too, but NDJSON
    skips the full-file parse/re-serialize and works directly.
    """
    lines = (
        json.dumps({
            "region":           r["location"]["region"],
            "source_type":      r["source_type"],
            "timestamp":        r["timestamp"].isoformat(),
            "temperature_c":    r["temperature_c"],
            "humidity_pct":     r["humidity_pct"],
            "co2_ppm":          r["co2_ppm"],
            "precipitation_mm": r["precipitation_mm"],
            "is_anomaly":       r["is_anomaly"],
        })
        for r in records
    )
    return "\n".join(lines).encode("utf-8")


# ── HDFS ─────────────────────────────────────────────────────────────────────

async def _write_to_hdfs(records: list[dict]) -> tuple[bool, bool]:
    """
    Upload CSV and NDJSON to HDFS. Returns (csv_ok, json_ok) independently
    so a failed JSON write doesn't block the two CSV-backed MapReduce jobs.
    Single WebHDFSClient instance — one connection pool for both uploads.
    """
    hdfs = WebHDFSClient()

    if not await hdfs.health_check():
        logger.warning(
            "seed_hdfs_skipped",
            reason="health_check_failed",
            hint="Hadoop must be running before the backend on first boot.",
        )
        return False, False

    await hdfs.mkdir("/earthscape/seed")

    csv_bytes  = _to_csv_bytes(records)
    json_bytes = _to_ndjson_bytes(records)

    csv_ok = await hdfs.upload_file(SEED_HDFS_CSV, csv_bytes, overwrite=True)
    if csv_ok:
        logger.info("seed_hdfs_written", path=SEED_HDFS_CSV,
                    size_mb=round(len(csv_bytes) / 1_048_576, 2))
    else:
        logger.warning("seed_hdfs_upload_failed", path=SEED_HDFS_CSV)

    json_ok = await hdfs.upload_file(SEED_HDFS_NDJSON, json_bytes, overwrite=True)
    if json_ok:
        logger.info("seed_hdfs_written", path=SEED_HDFS_NDJSON,
                    size_mb=round(len(json_bytes) / 1_048_576, 2))
    else:
        logger.warning("seed_hdfs_upload_failed", path=SEED_HDFS_NDJSON)

    return csv_ok, json_ok


# ── Mongo seeders ────────────────────────────────────────────────────────────

async def _seed_users(db: Any, admin_email: str, admin_password: str) -> dict[str, ObjectId]:
    now = datetime.now(UTC)
    users = [
        {"email": admin_email,              "password": admin_password, "role": "admin"},
        {"email": "analyst@earthscape.com", "password": "Analyst123!", "role": "analyst"},
        {"email": "viewer@earthscape.com",  "password": "Viewer123!",  "role": "viewer"},
    ]
    result: dict[str, ObjectId] = {}
    for u in users:
        existing = await db.users.find_one({"email": u["email"]})
        if existing:
            result[u["email"]] = existing["_id"]
            continue
        ins = await db.users.insert_one({
            "email": u["email"],
            "password_hash": hash_password(u["password"]),
            "role": u["role"],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        })
        result[u["email"]] = ins.inserted_id
        logger.info("seed_user_created", email=u["email"], role=u["role"])
    return result


async def _seed_climate_records(
    db: Any, admin_id: ObjectId
) -> tuple[ObjectId, list[ObjectId], list[dict]]:
    """
    Generate and insert 1826 days × 5 regions × 3 sources × 3 readings = 82,170
    records. Returns raw records list so _write_to_hdfs doesn't re-query Mongo.
    """
    now = datetime.now(UTC)

    existing = await db.ingestion_logs.find_one({"file_hash": "seed_v4_2021_2025"})
    if existing:
        ingestion_id = existing["_id"]
    else:
        res = await db.ingestion_logs.insert_one({
            "filename": "climate_seed.csv",
            "file_hash": "seed_v4_2021_2025",
            "hdfs_path": SEED_HDFS_CSV,
            "format": "csv",
            "record_count": 0,
            "status": "success",
            "error_message": None,
            "triggered_by": admin_id,
            "created_at": now,
        })
        ingestion_id = res.inserted_id

    records: list[dict] = []
    total_days = (SEED_END - SEED_START).days + 1

    for day_offset in range(total_days):
        day = SEED_START + timedelta(days=day_offset)
        base_dt = datetime(day.year, day.month, day.day, tzinfo=UTC)
        for region in REGIONS:
            for source in SOURCE_TYPES:
                for hour in (0, 8, 16):
                    records.append(
                        _make_record(region, base_dt.replace(hour=hour),
                                     source, ingestion_id, now)
                    )

    # Inject anomalies uniformly across the full range
    n_anomalies = max(1, int(len(records) * ANOMALY_RATE))
    anomaly_indices = set(_rng.sample(range(len(records)), n_anomalies))

    for idx in anomaly_indices:
        r = records[idx]
        region_data = next(reg for reg in REGIONS if reg["name"] == r["location"]["region"])
        records[idx] = _make_record(
            region_data, r["timestamp"], r["source_type"],
            ingestion_id, now, is_anomaly=True,
        )

    # Batch insert — keeps per-op BSON within limits on constrained hosts
    inserted_ids: list[ObjectId] = []
    for i in range(0, len(records), 1000):
        res = await db.climate_records.insert_many(records[i : i + 1000])
        inserted_ids.extend(res.inserted_ids)

    anomaly_record_ids = [inserted_ids[i] for i in sorted(anomaly_indices)]

    await db.ingestion_logs.update_one(
        {"_id": ingestion_id}, {"$set": {"record_count": len(records)}}
    )
    logger.info("seed_climate_records_inserted", total=len(records),
                anomalies=n_anomalies, start=SEED_START.isoformat(),
                end=SEED_END.isoformat())

    return ingestion_id, anomaly_record_ids, records


async def _seed_alert_rules(db: Any, admin_id: ObjectId) -> list[ObjectId]:
    now = datetime.now(UTC)
    rules = [
        {"name": "High Temperature Warning", "metric": "temperature_c",    "operator": ">",  "threshold": 40.0,  "severity": "high"},
        {"name": "Low Temperature Alert",    "metric": "temperature_c",    "operator": "<",  "threshold": 5.0,   "severity": "medium"},
        {"name": "Heavy Precipitation",      "metric": "precipitation_mm", "operator": ">",  "threshold": 50.0,  "severity": "medium"},
        {"name": "Elevated CO₂",             "metric": "co2_ppm",          "operator": ">",  "threshold": 430.0, "severity": "low"},
        {"name": "Low Humidity",             "metric": "humidity_pct",     "operator": "<",  "threshold": 20.0,  "severity": "low"},
    ]
    ids: list[ObjectId] = []
    for rule in rules:
        existing = await db.alert_rules.find_one({"name": rule["name"]})
        if existing:
            ids.append(existing["_id"])
            continue
        ins = await db.alert_rules.insert_one(
            {**rule, "is_active": True, "created_by": admin_id, "created_at": now}
        )
        ids.append(ins.inserted_id)
    logger.info("seed_alert_rules_inserted", count=len(ids))
    return ids


async def _seed_alert_events(
    db: Any, rule_ids: list[ObjectId],
    anomaly_ids: list[ObjectId], admin_id: ObjectId,
) -> None:
    now = datetime.now(UTC)
    events = []
    for i, record_id in enumerate(anomaly_ids[:15]):
        ack = i < 5
        events.append({
            "rule_id": rule_ids[i % len(rule_ids)],
            "climate_record_id": record_id,
            "triggered_value": round(45.5 + float(i), 2),
            "severity": ["high", "medium", "low"][i % 3],
            "acknowledged": ack,
            "acknowledged_by": admin_id if ack else None,
            "triggered_at": now - timedelta(hours=i * 3),
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
    viewer_id  = user_ids.get("viewer@earthscape.com")
    analyst_id = user_ids.get("analyst@earthscape.com")
    admin_id   = next(iter(user_ids.values()))
    if not viewer_id or not analyst_id:
        return
    now = datetime.now(UTC)
    tickets = [
        {
            "subject": "Dashboard charts not loading",
            "description": "Temperature trend chart shows empty state after ML training.",
            "screenshot_url": None,
            "status": "resolved",
            "response": "Ensure 90+ days of records exist before training.",
            "responded_by": admin_id,
            "responded_at": now - timedelta(days=1),
            "submitted_by": viewer_id,
            "created_at": now - timedelta(days=3),
            "updated_at": now - timedelta(days=1),
        },
        {
            "subject": "Export CSV cap exceeded",
            "description": "Getting cap exceeded error when exporting all records.",
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
            "description": "Viewer role cannot run ML training.",
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
    for t in tickets:
        if not await db.support_tickets.find_one({"subject": t["subject"]}):
            await db.support_tickets.insert_one(t)
    logger.info("seed_support_tickets_inserted", count=len(tickets))


# ── ML + MapReduce auto-run ───────────────────────────────────────────────────

async def _auto_train_ml(admin_id: ObjectId) -> None:
    """Train all 3 ML models against seeded Mongo data. HDFS not required."""
    from app.services.ml_service import MLService

    ml = MLService()
    for model in ("anomaly_detection", "trend_prediction", "correlation"):
        try:
            await ml.train(model, str(admin_id))
            logger.info("seed_ml_trained", model=model)
        except Exception as exc:
            logger.warning("seed_ml_failed", model=model, error=str(exc))


async def _auto_run_mapreduce(
    admin_id: ObjectId, csv_ok: bool, json_ok: bool
) -> None:
    """
    Run all 3 MapReduce jobs. Each job is independently gated on whether
    its required HDFS file was written — a failed JSON upload skips only
    anomaly_scores, not the two CSV jobs.
    """
    from app.services.job_service import JobService

    svc = JobService()

    job_configs = [
        ("temperature_agg",      "Temperature Aggregation — Seed Run",  SEED_HDFS_CSV,    csv_ok),
        ("precipitation_totals", "Precipitation Totals — Seed Run",     SEED_HDFS_CSV,    csv_ok),
        ("anomaly_scores",       "Anomaly Scores — Seed Run",           SEED_HDFS_NDJSON, json_ok),
    ]

    for job_type, job_name, hdfs_path, available in job_configs:
        if not available:
            logger.warning("seed_mapreduce_skipped", job_type=job_type,
                           reason=f"HDFS file not available: {hdfs_path}")
            continue
        try:
            job_id = await svc.job_repo.create(
                "mapreduce", job_name, str(admin_id),
                hdfs_path,
                f"/earthscape/processed/mapreduce/{job_type}/pending",
            )
            await svc.trigger_mapreduce(
                job_name, job_type, hdfs_path, str(admin_id), str(job_id)
            )
            logger.info("seed_mapreduce_done", job_type=job_type)
        except Exception as exc:
            logger.warning("seed_mapreduce_failed", job_type=job_type, error=str(exc))


# ── Entry point ───────────────────────────────────────────────────────────────

async def run_seed(admin_email: str, admin_password: str) -> None:
    """
    Called from app.main lifespan on every boot.
    Returns immediately if climate_records is non-empty.
    """
    db = get_db()

    count = await db.climate_records.count_documents({})
    if count > 0:
        logger.info("seed_skipped", existing_records=count)
        return

    logger.info("seed_start", start=SEED_START.isoformat(), end=SEED_END.isoformat())

    try:
        # 1 — Mongo
        user_ids = await _seed_users(db, admin_email, admin_password)
        admin_id = user_ids[admin_email]
        _, anomaly_ids, records = await _seed_climate_records(db, admin_id)
        rule_ids = await _seed_alert_rules(db, admin_id)
        await _seed_alert_events(db, rule_ids, anomaly_ids, admin_id)
        await _seed_support_tickets(db, user_ids)

        # 2 — HDFS (Docker assumed running — health_check gates both uploads)
        csv_ok, json_ok = await _write_to_hdfs(records)

        # 3 — ML (Mongo only, always runs)
        await _auto_train_ml(admin_id)

        # 4 — MapReduce (HDFS, per-file gated)
        await _auto_run_mapreduce(admin_id, csv_ok, json_ok)

        logger.info("seed_complete", admin=admin_email)
    except Exception as exc:
        logger.error("seed_failed", error=str(exc))
        raise