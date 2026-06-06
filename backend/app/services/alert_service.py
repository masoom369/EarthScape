import time

from app.config import get_settings
from app.db.mongo import get_db
from app.repositories.alert_repo import AlertRepository


class AlertService:
    _cache: list[dict] | None = None
    _cache_time: float = 0

    def __init__(self):
        self.repo = AlertRepository(get_db())
        self.settings = get_settings()

    @classmethod
    def invalidate_cache(cls) -> None:
        cls._cache = None
        cls._cache_time = 0

    async def get_active_rules(self) -> list[dict]:
        now = time.time()
        if (
            AlertService._cache is not None
            and now - AlertService._cache_time < self.settings.alert_cache_ttl_seconds
        ):
            return AlertService._cache
        rules = await self.repo.list_active_rules()
        AlertService._cache = rules
        AlertService._cache_time = now
        return rules

    async def list_rules(self) -> list[dict]:
        return await self.repo.list_all_rules()

    async def create_rule(self, data: dict, user_id: str) -> dict:
        rule = await self.repo.create_rule(data, user_id)
        self.invalidate_cache()
        return rule

    async def update_rule(self, rule_id: str, updates: dict) -> dict | None:
        rule = await self.repo.update_rule(rule_id, updates)
        if rule:
            self.invalidate_cache()
        return rule

    async def delete_rule(self, rule_id: str) -> bool:
        deleted = await self.repo.delete_rule(rule_id)
        if deleted:
            self.invalidate_cache()
        return deleted

    async def list_events(self, page: int, limit: int, acknowledged: bool | None) -> dict:
        items, total = await self.repo.list_events(page, limit, acknowledged)
        return {"items": items, "total": total, "page": page, "limit": limit}

    async def acknowledge_event(self, event_id: str, user_id: str) -> dict | None:
        return await self.repo.acknowledge_event(event_id, user_id)
