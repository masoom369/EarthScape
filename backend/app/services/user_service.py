from app.db.mongo import get_db
from app.middleware.auth import hash_password
from app.repositories.user_repo import UserRepository


class UserService:
    def __init__(self):
        self.repo = UserRepository(get_db())

    async def list_users(self, page: int, limit: int) -> dict:
        items = await self.repo.list_paginated(page, limit)
        total = await self.repo.count()
        return {"items": items, "total": total, "page": page, "limit": limit}

    async def create_user(self, email: str, password: str, role: str) -> dict:
        if await self.repo.find_by_email(email):
            raise ValueError("Email already registered")
        return await self.repo.create(email, hash_password(password), role)

    async def update_user(self, user_id: str, updates: dict) -> dict | None:
        return await self.repo.update(user_id, updates)

    async def deactivate_user(self, user_id: str) -> dict | None:
        return await self.repo.deactivate(user_id)