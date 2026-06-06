from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


def _serialize(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "job_type": doc["job_type"],
        "job_name": doc["job_name"],
        "status": doc["status"],
        "hdfs_input": doc.get("hdfs_input"),
        "hdfs_output": doc.get("hdfs_output"),
        "duration_seconds": doc.get("duration_seconds"),
        "triggered_by": str(doc["triggered_by"]),
        "started_at": doc["started_at"].isoformat(),
        "completed_at": doc["completed_at"].isoformat() if doc.get("completed_at") else None,
        "error": doc.get("error"),
    }


class JobRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.job_logs

    async def create(
        self,
        job_type: str,
        job_name: str,
        triggered_by: str,
        hdfs_input: str | None = None,
        hdfs_output: str | None = None,
    ) -> ObjectId:
        now = datetime.now(UTC)
        doc = {
            "job_type": job_type,
            "job_name": job_name,
            "status": "queued",
            "hdfs_input": hdfs_input,
            "hdfs_output": hdfs_output,
            "duration_seconds": None,
            "triggered_by": ObjectId(triggered_by),
            "started_at": now,
            "completed_at": None,
            "error": None,
        }
        result = await self.collection.insert_one(doc)
        return result.inserted_id

    async def update_status(
        self,
        job_id: ObjectId | str,
        status: str,
        error: str | None = None,
        duration_seconds: int | None = None,
        hdfs_output: str | None = None,
    ) -> None:
        oid = ObjectId(job_id) if isinstance(job_id, str) else job_id
        update: dict = {"status": status}
        if status in ("completed", "failed"):
            update["completed_at"] = datetime.now(UTC)
        if error:
            update["error"] = error
        if duration_seconds is not None:
            update["duration_seconds"] = duration_seconds
        if hdfs_output:
            update["hdfs_output"] = hdfs_output
        await self.collection.update_one({"_id": oid}, {"$set": update})

    async def find_by_id(self, job_id: str) -> dict | None:
        if not ObjectId.is_valid(job_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(job_id)})
        return _serialize(doc) if doc else None

    async def list_paginated(self, page: int, limit: int) -> tuple[list[dict], int]:
        skip = (page - 1) * limit
        total = await self.collection.count_documents({})
        cursor = self.collection.find().sort("started_at", -1).skip(skip).limit(limit)
        items = [_serialize(d) async for d in cursor]
        return items, total

    async def count_by_status(self) -> dict[str, int]:
        pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        result: dict[str, int] = {}
        async for doc in self.collection.aggregate(pipeline):
            result[doc["_id"]] = doc["count"]
        return result
