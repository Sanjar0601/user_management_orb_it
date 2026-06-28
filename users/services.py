import random
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from users.repository import UserRepository
from users.models import User, RefreshToken, VerificationCode
from users.schemas import UserCreate, UserUpdate
from core.security import create_access_token, create_refresh_token, verify_token
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:

    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def register(self, data: UserCreate) -> User:
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        user = User(
            email=data.email,
            name=data.name,
            surname=data.surname,
            hashed_password=pwd_context.hash(data.password),
        )
        user = await self.repo.create(user)

        # Generate verification code
        # In production: send via email/SMS using SendGrid or Twilio
        code = str(random.randint(100000, 999999))
        verification = VerificationCode(
            user_id=user.id,
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
        )
        await self.repo.create_verification_code(verification)
        print(f"[DEV] Verification code for {user.email}: {code}")
        return user

    async def login(self, email: str, password: str) -> dict:
        user = await self.repo.get_by_email(email)
        if not user or not pwd_context.verify(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified"
            )
        return await self._issue_tokens(user)

    async def refresh(self, token: str) -> dict:
        user_id = verify_token(token, "refresh")
        existing = await self.repo.get_refresh_token(token)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        await self.repo.revoke_refresh_token(existing)
        user = await self.repo.get_by_id(user_id)
        return await self._issue_tokens(user)

    async def verify(self, user_id: int, code: str) -> None:
        record = await self.repo.get_verification_code(user_id, code)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code"
            )
        record.is_used = True
        user = await self.repo.get_by_id(user_id)
        user.is_verified = True
        await self.repo.update(user)

    async def _issue_tokens(self, user: User) -> dict:
        access = create_access_token(user.id)
        refresh = create_refresh_token(user.id)
        token_record = RefreshToken(
            user_id=user.id,
            token=refresh,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        await self.repo.create_refresh_token(token_record)
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


class UserService:

    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def get_me(self, user_id: int) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def get_all(self) -> list[User]:
        return await self.repo.get_all()

    async def get_by_id(self, user_id: int) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def update(self, user_id: int, data: UserUpdate) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(user, field, value)
        return await self.repo.update(user)

    async def delete(self, user_id: int) -> None:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        await self.repo.delete(user)