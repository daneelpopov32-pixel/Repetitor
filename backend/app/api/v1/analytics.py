from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.analytics import DashboardResponse
from app.services import analytics as analytics_service
from app.utils.deps import get_current_user, require_role
from app.models import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await analytics_service.get_dashboard(db, student_id)


@router.get("/tutor/students")
async def tutor_students(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    return await analytics_service.get_tutor_students_summary(db, user.id)
