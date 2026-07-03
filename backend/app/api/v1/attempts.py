from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.attempt import (
    AnswerSaveRequest, AnswerSaveResponse, AttemptStartResponse,
    AttemptTasksResponse, SubmitResponse, AttemptDetailResponse,
)
from app.services import examination as exam_service
from app.utils.deps import get_current_user
from app.models import User

router = APIRouter(prefix="/attempts", tags=["Attempts"])


@router.post("/{attempt_id}/start", response_model=AttemptStartResponse)
async def start_attempt(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return await exam_service.start_attempt(db, test_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{attempt_id}", response_model=AttemptDetailResponse)
async def get_attempt(
    attempt_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return await exam_service.get_attempt_detail(db, attempt_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{attempt_id}/tasks", response_model=AttemptTasksResponse)
async def get_tasks(
    attempt_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return await exam_service.get_attempt_tasks(db, attempt_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{attempt_id}/answers/{task_id}", response_model=AnswerSaveResponse)
async def save_answer(
    attempt_id: UUID,
    task_id: UUID,
    data: AnswerSaveRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return await exam_service.save_answer(db, attempt_id, task_id, data.student_input)
    except ValueError as e:
        if "ATTEMPT_CLOSED" in str(e):
            raise HTTPException(status_code=400, detail="ATTEMPT_CLOSED")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{attempt_id}/submit", response_model=SubmitResponse)
async def submit(
    attempt_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return await exam_service.submit_attempt(db, attempt_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
