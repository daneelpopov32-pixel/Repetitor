from uuid import UUID
from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Answer, Task, Attempt, TestTask
from app.config import settings


async def ai_check(db: AsyncSession, task_id: UUID, student_answer: str) -> dict:
    task = (await db.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
    if not task:
        raise ValueError("Task not found")

    criteria_text = ""
    if task.fipi_criteria:
        import json
        criteria_text = json.dumps(task.fipi_criteria, ensure_ascii=False)

    prompt = (
        f"Задание: {task.text_content.get('text', '') if isinstance(task.text_content, dict) else task.text_content}\n"
        f"Критерии оценивания ФИПИ:\n{criteria_text}\n"
        f"Ответ ученика: {student_answer}\n\n"
        "Проанализируй ответ ученика по каждому критерию. Верни JSON с полями "
        "ai_feedback (текстовый разбор) и suggested_scores (словарь criterion_id -> балл)."
    )

    try:
        async with httpx.AsyncClient(timeout=settings.GIGACHAT_TIMEOUT) as client:
            response = await client.post(
                settings.GIGACHAT_API_URL,
                headers={"Authorization": f"Bearer {settings.GIGACHAT_API_KEY}"},
                json={
                    "model": "GigaChat",
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]

            import json
            parsed = json.loads(content)
            return {
                "ai_feedback": parsed.get("ai_feedback", content),
                "suggested_scores": parsed.get("suggested_scores", {}),
            }
    except Exception:
        return {
            "ai_feedback": "AI временно недоступен. Проверьте ответ вручную.",
            "suggested_scores": {},
        }


async def grade_answer(db: AsyncSession, answer_id: UUID, scores: dict, comment: str) -> dict:
    answer = (await db.execute(select(Answer).where(Answer.id == answer_id))).scalar_one_or_none()
    if not answer:
        raise ValueError("Answer not found")

    answer.manual_score = sum(scores.values())
    answer.ai_feedback = (answer.ai_feedback or "") + f"\n\nКомментарий репетитора: {comment}"
    answer.updated_at = datetime.utcnow()

    attempt = (await db.execute(select(Attempt).where(Attempt.id == answer.attempt_id))).scalar_one_or_none()
    if not attempt:
        raise ValueError("Attempt not found")

    all_essay_result = await db.execute(
        select(TestTask)
        .join(Task, Task.id == TestTask.task_id)
        .where(
            TestTask.test_id == attempt.test_id,
            Task.type == "ESSAY",
        )
    )
    essay_tasks = all_essay_result.scalars().all()

    all_graded = True
    for tt in essay_tasks:
        ans_result = await db.execute(
            select(Answer).where(Answer.attempt_id == attempt.id, Answer.task_id == tt.task_id)
        )
        ans = ans_result.scalar_one_or_none()
        if not ans or ans.manual_score is None:
            all_graded = False
            break

    if all_graded:
        attempt.status = "COMPLETED"
        attempt.finished_at = datetime.utcnow()

    await db.commit()

    return {
        "answer_id": answer.id,
        "manual_score": answer.manual_score,
        "status": "GRADED",
        "attempt_status": attempt.status,
    }


async def get_review_queue(db: AsyncSession, tutor_id: UUID) -> list[dict]:
    result = await db.execute(
        select(Answer)
        .join(Attempt, Attempt.id == Answer.attempt_id)
        .join(Task, Task.id == Answer.task_id)
        .where(
            Attempt.status == "PENDING_REVIEW",
            Task.type == "ESSAY",
            Answer.manual_score.is_(None),
        )
    )
    answers = result.scalars().all()
    return [
        {
            "answer_id": a.id,
            "attempt_id": a.attempt_id,
            "task_id": a.task_id,
            "student_input": a.student_input,
        }
        for a in answers
    ]
