from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


def _serialize(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "model_type": doc["model_type"],
        "trained_at": doc["trained_at"].isoformat(),
        "record_count": doc["record_count"],
        "accuracy_score": doc.get("accuracy_score"),
        "predictions": doc.get("predictions", []),
        "anomaly_record_ids": [str(x) for x in doc.get("anomaly_record_ids", [])],
        "correlation_matrix": doc.get("correlation_matrix"),
        "forecast_data": doc.get("forecast_data"),
        "job_id": str(doc["job_id"]) if doc.get("job_id") else None,
    }


class MLRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.ml_results

    async def create(self, data: dict) -> dict:
        data.setdefault("trained_at", datetime.now(UTC))
        result = await self.collection.insert_one(data)
        doc = await self.collection.find_one({"_id": result.inserted_id})
        return _serialize(doc)  # type: ignore[arg-type]

    async def get_latest_by_type(self, model_type: str) -> dict | None:
        doc = await self.collection.find_one(
            {"model_type": model_type},
            sort=[("trained_at", -1)],
        )
        return _serialize(doc) if doc else None

    async def list_recent(self, limit: int = 10) -> list[dict]:
        cursor = self.collection.find().sort("trained_at", -1).limit(limit)
        return [_serialize(d) async for d in cursor]
