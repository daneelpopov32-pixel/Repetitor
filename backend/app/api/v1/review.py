from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.review import AiCheckRequest, AiCheckResponse, GradeRequest, GradeResponse
from app.services import review as review_service
from app.utils.deps import require_role
from app.models import User

router = APIRouter(prefix="/review", tags=["Review"])


@router.post("/ai-check", response_model=AiCheckResponse)
async def ai_check(
    data: AiCheckRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    return await review_service.ai_check(db, data.task_id, data.student_answer)


@router.post("/grade", response_model=GradeResponse)
async def grade(
    data: GradeRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    return await review_service.grade_answer(db, data.answer_id, data.scores, data.comment)


@router.get("/queue")
async def review_queue(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    return await review_service.get_review_queue(db, user.id)
