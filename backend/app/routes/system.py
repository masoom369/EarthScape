from fastapi import APIRouter, Depends

from app.db.mongo import get_db
from app.hadoop.webhdfs import WebHDFSClient
from app.hadoop.yarn import YARNClient
from app.middleware.auth import require_roles
from app.models.common import HealthResponse, MetricsResponse
from app.repositories.alert_repo import AlertRepository
from app.repositories.job_repo import JobRepository

router = APIRouter(tags=["system"])
_request_count = 0


def increment_request_count():
    global _request_count
    _request_count += 1


@router.get("/health", response_model=HealthResponse)
async def health():
    mongo_status = "fail"
    try:
        db = get_db()
        await db.command("ping")
        mongo_status = "ok"
    except Exception:
        pass

    hdfs = WebHDFSClient()
    yarn = YARNClient()
    hdfs_status = "ok" if await hdfs.health_check() else "fail"
    yarn_status = "ok" if await yarn.health_check() else "fail"

    return HealthResponse(mongo=mongo_status, hdfs=hdfs_status, yarn=yarn_status)


@router.get("/metrics", response_model=MetricsResponse)
async def metrics(_user: dict = Depends(require_roles("admin"))):
    job_repo = JobRepository(get_db())
    alert_repo = AlertRepository(get_db())
    return MetricsResponse(
        request_count=_request_count,
        jobs_by_status=await job_repo.count_by_status(),
        active_alert_rules=await alert_repo.count_active_rules(),
    )
