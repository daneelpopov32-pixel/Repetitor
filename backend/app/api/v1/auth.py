from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if not data.consent_152fz:
        raise HTTPException(status_code=400, detail="Consent to personal data processing is required")
    try:
        result = await auth_service.register_user(db, data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await auth_service.login_user(db, data.email, data.password)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {**result, "email": data.email}
