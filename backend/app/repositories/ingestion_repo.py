from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


def _serialize(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "filename": doc["filename"],
        "file_hash": doc["file_hash"],
        "hdfs_path": doc.get("hdfs_path"),
        "format": doc["format"],
        "record_count": doc.get("record_count", 0),
        "status": doc["status"],
        "error_message": doc.get("error_message"),
        "triggered_by": str(doc["triggered_by"]),
        "created_at": doc["created_at"].isoformat(),
    }


class IngestionRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.ingestion_logs

    async def find_by_hash(self, file_hash: str) -> dict | None:
        return await self.collection.find_one({"file_hash": file_hash})

    async def find_by_id(self, log_id: str) -> dict | None:
        if not ObjectId.is_valid(log_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(log_id)})
        return _serialize(doc) if doc else None

    async def create_pending(
        self, filename: str, file_hash: str, fmt: str, triggered_by: str
    ) -> ObjectId:
        doc = {
            "filename": filename,
            "file_hash": file_hash,
            "hdfs_path": None,
            "format": fmt,
            "record_count": 0,
            "status": "pending",
            "error_message": None,
            "triggered_by": ObjectId(triggered_by),
            "created_at": datetime.now(UTC),
        }
        result = await self.collection.insert_one(doc)
        return result.inserted_id

    async def update_status(
        self,
        log_id: ObjectId,
        status: str,
        record_count: int = 0,
        hdfs_path: str | None = None,
        error_message: str | None = None,
    ) -> None:
        update: dict = {"status": status, "record_count": record_count}
        if hdfs_path:
            update["hdfs_path"] = hdfs_path
        if error_message:
            update["error_message"] = error_message
        await self.collection.update_one({"_id": log_id}, {"$set": update})

    async def list_paginated(self, page: int, limit: int) -> tuple[list[dict], int]:
        skip = (page - 1) * limit
        total = await self.collection.count_documents({})
        cursor = self.collection.find().sort("created_at", -1).skip(skip).limit(limit)
        items = [_serialize(d) async for d in cursor]
        return items, total