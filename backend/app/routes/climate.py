from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse

from app.middleware.auth import get_current_user, require_roles
from app.models.climate import ClimateSummaryResponse, PaginatedClimateRecords
from app.services.climate_service import ClimateService

router = APIRouter(prefix="/climate", tags=["climate"])


@router.get("", response_model=PaginatedClimateRecords)
async def list_climate(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    region: str | None = None,
    source_type: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    is_anomaly: bool | None = None,
    is_archived: bool = False,
    _user: dict = Depends(get_current_user),
):
    return await ClimateService().list_records(
        page, limit, region, source_type, from_date, to_date, is_anomaly, is_archived
    )


@router.get("/summary", response_model=ClimateSummaryResponse)
async def climate_summary(
    region: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    source_type: str | None = None,
    _user: dict = Depends(get_current_user),
):
    return await ClimateService().get_summary(region, from_date, to_date, source_type)


@router.get("/realtime")
async def climate_realtime(
    n: int = Query(100, ge=1, le=500),
    _user: dict = Depends(get_current_user),
):
    return {"items": await ClimateService().get_realtime(n)}


@router.get("/export")
async def export_climate(
    region: str | None = None,
    source_type: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    is_anomaly: bool | None = None,
    is_archived: bool = False,
    _user: dict = Depends(require_roles("admin", "analyst")),
):
    try:
        csv_data = await ClimateService().export_csv(
            region=region,
            source_type=source_type,
            from_date=from_date,
            to_date=to_date,
            is_anomaly=is_anomaly,
            is_archived=is_archived,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return PlainTextResponse(
        csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=climate_export.csv"},
    )