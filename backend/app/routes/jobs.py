from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.middleware.auth import require_roles
from app.models.job import JobLogResponse, MLTrainRequest, MapReduceJobRequest, PaginatedJobLogs
from app.services.job_service import JobService
from app.services.ml_service import MLService

router = APIRouter(prefix="/jobs", tags=["jobs"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/mapreduce", response_model=JobLogResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("10/minute")
async def trigger_mapreduce(
    request: Request,
    body: MapReduceJobRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_roles("admin", "analyst")),
):
    service = JobService()
    job_id = await service.job_repo.create(
        "mapreduce",
        body.job_name,
        user["id"],
        body.hdfs_input_path,
        f"/earthscape/processed/mapreduce/{body.job_type}/pending",
    )
    background_tasks.add_task(
        service.trigger_mapreduce,
        body.job_name,
        body.job_type,
        body.hdfs_input_path,
        user["id"],
        str(job_id),
    )
    result = await service.job_repo.find_by_id(str(job_id))
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job record missing after creation",
        )
    return result


@router.post("/ml/train", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("10/minute")
async def train_ml(
    request: Request,
    body: MLTrainRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_roles("admin", "analyst")),
):
    background_tasks.add_task(MLService().train, body.model_type, user["id"])
    return {"message": f"ML training started for {body.model_type}"}


@router.get("", response_model=PaginatedJobLogs)
async def list_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    _user: dict = Depends(require_roles("admin", "analyst")),
):
    return await JobService().list_jobs(page, limit)


@router.get("/{job_id}", response_model=JobLogResponse)
async def get_job(
    job_id: str,
    _user: dict = Depends(require_roles("admin", "analyst")),
):
    job = await JobService().get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job