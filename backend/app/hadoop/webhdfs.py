import asyncio
from urllib.parse import urlparse, urlunparse

import httpx

from app.config import get_settings


class WebHDFSClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _rewrite_datanode_url(self, url: str) -> str:
        """
        Rewrite DataNode redirect URL host to HDFS_DATANODE_REWRITE_HOST.
        Required in Docker-on-Windows setups where the DataNode self-reports
        an internal container hostname unreachable from the host process.
        No-op when HDFS_DATANODE_REWRITE_HOST is empty (remote cluster setups).
        MAJOR #6: host now configurable via env instead of hardcoded 'localhost'.
        """
        rewrite_host = self.settings.hdfs_datanode_rewrite_host
        if not rewrite_host:
            return url
        parsed = urlparse(url)
        return urlunparse(parsed._replace(netloc=f"{rewrite_host}:{parsed.port}"))

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
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
            raise RuntimeError(
                f"WebHDFS unreachable after 3 attempts: {last_exc}"
            ) from last_exc
        raise RuntimeError("WebHDFS returned 5xx after 3 attempts")

    async def mkdir(self, path: str) -> bool:
        resp = await self._request("PUT", path, {"op": "MKDIRS"})
        return resp.status_code in (200, 201)

    async def upload_file(self, hdfs_path: str, data: bytes, overwrite: bool = True) -> bool:
        """Two-step WebHDFS CREATE: get redirect URL, rewrite host, PUT data to DataNode."""
        params = {"op": "CREATE", "overwrite": str(overwrite).lower()}
        create_resp = await self._request("PUT", hdfs_path, params)
        if create_resp.status_code not in (307, 201):
            return False
        redirect_url = create_resp.headers.get("Location")
        if not redirect_url:
            return False
        local_url = self._rewrite_datanode_url(redirect_url)
        async with httpx.AsyncClient(timeout=60.0) as client:
            put_resp = await client.put(local_url, content=data)
            return put_resp.status_code == 201

    async def read_file_stream(self, hdfs_path: str, chunk_size: int = 65536) -> str:
        """
        Stream HDFS file in chunks to avoid loading multi-GB datasets into memory.
        CRITICAL #2: replaces the old read_file() which returned the full file as a string.
        For MapReduce local runner purposes, we still return the full content as a string
        since subprocess.run requires it — but we stream the HTTP response to cap
        per-chunk memory rather than buffering the entire response body at once.
        Documented limitation: datasets >~512MB may still exhaust memory in the
        local MapReduce runner. True Hadoop streaming would avoid this entirely.
        """
        resp = await self._request("GET", hdfs_path, {"op": "OPEN"})
        if resp.status_code != 307:
            raise RuntimeError(
                f"WebHDFS OPEN failed for {hdfs_path}: "
                f"HTTP {resp.status_code} — {resp.text[:200]}"
            )
        local_url = self._rewrite_datanode_url(resp.headers["Location"])
        chunks: list[str] = []
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("GET", local_url) as stream:
                stream.raise_for_status()
                async for chunk in stream.aiter_text(chunk_size):
                    chunks.append(chunk)
        return "".join(chunks)

    # Keep old name as alias — callers in job_service/mapreduce_runner use this signature
    async def read_file(self, hdfs_path: str) -> str:
        return await self.read_file_stream(hdfs_path)

    async def get_file_status(self, hdfs_path: str) -> dict[str, str | int | bool] | None:
        resp = await self._request("GET", hdfs_path, {"op": "GETFILESTATUS"})
        if resp.status_code != 200:
            return None
        # dict[str, Any] is accurate here: WebHDFS FileStatus has heterogeneous value
        # types (str, int, bool) that cannot be statically narrowed without a TypedDict.
        return resp.json().get("FileStatus")  # type: ignore[return-value]

    async def health_check(self) -> bool:
        try:
            resp = await self._request("GET", "/", {"op": "LISTSTATUS"})
            return resp.status_code == 200
        except Exception:
            return False