from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.middleware.auth import require_roles
from app.models.user import PaginatedUsers, UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=PaginatedUsers)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    _user: dict = Depends(require_roles("admin")),
):
    return await UserService().list_users(page, limit)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    _user: dict = Depends(require_roles("admin")),
):
    try:
        return await UserService().create_user(body.email, body.password, body.role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    body: UserUpdate,
    _user: dict = Depends(require_roles("admin")),
):
    result = await UserService().update_user(user_id, body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return result


@router.delete("/{user_id}", response_model=UserResponse)
async def deactivate_user(
    user_id: str,
    _user: dict = Depends(require_roles("admin")),
):
    result = await UserService().deactivate_user(user_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return result