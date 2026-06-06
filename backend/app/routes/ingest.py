from fastapi import (
    APIRouter, BackgroundTasks, Depends, File, Form,
    HTTPException, Query, UploadFile, status,
)
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.jobs.alert_worker import evaluate_record_alerts
from app.middleware.auth import require_roles
from app.models.ingestion import IngestionLogResponse, PaginatedIngestionLogs
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/ingest", tags=["ingest"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_type: str | None = Form(None),
    user: dict = Depends(require_roles("admin", "analyst")),
):
    content = await file.read()
    try:
        result = await IngestionService().ingest_file(
            file.filename or "upload",
            content,
            file.content_type or "",
            user["id"],
            source_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    # Fire alert evaluation for sensor records only, with correct MongoDB-assigned IDs
    for rec, inserted_id in result.get("records_with_ids", []):
        if rec.get("source_type") == "sensor":
            background_tasks.add_task(evaluate_record_alerts, rec, inserted_id)

    return {
        "id": result["id"],
        "filename": result["filename"],
        "record_count": result["record_count"],
        "hdfs_path": result["hdfs_path"],
        "status": result["status"],
    }


@router.get("/logs", response_model=PaginatedIngestionLogs)
async def list_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    _user: dict = Depends(require_roles("admin", "analyst")),
):
    return await IngestionService().list_logs(page, limit)


@router.get("/logs/{log_id}", response_model=IngestionLogResponse)
async def get_log(
    log_id: str,
    _user: dict = Depends(require_roles("admin", "analyst")),
):
    log = await IngestionService().get_log(log_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    return log