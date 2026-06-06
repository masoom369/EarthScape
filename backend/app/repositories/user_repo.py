from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


def _serialize(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "email": doc["email"],
        "role": doc["role"],
        "is_active": doc["is_active"],
        "created_at": doc["created_at"].isoformat(),
        "updated_at": doc["updated_at"].isoformat(),
    }


class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.users

    async def find_by_email(self, email: str) -> dict | None:
        return await self.collection.find_one({"email": email.lower()})

    async def find_by_id(self, user_id: str) -> dict | None:
        if not ObjectId.is_valid(user_id):
            return None
        return await self.collection.find_one({"_id": ObjectId(user_id)})

    async def count(self, filter_query: dict | None = None) -> int:
        return await self.collection.count_documents(filter_query or {})

    async def list_paginated(self, page: int, limit: int) -> list[dict]:
        skip = (page - 1) * limit
        cursor = self.collection.find().sort("created_at", -1).skip(skip).limit(limit)
        return [_serialize(d) async for d in cursor]

    async def create(self, email: str, password_hash: str, role: str) -> dict:
        now = datetime.now(UTC)
        doc = {
            "email": email.lower(),
            "password_hash": password_hash,
            "role": role,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _serialize(doc)

    async def update(self, user_id: str, updates: dict) -> dict | None:
        if not ObjectId.is_valid(user_id):
            return None
        updates["updated_at"] = datetime.now(UTC)
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": updates},
            return_document=True,
        )
        return _serialize(result) if result else None

    async def deactivate(self, user_id: str) -> dict | None:
        return await self.update(user_id, {"is_active": False})

    async def count_all(self) -> int:
        return await self.collection.count_documents({})
