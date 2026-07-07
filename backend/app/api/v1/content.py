from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Subject, Theme, Task, User
from app.schemas.content import (
    BulkImportRequest, BulkImportResponse,
    SubjectCreate,
)
from app.services import content_parser
from app.services.content import get_theme_tree, get_subjects
from app.utils.deps import require_role

router = APIRouter(prefix="/content", tags=["Content Management"])


@router.get("/subjects")
async def list_subjects(db: AsyncSession = Depends(get_db)):
    return await get_subjects(db)


@router.post("/subjects")
async def create_subject(
    data: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    subject = Subject(name=data.name)
    db.add(subject)
    await db.commit()
    return {"id": subject.id, "name": subject.name}


@router.get("/themes/tree")
async def theme_tree(subject_id: UUID, db: AsyncSession = Depends(get_db)):
    return await get_theme_tree(db, subject_id)


@router.post("/tasks/bulk-import", response_model=BulkImportResponse)
async def bulk_import_from_url(
    data: BulkImportRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    try:
        return await content_parser.import_from_url(
            db,
            url=data.url,
            subject_id=data.subject_id,
            theme_id=data.theme_id,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")


@router.get("/tasks")
async def list_tasks(
    subject_id: UUID | None = None,
    theme_id: UUID | None = None,
    task_type: str | None = None,
    offset: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    query = select(Task)
    if subject_id:
        query = query.where(Task.subject_id == subject_id)
    if theme_id:
        query = query.where(Task.theme_id == theme_id)
    if task_type:
        query = query.where(Task.type == task_type)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(query.offset(offset).limit(limit))
    tasks = result.scalars().all()
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "tasks": [
            {
                "id": str(t.id),
                "type": t.type,
                "theme_id": str(t.theme_id),
                "text_preview": t.text_content.get("text", "")[:100] if isinstance(t.text_content, dict) else str(t.text_content)[:100],
                "source_url": t.source_url,
                "exam_position": t.exam_position,
                "difficulty_level": t.difficulty_level,
            }
            for t in tasks
        ],
    }
