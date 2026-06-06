from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


def _serialize(doc: dict) -> dict:
    loc = doc.get("location", {})
    return {
        "id": str(doc["_id"]),
        "source_type": doc["source_type"],
        "location": {
            "region": loc.get("region", ""),
            "lat": loc.get("lat"),
            "lon": loc.get("lon"),
        },
        "timestamp": doc["timestamp"].isoformat(),
        "temperature_c": doc.get("temperature_c"),
        "precipitation_mm": doc.get("precipitation_mm"),
        "humidity_pct": doc.get("humidity_pct"),
        "co2_ppm": doc.get("co2_ppm"),
        "is_anomaly": doc.get("is_anomaly", False),
        "is_archived": doc.get("is_archived", False),
        "ingestion_id": str(doc["ingestion_id"]) if doc.get("ingestion_id") else None,
        "created_at": doc["created_at"].isoformat(),
    }


class ClimateRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.climate_records

    def _build_filter(
        self,
        region: str | None = None,
        source_type: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        is_anomaly: bool | None = None,
        is_archived: bool = False,
    ) -> dict:
        f: dict = {"is_archived": is_archived}
        if region:
            f["location.region"] = region
        if source_type:
            f["source_type"] = source_type
        if from_date or to_date:
            f["timestamp"] = {}
            if from_date:
                f["timestamp"]["$gte"] = from_date
            if to_date:
                f["timestamp"]["$lte"] = to_date
        if is_anomaly is not None:
            f["is_anomaly"] = is_anomaly
        return f

    async def bulk_insert(self, records: list[dict]) -> int:
        if not records:
            return 0
        result = await self.collection.insert_many(records)
        return len(result.inserted_ids)

    async def count_filtered(self, **kwargs) -> int:
        return await self.collection.count_documents(self._build_filter(**kwargs))

    async def list_paginated(self, page: int, limit: int, **kwargs) -> list[dict]:
        skip = (page - 1) * limit
        cursor = (
            self.collection.find(self._build_filter(**kwargs))
            .sort("timestamp", -1)
            .skip(skip)
            .limit(limit)
        )
        return [_serialize(d) async for d in cursor]

    async def list_for_export(self, limit: int, **kwargs) -> list[dict]:
        cursor = (
            self.collection.find(self._build_filter(**kwargs))
            .sort("timestamp", -1)
            .limit(limit)
        )
        return [_serialize(d) async for d in cursor]

    async def get_recent_sensor(self, n: int = 100) -> list[dict]:
        cursor = (
            self.collection.find({"source_type": "sensor", "is_archived": False})
            .sort("timestamp", -1)
            .limit(n)
        )
        return [_serialize(d) async for d in cursor]

    async def bulk_update_anomaly_flags(self, record_ids: list[str]) -> int:
        oids = [ObjectId(rid) for rid in record_ids if ObjectId.is_valid(rid)]
        if not oids:
            return 0
        result = await self.collection.update_many(
            {"_id": {"$in": oids}},
            {"$set": {"is_anomaly": True}},
        )
        return result.modified_count

    async def find_for_ml(self, days: int, fields: list[str] | None = None) -> list[dict]:
        since = datetime.now(UTC) - __import__("datetime").timedelta(days=days)
        cursor = self.collection.find(
            {"timestamp": {"$gte": since}, "is_archived": False}
        ).sort("timestamp", 1)
        docs = []
        async for doc in cursor:
            if fields:
                filtered = {k: doc.get(k) for k in fields}
                filtered["_id"] = doc["_id"]
                filtered["location"] = doc.get("location", {})
                filtered["timestamp"] = doc.get("timestamp")
                docs.append(filtered)
            else:
                docs.append(doc)
        return docs

    async def aggregate_summary(
        self,
        region: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        source_type: str | None = None,
    ) -> list[dict]:
        match: dict = {"is_archived": False}
        if region:
            match["location.region"] = region
        if source_type:
            match["source_type"] = source_type
        if from_date or to_date:
            match["timestamp"] = {}
            if from_date:
                match["timestamp"]["$gte"] = from_date
            if to_date:
                match["timestamp"]["$lte"] = to_date

        pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": {
                        "region": "$location.region",
                        "period": {"$dateToString": {"format": "%Y-%m", "date": "$timestamp"}},
                    },
                    "avg_temperature_c": {"$avg": "$temperature_c"},
                    "total_precipitation_mm": {"$sum": "$precipitation_mm"},
                    "record_count": {"$sum": 1},
                    "anomaly_count": {
                        "$sum": {"$cond": [{"$eq": ["$is_anomaly", True]}, 1, 0]}
                    },
                }
            },
            {"$sort": {"_id.period": 1}},
        ]
        results = []
        async for doc in self.collection.aggregate(pipeline):
            results.append({
                "region": doc["_id"]["region"],
                "period": doc["_id"]["period"],
                "avg_temperature_c": doc.get("avg_temperature_c"),
                "total_precipitation_mm": doc.get("total_precipitation_mm"),
                "record_count": doc["record_count"],
                "anomaly_count": doc["anomaly_count"],
            })
        return results
