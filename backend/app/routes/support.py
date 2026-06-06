from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.middleware.auth import get_current_user, require_roles
from app.models.support import PaginatedTickets, TicketCreate, TicketResponse, TicketUpdate
from app.services.support_service import SupportService

router = APIRouter(prefix="/support", tags=["support"])


@router.post("/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    body: TicketCreate,
    user: dict = Depends(get_current_user),
):
    return await SupportService().create_ticket(body.model_dump(), user["id"])


@router.get("/tickets", response_model=PaginatedTickets)
async def list_tickets(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    user: dict = Depends(get_current_user),
):
    return await SupportService().list_tickets(page, limit, user)


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    user: dict = Depends(get_current_user),
):
    ticket = await SupportService().get_ticket(ticket_id, user)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


@router.patch("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    body: TicketUpdate,
    user: dict = Depends(require_roles("admin")),
):
    result = await SupportService().update_ticket(
        ticket_id, body.model_dump(exclude_none=True), user["id"]
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return result