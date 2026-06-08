from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from jose import jwt

from app.config import get_settings
from app.middleware.auth import ALGORITHM, COOKIE_NAME, get_current_user
from app.models.auth import LoginRequest, UserProfile
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserProfile)
async def login(body: LoginRequest, response: Response):
    try:
        profile, token, _, _ = await AuthService().login(body.email, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    settings = get_settings()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        # MAJOR #8: secure flag set for production; disabled only when debug=True equivalent
        # settings has no debug flag — derive from CORS: if localhost in origins → dev mode
        secure=not any("localhost" in o for o in settings.cors_origin_list),
        samesite="strict",
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )
    return profile


@router.post("/logout")
async def logout(
    response: Response,
    user: dict = Depends(get_current_user),
    access_token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
):
    settings = get_settings()
    if access_token:
        try:
            payload = jwt.decode(access_token, settings.jwt_secret, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                await AuthService().logout(jti, datetime.fromtimestamp(exp, tz=UTC))
        except Exception:
            pass
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserProfile)
async def me(user: dict = Depends(get_current_user)):
    return user