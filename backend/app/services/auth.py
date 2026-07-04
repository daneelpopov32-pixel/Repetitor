from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Profile, TutorStudent, InvitationCode, Tenant
from app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token


async def register_user(db: AsyncSession, data: dict) -> dict:
    result = await db.execute(select(User).where(User.email == data["email"]))
    if result.scalar_one_or_none():
        raise ValueError("Email already exists")

    if data.get("role") == "STUDENT" and data.get("invitation_code"):
        code_result = await db.execute(
            select(InvitationCode).where(
                InvitationCode.code == data["invitation_code"],
                InvitationCode.expires_at > datetime.utcnow(),
                InvitationCode.used_at.is_(None),
            )
        )
        inv_code = code_result.scalar_one_or_none()
        if not inv_code:
            raise ValueError("Invalid or expired invitation code")
    else:
        inv_code = None

    tenant = (await db.execute(select(Tenant).limit(1))).scalar_one_or_none()
    if not tenant:
        tenant = Tenant(name="Default")
        db.add(tenant)
        await db.flush()

    user = User(
        tenant_id=tenant.id,
        email=data["email"],
        password_hash=hash_password(data["password"]),
        role=data["role"],
    )
    db.add(user)
    await db.flush()

    profile = Profile(
        user_id=user.id,
        first_name=data["first_name"],
        last_name=data["last_name"],
        birth_date=data.get("birth_date"),
        consent_152fz_at=datetime.utcnow(),
    )
    db.add(profile)

    if inv_code:
        inv_code.used_at = datetime.utcnow()
        inv_code.used_by_student_id = user.id
        link = TutorStudent(tutor_id=inv_code.tutor_id, student_id=user.id)
        db.add(link)

    await db.commit()

    return {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "access_token": create_access_token(user.id, user.role),
        "refresh_token": create_refresh_token(user.id),
    }


async def login_user(db: AsyncSession, email: str, password: str) -> dict:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid credentials")
    return {
        "user_id": user.id,
        "role": user.role,
        "access_token": create_access_token(user.id, user.role),
        "refresh_token": create_refresh_token(user.id),
    }


async def generate_invitation_code(db: AsyncSession, tutor_id: UUID, expires_in_days: int) -> dict:
    import secrets
    code = secrets.token_urlsafe(8)
    inv = InvitationCode(
        code=code,
        tutor_id=tutor_id,
        expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
    )
    db.add(inv)
    await db.commit()
    return {"code": code, "expires_at": inv.expires_at}
