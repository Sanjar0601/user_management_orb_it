from fastapi import FastAPI
from auth.router import router as auth_router
from users.router import router as users_router

app = FastAPI(
    title="Users API",
    description="User management API with authentication and verification",
    version="1.0.0"
)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(users_router, prefix="/users", tags=["Users"])