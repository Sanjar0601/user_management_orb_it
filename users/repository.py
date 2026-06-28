from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from users.models import User, RefreshToken, VerificationCode
from datetime import datetime


class UserRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_all(self) -> list[User]:
        result = await self.db.execute(select(User))
        return list(result.scalars().all())

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: User) -> User:
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.commit()

    async def create_verification_code(self, code: VerificationCode) -> VerificationCode:
        self.db.add(code)
        await self.db.commit()
        await self.db.refresh(code)
        return code

    async def get_verification_code(self, user_id: int, code: str) -> VerificationCode | None:
        result = await self.db.execute(
            select(VerificationCode).where(
                VerificationCode.user_id == user_id,
                VerificationCode.code == code,
                VerificationCode.is_used == False,
                VerificationCode.expires_at > datetime.utcnow()
            )
        )
        return result.scalar_one_or_none()

    async def create_refresh_token(self, token: RefreshToken) -> RefreshToken:
        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)
        return token

    async def get_refresh_token(self, token: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token == token,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.utcnow()
            )
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token: RefreshToken) -> None:
        token.is_revoked = True
        await self.db.commit()