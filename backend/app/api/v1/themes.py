from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Theme, Task
from app.schemas.theme import ThemeTreeResponse
from app.services import content as content_service

router = APIRouter(prefix="/themes", tags=["Themes"])


@router.get("/tree", response_model=ThemeTreeResponse)
async def theme_tree(subject_id: UUID, db: AsyncSession = Depends(get_db)):
    return await content_service.get_theme_tree(db, subject_id)


@router.get("/subjects")
async def subjects(db: AsyncSession = Depends(get_db)):
    return await content_service.get_subjects(db)


@router.get("/task-counts")
async def theme_task_counts(subject_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Theme.id,
            Theme.name,
            Theme.fipi_code,
            func.count(Task.id).filter(Task.type == "TEST").label("test_count"),
            func.count(Task.id).filter(Task.type == "ESSAY").label("essay_count"),
        )
        .outerjoin(Task, Task.theme_id == Theme.id)
        .where(Theme.subject_id == subject_id)
        .group_by(Theme.id, Theme.name, Theme.fipi_code)
    )
    rows = result.all()
    return [
        {
            "theme_id": str(r.id),
            "name": r.name,
            "fipi_code": r.fipi_code,
            "test_count": r.test_count,
            "essay_count": r.essay_count,
        }
        for r in rows
    ]
