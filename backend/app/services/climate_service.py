import csv
import io
from datetime import datetime

from app.db.mongo import get_db
from app.repositories.climate_repo import ClimateRepository

EXPORT_CAP = 10000


class ClimateService:
    def __init__(self):
        self.repo = ClimateRepository(get_db())

    def _parse_date(self, date_str: str | None) -> datetime | None:
        if not date_str:
            return None
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

    async def list_records(
        self,
        page: int,
        limit: int,
        region: str | None = None,
        source_type: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        is_anomaly: bool | None = None,
        is_archived: bool = False,
    ) -> dict:
        items = await self.repo.list_paginated(
            page, limit,
            region=region, source_type=source_type,
            from_date=self._parse_date(from_date),
            to_date=self._parse_date(to_date),
            is_anomaly=is_anomaly, is_archived=is_archived,
        )
        total = await self.repo.count_filtered(
            region=region, source_type=source_type,
            from_date=self._parse_date(from_date),
            to_date=self._parse_date(to_date),
            is_anomaly=is_anomaly, is_archived=is_archived,
        )
        return {"items": items, "total": total, "page": page, "limit": limit}

    async def get_summary(
        self, region: str | None, from_date: str | None, to_date: str | None, source_type: str | None
    ) -> dict:
        items = await self.repo.aggregate_summary(
            region=region,
            from_date=self._parse_date(from_date),
            to_date=self._parse_date(to_date),
            source_type=source_type,
        )
        return {"items": items}

    async def get_realtime(self, n: int = 100) -> list[dict]:
        return await self.repo.get_recent_sensor(n)

    async def export_csv(self, **filters) -> str:
        total = await self.repo.count_filtered(
            region=filters.get("region"),
            source_type=filters.get("source_type"),
            from_date=self._parse_date(filters.get("from_date")),
            to_date=self._parse_date(filters.get("to_date")),
            is_anomaly=filters.get("is_anomaly"),
            is_archived=filters.get("is_archived", False),
        )
        if total > EXPORT_CAP:
            raise ValueError(
                f"Export cap exceeded: {total} records match filter. "
                "Narrow criteria to 10,000 or fewer records."
            )
        records = await self.repo.list_for_export(EXPORT_CAP, **{
            k: v for k, v in {
                "region": filters.get("region"),
                "source_type": filters.get("source_type"),
                "from_date": self._parse_date(filters.get("from_date")),
                "to_date": self._parse_date(filters.get("to_date")),
                "is_anomaly": filters.get("is_anomaly"),
                "is_archived": filters.get("is_archived", False),
            }.items()
        })
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "id", "source_type", "region", "timestamp",
            "temperature_c", "precipitation_mm", "humidity_pct", "co2_ppm",
            "is_anomaly", "is_archived",
        ])
        writer.writeheader()
        for rec in records:
            writer.writerow({
                "id": rec["id"],
                "source_type": rec["source_type"],
                "region": rec["location"]["region"],
                "timestamp": rec["timestamp"],
                "temperature_c": rec.get("temperature_c"),
                "precipitation_mm": rec.get("precipitation_mm"),
                "humidity_pct": rec.get("humidity_pct"),
                "co2_ppm": rec.get("co2_ppm"),
                "is_anomaly": rec.get("is_anomaly"),
                "is_archived": rec.get("is_archived"),
            })
        return output.getvalue()
