from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import uuid4

from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.db.mongo import get_db
from app.repositories.token_repo import TokenRepository
from app.repositories.user_repo import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
COOKIE_NAME = "access_token"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, role: str, email: str) -> tuple[str, str, datetime]:
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
):
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    settings = get_settings()
    try:
        payload = jwt.decode(access_token, settings.jwt_secret, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub", "")
        jti: str = payload.get("jti", "")
        if not user_id or not jti:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

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
    async def checker(user: Annotated[dict, Depends(get_current_user)]):
        if user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return checker
