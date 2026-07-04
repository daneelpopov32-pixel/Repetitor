"""
API endpoints for FIPI integration:
- POST /fipi/sync-codifier - trigger codifier sync
- POST /fipi/sync-theme - trigger full sync for one theme
- POST /fipi/sync-subject - trigger full sync for all themes of a subject
- POST /fipi/create-test - create test from local DB
- POST /fipi/generate-ege - generate EGE History variant (21 tasks)
- GET /fipi/task-status/{task_id} - check Celery task status
- GET /fipi/sync-status - get sync status for all themes
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.deps import require_role
from app.models import User

router = APIRouter(prefix="/fipi", tags=["FIPI"])


class SyncCodifierRequest(BaseModel):
    subject_name: str = "История"


class SyncThemeRequest(BaseModel):
    theme_code: str


class CreateTestAsyncRequest(BaseModel):
    title: str
    theme_codes: list[str]
    count_per_theme: int = 5
    task_type: str = "TEST"  # TEST, ESSAY, MIX
    time_limit_minutes: int | None = None


@router.post("/sync-codifier")
async def sync_codifier(
    data: SyncCodifierRequest,
    user: User = Depends(require_role("TUTOR")),
):
    """Trigger one-time codifier sync from FIPI."""
    from app.tasks.fipi_tasks import sync_codifier
    task = sync_codifier.delay(data.subject_name)
    return {"task_id": task.id, "status": "started"}


@router.post("/sync-theme")
async def sync_theme(
    data: SyncThemeRequest,
    user: User = Depends(require_role("TUTOR")),
):
    """Trigger full sync for a single theme (fetches ALL tasks from FIPI)."""
    from app.tasks.fipi_tasks import sync_theme_full
    task = sync_theme_full.delay(data.theme_code)
    return {"task_id": task.id, "status": "started"}


@router.post("/sync-subject")
async def sync_subject(
    data: SyncCodifierRequest,
    user: User = Depends(require_role("TUTOR")),
):
    """Trigger full sync for all themes of a subject."""
    from app.tasks.fipi_tasks import sync_subject_full
    task = sync_subject_full.delay(data.subject_name)
    return {"task_id": task.id, "status": "started"}


@router.post("/create-test")
async def create_test_async(
    data: CreateTestAsyncRequest,
    user: User = Depends(require_role("TUTOR")),
):
    """Create test from local database (no live FIPI requests)."""
    from app.tasks.fipi_tasks import create_test_from_fipi
    task = create_test_from_fipi.delay(
        tutor_id=str(user.id),
        title=data.title,
        theme_codes=data.theme_codes,
        count_per_theme=data.count_per_theme,
        task_type=data.task_type,
        time_limit_minutes=data.time_limit_minutes,
    )
    return {"task_id": task.id, "status": "started"}


class GenerateEGERequest(BaseModel):
    title: str | None = None
    time_limit_minutes: int = 210


@router.post("/generate-ege")
async def generate_ege(
    data: GenerateEGERequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    """Generate a complete EGE History variant (21 tasks) from local DB."""
    from app.services.ege_generator import generate_ege_variant

    result = await generate_ege_variant(
        db=db,
        tutor_id=user.id,
        title=data.title,
        time_limit_minutes=data.time_limit_minutes,
    )
    return result


@router.get("/task-status/{task_id}")
async def task_status(
    task_id: str,
    user: User = Depends(require_role("TUTOR")),
):
    """Check Celery task status."""
    from app.celery_app import celery_app
    task = celery_app.AsyncResult(task_id)

    response = {
        "task_id": task_id,
        "status": task.status,
    }

    if task.status == "PROGRESS":
        response["progress"] = task.info
    elif task.status == "SUCCESS":
        response["result"] = task.result
    elif task.status == "FAILURE":
        response["error"] = str(task.info)

    return response


@router.get("/sync-status")
async def sync_status(
    user: User = Depends(require_role("TUTOR")),
):
    """Get sync status: task counts per theme for all subjects."""
    from sqlalchemy import select, func
    from app.database import get_db
    from app.models import Theme, Task, Subject
    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession

    # This endpoint needs a DB session - use dependency injection
    # But since we're in a sync-ish context, let's use a direct query
    from app.database import async_session

    async with async_session() as db:
        # Get all subjects
        subjects_result = await db.execute(select(Subject))
        subjects = subjects_result.scalars().all()

        result = []
        for subject in subjects:
            themes_result = await db.execute(
                select(
                    Theme.id,
                    Theme.fipi_code,
                    Theme.name,
                    func.count(Task.id).label("task_count"),
                )
                .outerjoin(Task, Task.theme_id == Theme.id)
                .where(Theme.subject_id == subject.id)
                .group_by(Theme.id, Theme.fipi_code, Theme.name)
                .order_by(Theme.fipi_code)
            )
            themes = themes_result.all()

            result.append({
                "subject_id": str(subject.id),
                "subject_name": subject.name,
                "themes": [
                    {
                        "theme_id": str(t.id),
                        "fipi_code": t.fipi_code,
                        "name": t.name,
                        "task_count": t.task_count,
                    }
                    for t in themes
                ],
            })

    return result
