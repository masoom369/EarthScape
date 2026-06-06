from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserProfile(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool