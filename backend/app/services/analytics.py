from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Attempt, Answer, Task, Theme, TutorStudent


async def get_dashboard(db: AsyncSession, student_id: UUID) -> dict:
    result = await db.execute(
        select(Attempt)
        .where(Attempt.student_id == student_id, Attempt.status == "COMPLETED")
    )
    attempts = result.scalars().all()

    if not attempts:
        return {
            "student_id": student_id,
            "total_tests": 0,
            "average_score": 0.0,
            "dynamics": [],
            "weak_themes": [],
            "strong_themes": [],
        }

    total_tests = len(attempts)
    scores = [a.auto_score or 0 for a in attempts]
    average_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    dynamics = []
    for a in sorted(attempts, key=lambda x: x.started_at or x.finished_at or datetime.min):
        dt = (a.finished_at or a.started_at)
        dynamics.append({
            "date": dt.strftime("%Y-%m-%d"),
            "score": a.auto_score or 0,
        })

    seen_dates: dict[str, int] = {}
    for d in dynamics:
        if d["date"] in seen_dates:
            seen_dates[d["date"]] = max(seen_dates[d["date"]], d["score"])
        else:
            seen_dates[d["date"]] = d["score"]
    dynamics = [{"date": k, "score": v} for k, v in sorted(seen_dates.items())]

    theme_stats: dict[UUID, dict] = {}
    for a in attempts:
        answers_result = await db.execute(
            select(Answer).where(Answer.attempt_id == a.id)
        )
        answers = answers_result.scalars().all()
        for ans in answers:
            task = (await db.execute(select(Task).where(Task.id == ans.task_id))).scalar_one_or_none()
            if not task:
                continue
            theme_id = task.theme_id
            if theme_id not in theme_stats:
                theme_stats[theme_id] = {"correct": 0, "total": 0}
            if task.type == "TEST":
                theme_stats[theme_id]["total"] += 1
                if ans.auto_score and ans.auto_score > 0:
                    theme_stats[theme_id]["correct"] += 1

    theme_ids = list(theme_stats.keys())
    if theme_ids:
        themes_result = await db.execute(select(Theme).where(Theme.id.in_(theme_ids)))
        themes_map = {t.id: t.name for t in themes_result.scalars().all()}
    else:
        themes_map = {}

    theme_rates = []
    for tid, stats in theme_stats.items():
        if stats["total"] > 0:
            rate = round(stats["correct"] / stats["total"] * 100, 1)
            theme_rates.append({
                "theme_id": tid,
                "name": themes_map.get(tid, "Unknown"),
                "success_rate": rate,
            })

    weak_themes = sorted([t for t in theme_rates if t["success_rate"] < 50], key=lambda x: x["success_rate"])
    strong_themes = sorted([t for t in theme_rates if t["success_rate"] >= 50], key=lambda x: x["success_rate"], reverse=True)

    return {
        "student_id": student_id,
        "total_tests": total_tests,
        "average_score": average_score,
        "dynamics": dynamics,
        "weak_themes": weak_themes,
        "strong_themes": strong_themes,
    }


async def get_tutor_students_summary(db: AsyncSession, tutor_id: UUID) -> list[dict]:
    result = await db.execute(
        select(TutorStudent).where(TutorStudent.tutor_id == tutor_id)
    )
    links = result.scalars().all()
    student_ids = [link.student_id for link in links]

    if not student_ids:
        return []

    summaries = []
    for sid in student_ids:
        dash = await get_dashboard(db, sid)
        summaries.append(dash)

    return summaries
