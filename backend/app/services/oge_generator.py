"""
OGE variant generator.

Generates a complete exam variant from local database,
following the official FIPI structure for OGE History and Social Studies.
"""
import random
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task, Theme, Test, TestTask
from app.services.oge_template import (
    OGE_HISTORY_TEMPLATE, OGE_HISTORY_MAX_PRIMARY_POINTS,
    OGE_HISTORY_EXAM_TIME_MINUTES, OGE_HISTORY_TOTAL_TASKS,
    OGE_SOCIAL_TEMPLATE, OGE_SOCIAL_MAX_PRIMARY_POINTS,
    OGE_SOCIAL_EXAM_TIME_MINUTES, OGE_SOCIAL_TOTAL_TASKS,
)

_TEMPLATES = {
    "История": (OGE_HISTORY_TEMPLATE, OGE_HISTORY_MAX_PRIMARY_POINTS, OGE_HISTORY_EXAM_TIME_MINUTES, OGE_HISTORY_TOTAL_TASKS),
    "Обществознание": (OGE_SOCIAL_TEMPLATE, OGE_SOCIAL_MAX_PRIMARY_POINTS, OGE_SOCIAL_EXAM_TIME_MINUTES, OGE_SOCIAL_TOTAL_TASKS),
}


async def generate_oge_variant(
    db: AsyncSession,
    tutor_id: UUID,
    subject_name: str,
    title: str = None,
    time_limit_minutes: int = None,
) -> dict:
    """Generate a complete OGE variant from local DB.

    Args:
        db: Async database session.
        tutor_id: UUID of the tutor creating the test.
        subject_name: Subject name ("История" or "Обществознание").
        title: Optional custom title.
        time_limit_minutes: Optional override; defaults to the official time.

    Returns dict with test info or error details.
    """
    if subject_name not in _TEMPLATES:
        return {"error": f"OGE-шаблон не найден для предмета: {subject_name}"}

    template, max_points, default_time, total_tasks = _TEMPLATES[subject_name]

    if time_limit_minutes is None:
        time_limit_minutes = default_time

    if not title:
        title = f"Вариант ОГЭ по {subject_name.lower()} {random.randint(1000, 9999)}"

    selected_tasks = []
    warnings = []
    used_task_ids = set()

    for position in template:
        pos_num = position["position"]
        allowed_types = position["allowed_types"]

        from sqlalchemy import select
        query = select(Task).where(Task.type.in_(allowed_types))

        # For essay tasks, require fipi_criteria
        if "ESSAY" in allowed_types:
            query = query.where(Task.fipi_criteria.isnot(None))

        # Try to match by exam_position first
        pos_query = query.where(Task.exam_position == pos_num)
        result = await db.execute(pos_query.limit(50))
        candidates = result.scalars().all()

        if len(candidates) < 3:
            result = await db.execute(query.limit(100))
            candidates = list(result.scalars().all())

        # Filter by subtype if available
        allowed_subtypes = position.get("allowed_subtypes", [])
        if allowed_subtypes:
            filtered = []
            for t in candidates:
                subtype = (t.metadata_ or {}).get("subtype", "")
                if subtype in allowed_subtypes or not subtype:
                    filtered.append(t)
            if filtered:
                candidates = filtered

        # Exclude already used tasks
        candidates = [t for t in candidates if str(t.id) not in used_task_ids]

        if not candidates:
            warnings.append(
                f"Позиция {pos_num}: нет подходящих заданий "
                f"(тип: {allowed_types})"
            )
            continue

        chosen = random.choice(candidates)
        selected_tasks.append({
            "task_id": str(chosen.id),
            "position": pos_num,
            "type": chosen.type,
            "theme_id": str(chosen.theme_id) if chosen.theme_id else None,
        })
        used_task_ids.add(str(chosen.id))

    if len(selected_tasks) < total_tasks:
        warnings.append(
            f"Собрано только {len(selected_tasks)} из {total_tasks} заданий. "
            f"Нужна синхронизация недостающих тем."
        )

    if not selected_tasks:
        return {
            "error": "Не удалось собрать ни одного задания. Запустите полную синхронизацию.",
            "warnings": warnings,
        }

    # Create the test
    test = Test(
        tutor_id=tutor_id,
        title=title,
        time_limit_minutes=time_limit_minutes,
    )
    db.add(test)
    await db.flush()

    for i, task_info in enumerate(selected_tasks):
        db.add(TestTask(
            test_id=test.id,
            task_id=UUID(task_info["task_id"]),
            order_number=i + 1,
        ))

    await db.commit()
    await db.refresh(test)

    result = {
        "test_id": str(test.id),
        "title": test.title,
        "tasks_count": len(selected_tasks),
        "time_limit_minutes": time_limit_minutes,
        "max_points": sum(
            p["max_points"]
            for p in template
            if p["position"] in [t["position"] for t in selected_tasks]
        ),
    }
    if warnings:
        result["warnings"] = warnings

    return result
