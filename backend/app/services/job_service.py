import json
from datetime import UTC, datetime

from bson import ObjectId

from app.db.mongo import get_db
from app.hadoop.webhdfs import WebHDFSClient
from app.jobs.mapreduce_runner import MapReduceRunner
from app.repositories.job_repo import JobRepository
from app.repositories.ml_repo import MLRepository


class JobService:
    def __init__(self):
        db = get_db()
        self.job_repo = JobRepository(db)
        self.ml_repo = MLRepository(db)
        self.hdfs = WebHDFSClient()
        self.runner = MapReduceRunner()

    async def trigger_mapreduce(
        self,
        job_name: str,
        job_type: str,
        hdfs_input: str,
        user_id: str,
        existing_job_id: str,
    ) -> dict:
        job_id = ObjectId(existing_job_id)
        job_id_str = existing_job_id

        try:
            await self.job_repo.update_status(job_id, "running")
            start = datetime.now(UTC)

            app_id, output_path = await self.runner.submit_job(
                job_id_str, job_type, job_name, hdfs_input
            )

            # Local runner completes synchronously — no YARN polling needed.
            # YARN polling only applies when app_id is a real YARN application id.
            duration = int((datetime.now(UTC) - start).total_seconds())

            summary = await self._read_and_parse_output(output_path, job_type)
            await self.ml_repo.create({
                "model_type": f"mapreduce_{job_type}",
                "record_count": len(summary),
                "predictions": summary,
                "job_id": job_id,
            })
            await self.job_repo.update_status(
                job_id, "completed",
                duration_seconds=duration,
                hdfs_output=output_path,
            )
        except Exception as exc:
            await self.job_repo.update_status(job_id, "failed", error=str(exc))

        result = await self.job_repo.find_by_id(job_id_str)
        if result is None:
            raise RuntimeError(f"Job document {job_id_str} missing after update")
        return result

    async def _read_and_parse_output(self, output_path: str, job_type: str) -> list[dict]:
        try:
            content = await self.hdfs.read_file(f"{output_path}/part-00000")
        except Exception:
            return []
        lines = [ln.strip() for ln in content.split("\n") if ln.strip()]
        results: list[dict] = []
        for line in lines:
            parts = line.split("\t")
            match job_type:
                case "temperature_agg" if len(parts) >= 4:
                    results.append({
                        "region": parts[0],
                        "min": float(parts[1]),
                        "max": float(parts[2]),
                        "mean": float(parts[3]),
                    })
                case "precipitation_totals" if len(parts) >= 2:
                    key = parts[0]
                    region, period = key.rsplit("_", 1) if "_" in key else (key, "")
                    results.append({
                        "region": region,
                        "period": period,
                        "total_mm": float(parts[1]),
                    })
                case "anomaly_scores":
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        if len(parts) >= 3:
                            results.append({
                                "record_id": parts[0],
                                "anomaly_score": float(parts[1]),
                                "is_anomaly": parts[2] == "true",
                            })
        return results

    async def list_jobs(self, page: int, limit: int) -> dict:
        items, total = await self.job_repo.list_paginated(page, limit)
        return {"items": items, "total": total, "page": page, "limit": limit}

    async def get_job(self, job_id: str) -> dict | None:
        return await self.job_repo.find_by_id(job_id)

    async def create_ml_job_log(self, job_name: str, user_id: str) -> ObjectId:
        return await self.job_repo.create("ml_train", job_name, user_id)

    async def complete_ml_job(
        self, job_id: ObjectId, status: str, duration: int, error: str | None = None
    ) -> None:
        await self.job_repo.update_status(job_id, status, error=error, duration_seconds=duration)