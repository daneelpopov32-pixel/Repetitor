from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Subject, Theme, Task, User
from app.schemas.content import (
    TaskImportRequest, TaskImportResponse,
    BulkImportRequest, BulkImportResponse,
    SubjectCreate, ThemeCreate,
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


@router.post("/themes")
async def create_theme(
    data: ThemeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    theme = Theme(
        subject_id=data.subject_id,
        parent_theme_id=data.parent_theme_id,
        fipi_code=data.fipi_code,
        name=data.name,
    )
    db.add(theme)
    await db.commit()
    return {"id": theme.id, "name": theme.name, "fipi_code": theme.fipi_code}


@router.post("/tasks/import", response_model=TaskImportResponse)
async def import_single_task(
    data: TaskImportRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    try:
        return await content_parser.import_task(
            db,
            subject_id=data.subject_id,
            theme_id=data.theme_id,
            task_type=data.type,
            text_content=data.text_content,
            correct_answer_key=data.correct_answer_key,
            fipi_criteria=data.fipi_criteria,
            source_url=data.source_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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

    result = await db.execute(query.limit(100))
    tasks = result.scalars().all()
    return [
        {
            "id": t.id,
            "type": t.type,
            "theme_id": t.theme_id,
            "text_preview": t.text_content.get("text", "")[:100] if isinstance(t.text_content, dict) else str(t.text_content)[:100],
            "source_url": t.source_url,
        }
        for t in tasks
    ]
