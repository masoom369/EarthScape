from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


def _serialize(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "subject": doc["subject"],
        "description": doc["description"],
        "screenshot_url": doc.get("screenshot_url"),
        "status": doc["status"],
        "response": doc.get("response"),
        "responded_by": str(doc["responded_by"]) if doc.get("responded_by") else None,
        "responded_at": doc["responded_at"].isoformat() if doc.get("responded_at") else None,
        "submitted_by": str(doc["submitted_by"]),
        "created_at": doc["created_at"].isoformat(),
        "updated_at": doc["updated_at"].isoformat(),
    }


class SupportRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.support_tickets

    async def create(self, data: dict, submitted_by: str) -> dict:
        now = datetime.now(UTC)
        doc = {
            **data,
            "status": "open",
            "response": None,
            "responded_by": None,
            "responded_at": None,
            "submitted_by": ObjectId(submitted_by),
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _serialize(doc)

    async def find_by_id(self, ticket_id: str) -> dict | None:
        if not ObjectId.is_valid(ticket_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(ticket_id)})
        return _serialize(doc) if doc else None

    async def list_paginated(
        self, page: int, limit: int, user_id: str | None = None, is_admin: bool = False
    ) -> tuple[list[dict], int]:
        f: dict = {}
        if not is_admin and user_id:
            f["submitted_by"] = ObjectId(user_id)
        skip = (page - 1) * limit
        total = await self.collection.count_documents(f)
        cursor = self.collection.find(f).sort("created_at", -1).skip(skip).limit(limit)
        items = [_serialize(d) async for d in cursor]
        return items, total

    async def update(self, ticket_id: str, updates: dict) -> dict | None:
        if not ObjectId.is_valid(ticket_id):
            return None
        updates["updated_at"] = datetime.now(UTC)
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(ticket_id)},
            {"$set": updates},
            return_document=True,
        )
        return _serialize(result) if result else None