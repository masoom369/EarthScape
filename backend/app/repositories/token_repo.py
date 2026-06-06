from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase


class TokenRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.revoked_tokens

    async def revoke(self, jti: str, expires_at: datetime) -> None:
        await self.collection.insert_one({"jti": jti, "expires_at": expires_at})

    async def is_revoked(self, jti: str) -> bool:
        doc = await self.collection.find_one({"jti": jti})
        return doc is not None
