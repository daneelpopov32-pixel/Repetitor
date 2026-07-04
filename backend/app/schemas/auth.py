from __future__ import annotations
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    birth_date: date | None = None
    role: str  # TUTOR, STUDENT
    invitation_code: str | None = None
    consent_152fz: bool


class TokenResponse(BaseModel):
    user_id: UUID
    email: str
    role: str
    access_token: str
    refresh_token: str


class LoginRequest(BaseModel):
    email: str
    password: str


class InvitationCodeCreate(BaseModel):
    expires_in_days: int = 7


class InvitationCodeResponse(BaseModel):
    code: str
    expires_at: datetime
