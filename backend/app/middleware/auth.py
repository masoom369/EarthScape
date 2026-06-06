from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import uuid4

import bcrypt
from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError, jwt

from app.config import get_settings
from app.db.mongo import get_db
from app.repositories.token_repo import TokenRepository
from app.repositories.user_repo import UserRepository

ALGORITHM = "HS256"
COOKIE_NAME = "access_token"


def hash_password(password: str) -> str:
    """Hash plaintext password with bcrypt. Returns utf-8 string for MongoDB storage."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time bcrypt comparison against stored hash string."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str, role: str, email: str) -> tuple[str, str, datetime]:
    """Sign JWT. Returns (encoded_token, jti, expiry_datetime)."""
    settings = get_settings()
    jti = str(uuid4())
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "role": role,
        "email": email,
        "jti": jti,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)
    return token, jti, expire


async def get_current_user(
    access_token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> dict:
    """Decode JWT cookie, verify revocation, return active user dict."""
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    settings = get_settings()
    try:
        payload = jwt.decode(access_token, settings.jwt_secret, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub", "")
        jti: str = payload.get("jti", "")
        if not user_id or not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc

    token_repo = TokenRepository(get_db())
    if await token_repo.is_revoked(jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    user_repo = UserRepository(get_db())
    user = await user_repo.find_by_id(user_id)
    if not user or not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "role": user["role"],
        "is_active": user["is_active"],
    }


def require_roles(*roles: str):
    """Dependency factory: reject request if authenticated user's role not in roles."""
    async def checker(user: Annotated[dict, Depends(get_current_user)]) -> dict:
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user
    return checker