from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.middleware.auth import get_current_user, require_roles
from app.models.alert import (
    AlertEventResponse,
    AlertRuleCreate,
    AlertRuleResponse,
    AlertRuleUpdate,
    PaginatedAlertEvents,
)
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/rules", response_model=list[AlertRuleResponse])
async def list_rules(_user: dict = Depends(get_current_user)):
    return await AlertService().list_rules()


@router.post("/rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    body: AlertRuleCreate,
    user: dict = Depends(require_roles("admin")),
):
    return await AlertService().create_rule(body.model_dump(), user["id"])


@router.patch("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_rule(
    rule_id: str,
    body: AlertRuleUpdate,
    _user: dict = Depends(require_roles("admin")),
):
    result = await AlertService().update_rule(rule_id, body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return result


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: str,
    _user: dict = Depends(require_roles("admin")),
):
    if not await AlertService().delete_rule(rule_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")


@router.get("/events", response_model=PaginatedAlertEvents)
async def list_events(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    acknowledged: bool | None = None,
    _user: dict = Depends(get_current_user),
):
    return await AlertService().list_events(page, limit, acknowledged)


@router.patch("/events/{event_id}/acknowledge", response_model=AlertEventResponse)
async def acknowledge_event(
    event_id: str,
    user: dict = Depends(get_current_user),
):
    result = await AlertService().acknowledge_event(event_id, user["id"])
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return result