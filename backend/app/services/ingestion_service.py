import csv
import hashlib
import io
import json
from datetime import UTC, datetime
from pathlib import Path

from bson import ObjectId

from app.config import get_settings
from app.db.mongo import get_db
from app.hadoop.webhdfs import WebHDFSClient
from app.repositories.climate_repo import ClimateRepository
from app.repositories.ingestion_repo import IngestionRepository

REGION_COORDS: dict[str, tuple[float, float]] = {
    "Karachi": (24.8607, 67.0011),
    "Lahore": (31.5204, 74.3587),
    "Islamabad": (33.6844, 73.0479),
    "Quetta": (30.1798, 66.9750),
    "Peshawar": (34.0151, 71.5249),
}

VALID_SOURCE_TYPES = {"satellite", "weather_station", "sensor"}
ALLOWED_EXTENSIONS: dict[str, str] = {".csv": "csv", ".json": "json", ".geojson": "geojson"}
ALLOWED_MIME: set[str] = {
    "text/csv",
    "application/csv",
    "application/json",
    "application/geo+json",
    "text/plain",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def _float_or_none(val: object) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(val)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return None


class IngestionService:
    def __init__(self):
        db = get_db()
        self.ingestion_repo = IngestionRepository(db)
        self.climate_repo = ClimateRepository(db)
        self.hdfs = WebHDFSClient()
        self.settings = get_settings()

    def _compute_hash(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def _detect_format(self, filename: str) -> str | None:
        return ALLOWED_EXTENSIONS.get(Path(filename).suffix.lower())

    def _build_record(
        self,
        region: str,
        lat: float,
        lon: float,
        ts: datetime,
        source_type: str,
        log_id: ObjectId,
        now: datetime,
        temperature_c: object = None,
        precipitation_mm: object = None,
        humidity_pct: object = None,
        co2_ppm: object = None,
    ) -> dict:
        return {
            "source_type": source_type,
            "location": {"region": region, "lat": lat, "lon": lon},
            "timestamp": ts,
            "temperature_c": _float_or_none(temperature_c),
            "precipitation_mm": _float_or_none(precipitation_mm),
            "humidity_pct": _float_or_none(humidity_pct),
            "co2_ppm": _float_or_none(co2_ppm),
            "is_anomaly": False,
            "is_archived": False,
            "ingestion_id": log_id,
            "created_at": now,
        }

    def _parse_csv(
        self, content: str, log_id: ObjectId, source_type: str
    ) -> list[dict]:
        reader = csv.DictReader(io.StringIO(content))
        records: list[dict] = []
        now = datetime.now(UTC)
        for row in reader:
            region = row.get("region", "Unknown")
            lat, lon = REGION_COORDS.get(region, (0.0, 0.0))
            try:
                ts = datetime.fromisoformat(
                    (row.get("timestamp") or "").replace("Z", "+00:00")
                )
            except ValueError:
                continue
            records.append(self._build_record(
                region=region, lat=lat, lon=lon, ts=ts,
                source_type=source_type, log_id=log_id, now=now,
                temperature_c=row.get("temperature_c"),
                precipitation_mm=row.get("precipitation_mm"),
                humidity_pct=row.get("humidity_pct"),
                co2_ppm=row.get("co2_ppm"),
            ))
        return records

    def _parse_json_records(
        self, content: str, log_id: ObjectId, source_type: str, is_jsonl: bool
    ) -> list[dict]:
        now = datetime.now(UTC)
        items: list[dict] = []
        if is_jsonl:
            for line in content.strip().split("\n"):
                if line.strip():
                    items.append(json.loads(line))
        else:
            data = json.loads(content)
            items = data if isinstance(data, list) else [data]

        records: list[dict] = []
        for item in items:
            # Strip injected test marker — never written to MongoDB
            item.pop("_injected_anomaly", None)

            region = item.get("region") or (
                item.get("location", {}).get("region", "Unknown")
                if isinstance(item.get("location"), dict)
                else "Unknown"
            )
            loc = item.get("location") if isinstance(item.get("location"), dict) else {}
            lat = loc.get("lat") or REGION_COORDS.get(region, (0.0, 0.0))[0]
            lon = loc.get("lon") or REGION_COORDS.get(region, (0.0, 0.0))[1]

            try:
                ts = datetime.fromisoformat(
                    (item.get("timestamp") or "").replace("Z", "+00:00")
                )
            except ValueError:
                continue

            # Validate source_type from payload — reject unknown values
            raw_st = item.get("source_type", source_type)
            st = raw_st if raw_st in VALID_SOURCE_TYPES else source_type

            records.append(self._build_record(
                region=region, lat=lat, lon=lon, ts=ts,
                source_type=st, log_id=log_id, now=now,
                temperature_c=item.get("temperature_c"),
                precipitation_mm=item.get("precipitation_mm"),
                humidity_pct=item.get("humidity_pct"),
                co2_ppm=item.get("co2_ppm"),
            ))
        return records

    async def ingest_file(
        self,
        filename: str,
        content: bytes,
        content_type: str,
        user_id: str,
        source_type: str | None = None,
    ) -> dict:
        if len(content) > MAX_FILE_SIZE:
            raise ValueError("File exceeds 50 MB limit")
        fmt = self._detect_format(filename)
        if not fmt:
            raise ValueError("Unsupported file format. Allowed: CSV, JSON, GeoJSON")
        if content_type and content_type not in ALLOWED_MIME:
            raise ValueError(f"Unsupported MIME type: {content_type}")

        file_hash = self._compute_hash(content)
        if await self.ingestion_repo.find_by_hash(file_hash):
            raise ValueError("Duplicate file: already ingested")

        log_id = await self.ingestion_repo.create_pending(filename, file_hash, fmt, user_id)

        now = datetime.now(UTC)
        st = source_type or ("weather_station" if fmt == "csv" else "satellite")
        if st not in VALID_SOURCE_TYPES:
            st = "satellite"

        hdfs_path = (
            f"/earthscape/raw/{st}"
            f"/{now.year}/{now.month:02d}/{now.day:02d}/{log_id}.{fmt}"
        )

        try:
            await self.hdfs.mkdir(
                f"/earthscape/raw/{st}/{now.year}/{now.month:02d}/{now.day:02d}"
            )
            if not await self.hdfs.upload_file(hdfs_path, content):
                raise RuntimeError("HDFS upload failed")

            text = content.decode("utf-8")
            if fmt == "csv":
                climate_records = self._parse_csv(text, log_id, st)
            else:
                is_jsonl = "\n" in text.strip() and text.strip().startswith("{")
                climate_records = self._parse_json_records(text, log_id, st, is_jsonl)

            count, inserted_ids = await self.climate_repo.bulk_insert(climate_records)
            await self.ingestion_repo.update_status(log_id, "success", count, hdfs_path)

            return {
                "id": str(log_id),
                "filename": filename,
                "record_count": count,
                "hdfs_path": hdfs_path,
                "status": "success",
                # Pair each raw record dict with its assigned MongoDB id for alert evaluation
                "records_with_ids": list(zip(climate_records, inserted_ids, strict=True)),
            }
        except Exception as exc:
            await self.ingestion_repo.update_status(
                log_id, "failed", 0, error_message=str(exc)
            )
            raise

    async def list_logs(self, page: int, limit: int) -> dict:
        items, total = await self.ingestion_repo.list_paginated(page, limit)
        return {"items": items, "total": total, "page": page, "limit": limit}

    async def get_log(self, log_id: str) -> dict | None:
        return await self.ingestion_repo.find_by_id(log_id)