from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Test, TestTask, TestAssignment, Task, Attempt, Answer, Theme


async def create_test(db: AsyncSession, tutor_id: UUID, data: dict) -> dict:
    test = Test(
        tutor_id=tutor_id,
        title=data["title"],
        time_limit_minutes=data.get("time_limit_minutes"),
    )
    db.add(test)
    await db.flush()

    for item in data["tasks"]:
        tt = TestTask(test_id=test.id, task_id=item["task_id"], order_number=item["order_number"])
        db.add(tt)

    await db.commit()
    return {
        "test_id": test.id,
        "title": test.title,
        "time_limit_minutes": test.time_limit_minutes,
        "created_at": test.created_at,
    }


async def assign_test(db: AsyncSession, test_id: UUID, student_ids: list[UUID]) -> list[dict]:
    assignments = []
    for sid in student_ids:
        a = TestAssignment(test_id=test_id, student_id=sid)
        db.add(a)
        await db.flush()
        assignments.append({"assignment_id": a.id, "student_id": sid, "status": a.status})
    await db.commit()
    return assignments


async def get_student_assignments(db: AsyncSession, student_id: UUID) -> list[dict]:
    result = await db.execute(
        select(TestAssignment)
        .where(TestAssignment.student_id == student_id)
        .options(selectinload(TestAssignment.test))
    )
    rows = result.scalars().all()
    return [
        {
            "assignment_id": a.id,
            "test_id": a.test_id,
            "title": a.test.title,
            "status": a.status,
            "assigned_at": a.assigned_at,
        }
        for a in rows
    ]


async def start_attempt(db: AsyncSession, test_id: UUID, student_id: UUID) -> dict:
    result = await db.execute(select(Test).where(Test.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise ValueError("Test not found")

    now = datetime.utcnow()
    attempt = Attempt(
        test_id=test_id,
        student_id=student_id,
        started_at=now,
        status="IN_PROGRESS",
    )
    db.add(attempt)
    await db.flush()

    assignment_result = await db.execute(
        select(TestAssignment).where(
            TestAssignment.test_id == test_id,
            TestAssignment.student_id == student_id,
        )
    )
    assignment = assignment_result.scalar_one_or_none()
    if assignment:
        assignment.status = "IN_PROGRESS"

    await db.commit()
    return {
        "attempt_id": attempt.id,
        "status": attempt.status,
        "started_at": attempt.started_at,
        "time_limit_minutes": test.time_limit_minutes,
        "server_time": datetime.utcnow(),
    }


async def get_attempt_tasks(db: AsyncSession, attempt_id: UUID) -> dict:
    attempt = (await db.execute(select(Attempt).where(Attempt.id == attempt_id))).scalar_one_or_none()
    if not attempt:
        raise ValueError("Attempt not found")

    result = await db.execute(
        select(TestTask)
        .where(TestTask.test_id == attempt.test_id)
        .options(selectinload(TestTask.task))
        .order_by(TestTask.order_number)
    )
    items = result.scalars().all()

    # Get theme names for all tasks
    theme_ids = list({tt.task.theme_id for tt in items if tt.task.theme_id})
    theme_map = {}
    if theme_ids:
        themes_result = await db.execute(
            select(Theme).where(Theme.id.in_(theme_ids))
        )
        theme_map = {t.id: t.name for t in themes_result.scalars().all()}

    # Get existing answers for this attempt
    answers_result = await db.execute(
        select(Answer).where(Answer.attempt_id == attempt_id)
    )
    answers_map = {str(a.task_id): a for a in answers_result.scalars().all()}

    return {
        "attempt_id": attempt.id,
        "tasks": [
            {
                "task_id": tt.task.id,
                "order_number": tt.order_number,
                "type": tt.task.type,
                "answer_type": (tt.task.correct_answer_key or {}).get("type", "short_answer"),
                "text_content": tt.task.text_content,
                "exam_position": tt.task.exam_position,
                "difficulty_level": tt.task.difficulty_level,
                "block_id": (tt.task.metadata_ or {}).get("fipi_guid", ""),
                "theme_name": theme_map.get(tt.task.theme_id, ""),
                "student_input": answers_map.get(str(tt.task.id), Answer()).student_input if str(tt.task.id) in answers_map else None,
            }
            for tt in items
        ],
    }


async def get_attempt_detail(db: AsyncSession, attempt_id: UUID) -> dict:
    attempt = (await db.execute(select(Attempt).where(Attempt.id == attempt_id))).scalar_one_or_none()
    if not attempt:
        raise ValueError("Attempt not found")

    result = await db.execute(select(Test).where(Test.id == attempt.test_id))
    test = result.scalar_one_or_none()
    return {
        "attempt_id": attempt.id,
        "status": attempt.status,
        "started_at": attempt.started_at,
        "time_limit_minutes": test.time_limit_minutes if test else None,
        "server_time": datetime.utcnow(),
    }


async def save_answer(db: AsyncSession, attempt_id: UUID, task_id: UUID, student_input: str) -> dict:
    attempt = (await db.execute(select(Attempt).where(Attempt.id == attempt_id))).scalar_one_or_none()
    if not attempt:
        raise ValueError("Attempt not found")
    if attempt.status not in ("IN_PROGRESS",):
        raise ValueError("ATTEMPT_CLOSED")

    now = datetime.utcnow()
    if attempt.started_at and attempt.status == "IN_PROGRESS":
        test = (await db.execute(select(Test).where(Test.id == attempt.test_id))).scalar_one_or_none()
        if test and test.time_limit_minutes:
            elapsed = (now - attempt.started_at).total_seconds() / 60
            if elapsed > test.time_limit_minutes:
                attempt.status = "COMPLETED"
                attempt.finished_at = now
                await db.commit()
                raise ValueError("ATTEMPT_CLOSED")

    result = await db.execute(
        select(Answer).where(Answer.attempt_id == attempt_id, Answer.task_id == task_id)
    )
    answer = result.scalar_one_or_none()
    if answer:
        answer.student_input = student_input
        answer.updated_at = now
    else:
        answer = Answer(attempt_id=attempt_id, task_id=task_id, student_input=student_input, updated_at=now)
        db.add(answer)

    await db.commit()
    return {"status": "saved", "updated_at": now}


async def submit_attempt(db: AsyncSession, attempt_id: UUID) -> dict:
    attempt = (await db.execute(select(Attempt).where(Attempt.id == attempt_id))).scalar_one_or_none()
    if not attempt:
        raise ValueError("Attempt not found")

    task_ids_result = await db.execute(
        select(TestTask.task_id).where(TestTask.test_id == attempt.test_id)
    )
    task_ids = [row[0] for row in task_ids_result.all()]

    answers_result = await db.execute(
        select(Answer).where(Answer.attempt_id == attempt_id)
    )
    answers_list = {a.task_id: a for a in answers_result.scalars().all()}

    tasks_result = await db.execute(select(Task).where(Task.id.in_(task_ids)))
    tasks_map = {t.id: t for t in tasks_result.scalars().all()}

    auto_score = 0
    max_auto_score = 0
    has_essay = False

    for tid in task_ids:
        task = tasks_map.get(tid)
        if not task:
            continue
        answer = answers_list.get(tid)

        if task.type == "TEST":
            max_auto_score += 1
            if answer and task.correct_answer_key:
                score = _grade_test_answer(task.correct_answer_key, answer.student_input)
                answer.auto_score = score
                auto_score += score
        elif task.type == "ESSAY":
            has_essay = True

    if has_essay:
        attempt.status = "PENDING_REVIEW"
    else:
        attempt.status = "COMPLETED"

    attempt.auto_score = auto_score
    attempt.finished_at = datetime.utcnow()

    assignment_result = await db.execute(
        select(TestAssignment).where(
            TestAssignment.test_id == attempt.test_id,
            TestAssignment.student_id == attempt.student_id,
        )
    )
    assignment = assignment_result.scalar_one_or_none()
    if assignment and not has_essay:
        assignment.status = "COMPLETED"

    await db.commit()

    pending_essay = sum(1 for tid in task_ids if tasks_map.get(tid) and tasks_map[tid].type == "ESSAY")
    return {
        "attempt_id": attempt.id,
        "status": attempt.status,
        "auto_score": auto_score,
        "max_auto_score": max_auto_score,
        "pending_essay_count": pending_essay,
    }


def _grade_test_answer(key: dict, student_input: str | None) -> int:
    if not student_input:
        return 0
    answer_type = key.get("type", "")
    correct = key.get("correct_answer") or key.get("value") or key.get("values")

    if answer_type in ("short_answer", "single_choice", ""):
        return 1 if str(student_input).strip().lower() == str(correct).strip().lower() else 0
    elif answer_type == "multiple_choice":
        try:
            student_set = set(str(x).strip() for x in str(student_input).split(","))
            correct_set = set(str(x) for x in correct)
            return 1 if student_set == correct_set else 0
        except Exception:
            return 0
    elif answer_type == "match":
        try:
            import json
            student_pairs = json.loads(student_input) if isinstance(student_input, str) else student_input
            return 1 if student_pairs == correct else 0
        except Exception:
            return 0
    elif answer_type == "sequence":
        try:
            student_seq = [int(x) for x in str(student_input).split(",")]
            return 1 if student_seq == correct else 0
        except Exception:
            return 0

    return 0
