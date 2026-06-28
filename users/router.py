from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from users.schemas import UserResponse, UserUpdate
from users.services import UserService
from users.dependencies import get_current_verified_user, get_current_admin
from users.models import User, UserRole

router = APIRouter()


@router.get("/me", response_model=UserResponse, summary="Get current user",
            description="Returns the profile of the currently authenticated user.")
async def get_me(current_user: User = Depends(get_current_verified_user)):
    return current_user


@router.get("/", response_model=list[UserResponse], summary="Get all users",
            description="Returns a list of all users. Admin only.")
async def get_users(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    service = UserService(db)
    return await service.get_all()


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID",
            description="Returns a single user by ID. Admin only.")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    service = UserService(db)
    return await service.get_by_id(user_id)


@router.patch("/{user_id}", response_model=UserResponse, summary="Update user",
              description="Partially updates user data.")
async def update_user(user_id: int, data: UserUpdate, db: AsyncSession = Depends(get_db),
                      _: User = Depends(get_current_verified_user)):
    service = UserService(db)
    return await service.update(user_id, data)


@router.delete("/{user_id}", status_code=204, summary="Delete user",
               description="Deletes a user by ID. Admin only.")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    service = UserService(db)
    await service.delete(user_id)


@router.patch("/me/make-admin", response_model=UserResponse, summary="Make current user admin",
              description="DEV ONLY: Grants admin role to the current user. Remove in production.")
async def make_admin(current_user: User = Depends(get_current_verified_user),
                     db: AsyncSession = Depends(get_db)):
    current_user.role = UserRole.admin
    await db.commit()
    await db.refresh(current_user)
    return current_user