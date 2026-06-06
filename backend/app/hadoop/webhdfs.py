import asyncio
from typing import Any

import httpx

from app.config import get_settings


class WebHDFSClient:
    def __init__(self):
        self.settings = get_settings()

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        content: bytes | None = None,
    ) -> httpx.Response:
        url = f"{self.settings.webhdfs_base_url}{path}"
        base_params = {"user.name": "root", **(params or {})}
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.request(
                        method, url, params=base_params, content=content
                    )
                    if response.status_code < 500:
                        return response
            except httpx.TransportError as exc:
                last_exc = exc
            await asyncio.sleep(2**attempt)
        if last_exc:
            raise RuntimeError(f"WebHDFS unreachable after 3 attempts: {last_exc}") from last_exc
        raise RuntimeError("WebHDFS returned 5xx after 3 attempts")

    async def mkdir(self, path: str) -> bool:
        resp = await self._request("PUT", path, {"op": "MKDIRS"})
        return resp.status_code in (200, 201)

    async def upload_file(self, hdfs_path: str, data: bytes, overwrite: bool = True) -> bool:
        """Two-step WebHDFS CREATE: get redirect URL, then PUT data to DataNode."""
        params = {"op": "CREATE", "overwrite": str(overwrite).lower()}
        create_resp = await self._request("PUT", hdfs_path, params)
        if create_resp.status_code not in (307, 201):
            return False
        redirect_url = create_resp.headers.get("Location")
        if not redirect_url:
            return False
        async with httpx.AsyncClient(timeout=60.0) as client:
            put_resp = await client.put(redirect_url, content=data)
            return put_resp.status_code == 201

    async def read_file(self, hdfs_path: str) -> str:
        """WebHDFS OPEN always redirects 307 to DataNode. Raise on any other status."""
        resp = await self._request("GET", hdfs_path, {"op": "OPEN"})
        if resp.status_code != 307:
            raise RuntimeError(
                f"WebHDFS OPEN failed for {hdfs_path}: "
                f"HTTP {resp.status_code} — {resp.text[:200]}"
            )
        async with httpx.AsyncClient(timeout=60.0) as client:
            redirect = await client.get(resp.headers["Location"])
            redirect.raise_for_status()
            return redirect.text

    async def get_file_status(self, hdfs_path: str) -> dict[str, Any] | None:
        resp = await self._request("GET", hdfs_path, {"op": "GETFILESTATUS"})
        if resp.status_code != 200:
            return None
        return resp.json().get("FileStatus")

    async def health_check(self) -> bool:
        try:
            resp = await self._request("GET", "/", {"op": "LISTSTATUS"})
            return resp.status_code == 200
        except Exception:
            return False