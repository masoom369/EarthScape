import asyncio
from typing import Any

import httpx

from app.config import get_settings


class YARNClient:
    def __init__(self):
        self.settings = get_settings()
        self.base = self.settings.yarn_base_url

    async def new_application(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base}/apps/new-application")
            resp.raise_for_status()
            return resp.json()

    async def submit_application(self, payload: dict) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base}/apps", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def get_application(self, app_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{self.base}/apps/{app_id}")
            resp.raise_for_status()
            return resp.json()

    async def poll_until_finished(
        self, app_id: str, interval: int = 10, max_attempts: int = 60
    ) -> dict[str, Any]:
        for _ in range(max_attempts):
            data = await self.get_application(app_id)
            app = data.get("app", {})
            if app.get("state", "") in ("FINISHED", "FAILED", "KILLED"):
                return app
            await asyncio.sleep(interval)
        return {"state": "TIMEOUT", "finalStatus": "FAILED", "diagnostics": "Polling timeout"}

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base}/metrics")
                return resp.status_code == 200
        except Exception:
            return False