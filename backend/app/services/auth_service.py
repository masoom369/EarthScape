from app.db.mongo import get_db
from app.middleware.auth import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.repositories.token_repo import TokenRepository
from app.repositories.user_repo import UserRepository


class AuthService:
    def __init__(self):
        db = get_db()
        self.user_repo = UserRepository(db)
        self.token_repo = TokenRepository(db)

    async def login(self, email: str, password: str) -> tuple[dict, str, str, object]:
        user = await self.user_repo.find_by_email(email)
        if not user or not verify_password(password, user["password_hash"]):
            raise ValueError("Invalid email or password")
        if not user.get("is_active"):
            raise ValueError("Account deactivated")
        token, jti, expire = create_access_token(
            str(user["_id"]), user["role"], user["email"]
        )
        profile = {
            "id": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
            "is_active": user["is_active"],
        }
        return profile, token, jti, expire

    async def logout(self, jti: str, expires_at) -> None:
        await self.token_repo.revoke(jti, expires_at)

    async def ensure_default_admin(self, email: str, password: str) -> None:
        count = await self.user_repo.count_all()
        if count == 0:
            await self.user_repo.create(email, hash_password(password), "admin")
