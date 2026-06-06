from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


def _serialize_rule(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "metric": doc["metric"],
        "operator": doc["operator"],
        "threshold": doc["threshold"],
        "severity": doc["severity"],
        "is_active": doc["is_active"],
        "created_by": str(doc["created_by"]),
        "created_at": doc["created_at"].isoformat(),
    }


def _serialize_event(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "rule_id": str(doc["rule_id"]),
        "climate_record_id": str(doc["climate_record_id"]),
        "triggered_value": doc["triggered_value"],
        "severity": doc["severity"],
        "acknowledged": doc.get("acknowledged", False),
        "acknowledged_by": str(doc["acknowledged_by"]) if doc.get("acknowledged_by") else None,
        "triggered_at": doc["triggered_at"].isoformat(),
        "notification_log": doc.get("notification_log"),
    }


class AlertRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.rules = db.alert_rules
        self.events = db.alert_events

    async def list_active_rules(self) -> list[dict]:
        cursor = self.rules.find({"is_active": True})
        return [doc async for doc in cursor]

    async def count_active_rules(self) -> int:
        return await self.rules.count_documents({"is_active": True})

    async def list_all_rules(self) -> list[dict]:
        cursor = self.rules.find().sort("created_at", -1)
        return [_serialize_rule(d) async for d in cursor]

    async def create_rule(self, data: dict, created_by: str) -> dict:
        doc = {
            **data,
            "is_active": True,
            "created_by": ObjectId(created_by),
            "created_at": datetime.now(UTC),
        }
        result = await self.rules.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _serialize_rule(doc)

    async def update_rule(self, rule_id: str, updates: dict) -> dict | None:
        if not ObjectId.is_valid(rule_id):
            return None
        result = await self.rules.find_one_and_update(
            {"_id": ObjectId(rule_id)},
            {"$set": updates},
            return_document=True,
        )
        return _serialize_rule(result) if result else None

    async def delete_rule(self, rule_id: str) -> bool:
        if not ObjectId.is_valid(rule_id):
            return False
        result = await self.rules.delete_one({"_id": ObjectId(rule_id)})
        return result.deleted_count > 0

    async def create_event(self, data: dict) -> dict:
        data.setdefault("acknowledged", False)
        data.setdefault("triggered_at", datetime.now(UTC))
        result = await self.events.insert_one(data)
        doc = await self.events.find_one({"_id": result.inserted_id})
        return _serialize_event(doc)  # type: ignore[arg-type]

    async def list_events(
        self, page: int, limit: int, acknowledged: bool | None = None
    ) -> tuple[list[dict], int]:
        f: dict = {}
        if acknowledged is not None:
            f["acknowledged"] = acknowledged
        skip = (page - 1) * limit
        total = await self.events.count_documents(f)
        cursor = self.events.find(f).sort("triggered_at", -1).skip(skip).limit(limit)
        items = [_serialize_event(d) async for d in cursor]
        return items, total

    async def acknowledge_event(self, event_id: str, user_id: str) -> dict | None:
        if not ObjectId.is_valid(event_id):
            return None
        result = await self.events.find_one_and_update(
            {"_id": ObjectId(event_id)},
            {"$set": {"acknowledged": True, "acknowledged_by": ObjectId(user_id)}},
            return_document=True,
        )
        return _serialize_event(result) if result else None
