from uuid import UUID
import logging
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Theme, Task, Subject
from app.schemas.theme import ThemeTreeResponse
from app.services import content as content_service

logger = logging.getLogger(__name__)

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


# In-memory cache for FIPI task counts (key: subject_name, value: {data, timestamp})
_fipi_counts_cache: dict[str, tuple[list, float]] = {}
_FIPI_CACHE_TTL = 3600  # 1 hour


@router.get("/fipi-counts")
async def fipi_task_counts(
    subject_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get task counts from FIPI (open bank) for each theme of a subject.
    Results are cached in memory for 1 hour.
    """
    import time
    import httpx

    # Get subject name
    subj_result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = subj_result.scalar_one_or_none()
    if not subject:
        return []

    subject_name = subject.name
    now = time.time()

    # Check cache
    if subject_name in _fipi_counts_cache:
        cached_data, cached_at = _fipi_counts_cache[subject_name]
        if now - cached_at < _FIPI_CACHE_TTL:
            return cached_data

    # Import codifier mapping
    from app.tasks.fipi_tasks import get_codifier, _extract_tasks_from_html, HEADERS, get_base_url, get_project_id

    codifier = get_codifier(subject_name)
    if not codifier:
        return []

    base_url = get_base_url()
    project_id = get_project_id()

    # Get themes from DB for this subject
    themes_result = await db.execute(
        select(Theme).where(Theme.subject_id == subject_id)
    )
    db_themes = {t.fipi_code: t for t in themes_result.scalars().all()}

    results = []

    for fipi_code, theme_name in codifier.items():
        # Try to find theme in DB (handle trailing dot variants)
        db_theme = db_themes.get(fipi_code) or db_themes.get(fipi_code.rstrip("."))

        try:
            async with httpx.AsyncClient(timeout=15, verify=False) as client:
                resp = await client.post(
                    f"{base_url}/questions.php",
                    data={
                        "search": "1",
                        "pagesize": "10",
                        "proj": project_id,
                        "theme": fipi_code,
                        "page": "1",
                    },
                    headers=HEADERS,
                )
                html = resp.content.decode("windows-1251", errors="replace")
                all_tasks = _extract_tasks_from_html(html)

                test_count = sum(1 for t in all_tasks if t.get("type") == "TEST")
                essay_count = sum(1 for t in all_tasks if t.get("type") == "ESSAY")

                results.append({
                    "theme_id": str(db_theme.id) if db_theme else None,
                    "fipi_code": fipi_code,
                    "name": theme_name,
                    "test_count": test_count,
                    "essay_count": essay_count,
                })
        except httpx.TimeoutException:
            logger.warning("FIPI timeout for theme %s (%s)", fipi_code, theme_name)
            results.append({
                "theme_id": str(db_theme.id) if db_theme else None,
                "fipi_code": fipi_code,
                "name": theme_name,
                "test_count": 0,
                "essay_count": 0,
                "error": "timeout",
            })
        except Exception as exc:
            logger.warning("FIPI request failed for %s: %s", fipi_code, exc)
            results.append({
                "theme_id": str(db_theme.id) if db_theme else None,
                "fipi_code": fipi_code,
                "name": theme_name,
                "test_count": 0,
                "essay_count": 0,
                "error": str(exc),
            })

    # Cache results
    _fipi_counts_cache[subject_name] = (results, now)

    return results
