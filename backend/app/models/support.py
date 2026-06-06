from typing import Literal

from pydantic import BaseModel, Field

TicketStatus = Literal["open", "in-progress", "resolved"]


class TicketCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    screenshot_url: str | None = None


class TicketUpdate(BaseModel):
    status: TicketStatus | None = None
    response: str | None = None


class TicketResponse(BaseModel):
    id: str
    subject: str
    description: str
    screenshot_url: str | None = None
    status: str
    response: str | None = None
    responded_by: str | None = None
    responded_at: str | None = None
    submitted_by: str
    created_at: str
    updated_at: str


class PaginatedTickets(BaseModel):
    items: list[TicketResponse]
    total: int
    page: int
    limit: int