"""
API endpoints for FIPI integration:
- POST /content/sync-codifier - trigger codifier sync
- POST /tests/create-async - create test with live FIPI fetch
- GET /tasks/{task_id} - check Celery task status
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.deps import require_role
from app.models import User

router = APIRouter(prefix="/fipi", tags=["FIPI"])


class SyncCodifierRequest(BaseModel):
    subject_name: str = "История"


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


@router.post("/create-test")
async def create_test_async(
    data: CreateTestAsyncRequest,
    user: User = Depends(require_role("TUTOR")),
):
    """Create test with live FIPI fetch (async)."""
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
