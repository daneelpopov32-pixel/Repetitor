"""
EGE History variant generator.

Generates a complete 21-task exam variant from local database,
following the official FIPI structure.
"""
import random
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task, Theme, Test, TestTask
from app.services.ege_template import EGE_HISTORY_TEMPLATE
from app.services.kim_mapping import POSITION_LEVELS


async def generate_ege_variant(
    db: AsyncSession,
    tutor_id: UUID,
    title: str = None,
    time_limit_minutes: int = 210,
) -> dict:
    """Generate a complete EGE History variant from local DB.

    Returns dict with test info or error details.
    """
    if not title:
        title = f"Вариант ЕГЭ по истории {random.randint(1000, 9999)}"

    selected_tasks = []
    warnings = []
    used_task_ids = set()

    for position in EGE_HISTORY_TEMPLATE:
        pos_num = position["position"]
        allowed_types = position["allowed_types"]
        allowed_subtypes = position.get("allowed_subtypes", [])
        required_level = POSITION_LEVELS.get(pos_num)

        # Query tasks matching the position requirements
        query = select(Task).where(Task.type.in_(allowed_types))

        # For essay tasks, we need fipi_criteria
        if "ESSAY" in allowed_types:
            query = query.where(Task.fipi_criteria.isnot(None))

        # Try to match by exam_position first
        if required_level:
            pos_query = query.where(Task.exam_position == pos_num)
            result = await db.execute(pos_query.limit(50))
            candidates = result.scalars().all()

            # If not enough by position, fall back to subtype matching
            if len(candidates) < 3:
                result = await db.execute(query.limit(100))
                candidates = list(result.scalars().all())
        else:
            result = await db.execute(query.limit(100))
            candidates = list(result.scalars().all())

        # Filter by subtype if available in metadata
        if allowed_subtypes:
            filtered = []
            for t in candidates:
                subtype = (t.metadata_ or {}).get("subtype", "")
                if subtype in allowed_subtypes or not subtype:
                    filtered.append(t)
            if filtered:
                candidates = filtered

        # Prefer tasks with matching difficulty level
        if required_level:
            level_matched = [t for t in candidates if t.difficulty_level == required_level]
            if level_matched:
                candidates = level_matched

        # Exclude already used tasks
        candidates = [t for t in candidates if str(t.id) not in used_task_ids]

        if not candidates:
            warnings.append(
                f"Позиция {pos_num}: нет подходящих заданий "
                f"(тип: {allowed_types}, уровень: {required_level})"
            )
            continue

        # Pick one random task
        chosen = random.choice(candidates)
        selected_tasks.append({
            "task_id": str(chosen.id),
            "position": pos_num,
            "type": chosen.type,
            "theme_id": str(chosen.theme_id) if chosen.theme_id else None,
        })
        used_task_ids.add(str(chosen.id))

    if len(selected_tasks) < 21:
        warnings.append(
            f"Собрано только {len(selected_tasks)} из 21 задания. "
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

    # Add tasks in order
    for i, task_info in enumerate(selected_tasks):
        db.add(TestTask(
            test_id=test.id,
            task_id=UUID(task_info["task_id"]),
            order_number=i + 1,
        ))

    await db.commit()
    await db.refresh(test)

    # Build response
    result = {
        "test_id": str(test.id),
        "title": test.title,
        "tasks_count": len(selected_tasks),
        "time_limit_minutes": time_limit_minutes,
        "max_points": sum(
            p["max_points"]
            for p in EGE_HISTORY_TEMPLATE
            if p["position"] in [t["position"] for t in selected_tasks]
        ),
    }
    if warnings:
        result["warnings"] = warnings

    return result
