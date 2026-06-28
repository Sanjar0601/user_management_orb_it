from pydantic import BaseModel, EmailStr
from enum import Enum


class UserRole(str, Enum):
    user = "user"
    admin = "admin"


# Request schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    surname: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    surname: str | None = None
    email: EmailStr | None = None


class VerifyRequest(BaseModel):
    email: EmailStr
    code: str

class RefreshRequest(BaseModel):
    refresh_token: str


# Response schemas
class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    surname: str | None
    role: UserRole
    is_verified: bool

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"