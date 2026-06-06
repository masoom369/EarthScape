from datetime import UTC, datetime

from app.db.mongo import get_db
from app.repositories.support_repo import SupportRepository


class SupportService:
    def __init__(self):
        self.repo = SupportRepository(get_db())

    async def create_ticket(self, data: dict, user_id: str) -> dict:
        return await self.repo.create(data, user_id)

    async def list_tickets(self, page: int, limit: int, user: dict) -> dict:
        is_admin = user["role"] == "admin"
        user_id = None if is_admin else user["id"]
        items, total = await self.repo.list_paginated(page, limit, user_id, is_admin)
        return {"items": items, "total": total, "page": page, "limit": limit}

    async def get_ticket(self, ticket_id: str, user: dict) -> dict | None:
        ticket = await self.repo.find_by_id(ticket_id)
        if not ticket:
            return None
        if user["role"] != "admin" and ticket["submitted_by"] != user["id"]:
            return None
        return ticket

    async def update_ticket(self, ticket_id: str, updates: dict, admin_id: str) -> dict | None:
        patch = dict(updates)
        if patch.get("response"):
            patch["responded_by"] = admin_id
            patch["responded_at"] = datetime.now(UTC)
        return await self.repo.update(ticket_id, patch)