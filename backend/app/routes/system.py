from fastapi import APIRouter, Depends

from app.db.mongo import get_db
from app.hadoop.webhdfs import WebHDFSClient
from app.hadoop.yarn import YARNClient
from app.metrics import get_request_count
from app.middleware.auth import require_roles
from app.models.common import HealthResponse, MetricsResponse
from app.repositories.alert_repo import AlertRepository
from app.repositories.job_repo import JobRepository

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health():
    mongo_status = "fail"
    try:
        await get_db().command("ping")
        mongo_status = "ok"
    except Exception:
        pass
    hdfs_status = "ok" if await WebHDFSClient().health_check() else "fail"
    yarn_status = "ok" if await YARNClient().health_check() else "fail"
    return HealthResponse(mongo=mongo_status, hdfs=hdfs_status, yarn=yarn_status)


@router.get("/metrics", response_model=MetricsResponse)
async def metrics(_user: dict = Depends(require_roles("admin"))):
    db = get_db()
    return MetricsResponse(
        request_count=get_request_count(),
        jobs_by_status=await JobRepository(db).count_by_status(),
        active_alert_rules=await AlertRepository(db).count_active_rules(),
    )