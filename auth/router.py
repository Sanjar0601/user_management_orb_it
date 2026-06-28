from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from users.schemas import UserCreate, UserLogin, UserResponse, TokenResponse, RefreshRequest, VerifyRequest
from users.services import AuthService
from users.dependencies import get_current_user
from users.models import User

router = APIRouter()


@router.post("/signup", response_model=UserResponse, summary="Register a new user",
             description="Creates a new user account and sends a verification code to the provided email.")
async def signup(data: UserCreate, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.register(data)


@router.post("/login", response_model=TokenResponse, summary="Login",
             description="Authenticates user and returns access and refresh tokens.")
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.login(data.email, data.password)


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token",
             description="Issues a new access token using a valid refresh token. Refresh token is rotated.")
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.refresh(data.refresh_token)


@router.post("/verify", summary="Verify email",
             description="Confirms user email using the verification code sent after registration.")
async def verify(data: VerifyRequest, db: AsyncSession = Depends(get_db)):
    from users.repository import UserRepository
    service = AuthService(db)
    user = await UserRepository(db).get_by_email(data.email)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    await service.verify(user.id, data.code)
    return {"message": "Email verified successfully"}