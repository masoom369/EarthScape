from typing import Literal

from pydantic import BaseModel, EmailStr, Field

Role = Literal["admin", "analyst", "viewer"]


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: Role


class UserUpdate(BaseModel):
    role: Role | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str


class PaginatedUsers(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    limit: int
