"""
Tests list API with search, filters, assignment, and status tracking.
"""
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User, Test, TestTask, TestAssignment, Task, Theme, TutorStudent, Attempt, Answer
from app.utils.deps import require_role

router = APIRouter(prefix="/tests", tags=["Tests"])


class CreateTestRequest(BaseModel):
    title: str
    tasks: list[dict] = []
    time_limit_minutes: int | None = None


@router.post("")
async def create_test(
    data: CreateTestRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    test = Test(tutor_id=user.id, title=data.title, time_limit_minutes=data.time_limit_minutes)
    db.add(test)
    await db.flush()
    for i, t in enumerate(data.tasks):
        db.add(TestTask(test_id=test.id, task_id=UUID(t["task_id"]), order_number=t.get("order_number", i + 1)))
    await db.commit()
    return {"test_id": str(test.id), "title": test.title, "time_limit_minutes": test.time_limit_minutes}


@router.get("")
async def list_tests(
    search: str = Query(None, description="Search by test title or student name"),
    theme_ids: str = Query(None, description="Comma-separated theme IDs"),
    student_ids: str = Query(None, description="Comma-separated student IDs"),
    date_from: str = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: str = Query(None, description="Filter to date (YYYY-MM-DD)"),
    min_tasks: int = Query(None, description="Min task count"),
    max_tasks: int = Query(None, description="Max task count"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    # Base query
    query = select(Test).where(Test.tutor_id == user.id)

    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Test.title.ilike(search_term),
            )
        )

    # Date filters
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
            query = query.where(Test.created_at >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to + "T23:59:59")
            query = query.where(Test.created_at <= dt_to)
        except ValueError:
            pass

    query = query.order_by(Test.created_at.desc())
    result = await db.execute(query)
    tests = result.scalars().all()

    # Post-process filters that require joins
    out = []
    for t in tests:
        # Get task count and theme IDs
        task_result = await db.execute(
            select(TestTask.task_id, Task.theme_id)
            .join(Task, Task.id == TestTask.task_id)
            .where(TestTask.test_id == t.id)
        )
        task_rows = task_result.all()
        task_count = len(task_rows)
        test_theme_ids = list(set(str(r[1]) for r in task_rows if r[1]))

        # Theme filter
        if theme_ids:
            filter_themes = set(theme_ids.split(","))
            if not filter_themes.intersection(test_theme_ids):
                continue

        # Task count filter
        if min_tasks is not None and task_count < min_tasks:
            continue
        if max_tasks is not None and task_count > max_tasks:
            continue

        # Get assignments with eager-loaded student and profile
        assign_result = await db.execute(
            select(TestAssignment)
            .where(TestAssignment.test_id == t.id)
            .options(
                selectinload(TestAssignment.student)
                .selectinload(User.profile)
            )
        )
        assignments = assign_result.scalars().all()

        # Student filter
        if student_ids:
            filter_students = set(student_ids.split(","))
            test_student_ids = {str(a.student_id) for a in assignments}
            if not filter_students.intersection(test_student_ids):
                continue

        # Search by student name
        if search and not any(
            search.lower() in (a.student.profile.first_name + " " + a.student.profile.last_name).lower()
            for a in assignments if a.student and a.student.profile
        ):
            # Also check title
            if search.lower() not in t.title.lower():
                continue

        # Build assignment list with statuses and progress
        assignment_list = []
        for a in assignments:
            student_name = ""
            if a.student and a.student.profile:
                student_name = f"{a.student.profile.last_name} {a.student.profile.first_name}"

            # Determine status
            status = "new"
            if a.status == "IN_PROGRESS":
                status = "in_progress"
            elif a.status == "COMPLETED":
                status = "completed"
            elif a.status == "ASSIGNED":
                # Check if student has viewed (any attempt exists)
                attempt_result = await db.execute(
                    select(func.count(Attempt.id)).where(
                        Attempt.test_id == t.id,
                        Attempt.student_id == a.student_id,
                    )
                )
                attempt_count = attempt_result.scalar() or 0
                if attempt_count > 0:
                    status = "viewed"

            progress = await _calc_student_progress(db, t.id, a.student_id, task_count)

            assignment_list.append({
                "assignment_id": str(a.id),
                "student_id": str(a.student_id),
                "student_name": student_name,
                "status": status,
                "assigned_at": a.assigned_at.isoformat() if a.assigned_at else None,
                **progress,
            })

        out.append({
            "test_id": str(t.id),
            "title": t.title,
            "time_limit_minutes": t.time_limit_minutes,
            "tasks_count": task_count,
            "theme_ids": test_theme_ids,
            "assignments": assignment_list,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })

    return out


@router.get("/student")
async def get_student_tests(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("STUDENT")),
):
    """Get tests assigned to the current student."""
    # Get assignments for this student
    assign_result = await db.execute(
        select(TestAssignment, Test)
        .join(Test, Test.id == TestAssignment.test_id)
        .where(TestAssignment.student_id == user.id)
        .order_by(TestAssignment.assigned_at.desc())
    )
    rows = assign_result.all()

    out = []
    for assignment, test in rows:
        # Check if student has an attempt
        attempt_result = await db.execute(
            select(Attempt).where(
                Attempt.test_id == test.id,
                Attempt.student_id == user.id,
            )
        )
        attempt = attempt_result.scalars().first()

        # Get task count
        task_count_result = await db.execute(
            select(func.count(TestTask.task_id)).where(TestTask.test_id == test.id)
        )
        task_count = task_count_result.scalar() or 0

        out.append({
            "test_id": str(test.id),
            "title": test.title,
            "time_limit_minutes": test.time_limit_minutes,
            "tasks_count": task_count,
            "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
            "assignment_status": assignment.status,
            "attempt_id": str(attempt.id) if attempt else None,
            "attempt_status": attempt.status if attempt else None,
        })

    return out


@router.get("/{test_id}")
async def get_test(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    result = await db.execute(
        select(Test)
        .where(Test.id == test_id, Test.tutor_id == user.id)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    tasks_result = await db.execute(
        select(TestTask, Task)
        .join(Task, Task.id == TestTask.task_id)
        .where(TestTask.test_id == test_id)
        .order_by(TestTask.order_number)
    )
    rows = tasks_result.all()

    # Get total tasks for progress calculation
    total_tasks = len(rows)

    # Get theme fipi_codes for tasks
    theme_ids = list({str(t.theme_id) for _, t in rows if t.theme_id})
    theme_map = {}
    if theme_ids:
        themes_result = await db.execute(
            select(Theme).where(Theme.id.in_([UUID(tid) for tid in theme_ids]))
        )
        theme_map = {str(t.id): t.fipi_code for t in themes_result.scalars().all()}

    # Get assignments with eager-loaded student and profile
    assign_result = await db.execute(
        select(TestAssignment)
        .where(TestAssignment.test_id == test_id)
        .options(
            selectinload(TestAssignment.student)
            .selectinload(User.profile)
        )
    )
    assignments = assign_result.scalars().all()
    assignment_list = []
    for a in assignments:
        student_name = ""
        if a.student and a.student.profile:
            student_name = f"{a.student.profile.last_name} {a.student.profile.first_name}"
        status = "new"
        if a.status == "IN_PROGRESS":
            status = "in_progress"
        elif a.status == "COMPLETED":
            status = "completed"
        elif a.status == "ASSIGNED":
            attempt_result = await db.execute(
                select(func.count(Attempt.id)).where(
                    Attempt.test_id == test_id,
                    Attempt.student_id == a.student_id,
                )
            )
            if (attempt_result.scalar() or 0) > 0:
                status = "viewed"

        progress = await _calc_student_progress(db, test_id, a.student_id, total_tasks)

        assignment_list.append({
            "assignment_id": str(a.id),
            "student_id": str(a.student_id),
            "student_name": student_name,
            "status": status,
            **progress,
        })

    return {
        "test_id": str(test.id),
        "title": test.title,
        "time_limit_minutes": test.time_limit_minutes,
        "created_at": test.created_at.isoformat() if test.created_at else None,
        "tasks": [
            {
                "task_id": str(tt.task_id),
                "order_number": tt.order_number,
                "type": t.type,
                "text_content": t.text_content,
                "correct_answer_key": t.correct_answer_key,
                "fipi_criteria": t.fipi_criteria,
                "theme_id": str(t.theme_id),
                "fipi_code": theme_map.get(str(t.theme_id)),
                "exam_position": t.exam_position,
                "difficulty_level": t.difficulty_level,
            }
            for tt, t in rows
        ],
        "assignments": assignment_list,
    }


class AssignRequest(BaseModel):
    student_ids: list[UUID]


@router.post("/{test_id}/assign")
async def assign_test(
    test_id: UUID,
    data: AssignRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    result = await db.execute(
        select(Test).where(Test.id == test_id, Test.tutor_id == user.id)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    created = []
    for sid in data.student_ids:
        # Check if already assigned
        existing = await db.execute(
            select(TestAssignment).where(
                TestAssignment.test_id == test_id,
                TestAssignment.student_id == sid,
            )
        )
        if existing.scalar_one_or_none():
            continue

        a = TestAssignment(test_id=test_id, student_id=sid)
        db.add(a)
        await db.flush()
        created.append({"student_id": str(sid), "status": a.status})

    await db.commit()
    return created


async def _calc_student_progress(db: AsyncSession, test_id: UUID, student_id: UUID, total_tasks: int) -> dict:
    """Calculate progress for a single student on a test."""
    from app.models import Answer, Attempt

    # Get all attempts for this student on this test
    attempts_result = await db.execute(
        select(Attempt).where(Attempt.test_id == test_id, Attempt.student_id == student_id)
    )
    attempts = attempts_result.scalars().all()

    if not attempts:
        return {
            "progress_percent": 0,
            "answers_done": 0,
            "answers_total": total_tasks,
            "auto_score": None,
            "last_activity": None,
        }

    # Use the latest attempt for progress
    latest = max(attempts, key=lambda a: a.started_at or datetime.min)

    # Count answers with non-empty student_input
    answers_result = await db.execute(
        select(Answer).where(Answer.attempt_id == latest.id)
    )
    answers = answers_result.scalars().all()
    answers_done = sum(1 for a in answers if a.student_input and a.student_input.strip())

    # Sum auto_score from answers
    auto_score = sum(a.auto_score or 0 for a in answers)

    # Last activity = latest answer updated_at
    last_activity = None
    for a in answers:
        if a.updated_at:
            if last_activity is None or a.updated_at > last_activity:
                last_activity = a.updated_at

    progress_percent = round(answers_done / total_tasks * 100) if total_tasks > 0 else 0

    return {
        "progress_percent": progress_percent,
        "answers_done": answers_done,
        "answers_total": total_tasks,
        "auto_score": auto_score if auto_score > 0 else None,
        "last_activity": last_activity.isoformat() if last_activity else None,
    }


@router.get("/{test_id}/assignments")
async def get_test_assignments(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    """Get assignments with progress for a specific test."""
    result = await db.execute(
        select(Test).where(Test.id == test_id, Test.tutor_id == user.id)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Get total tasks
    task_count_result = await db.execute(
        select(func.count(TestTask.task_id)).where(TestTask.test_id == test_id)
    )
    total_tasks = task_count_result.scalar() or 0

    # Get assignments
    assign_result = await db.execute(
        select(TestAssignment)
        .where(TestAssignment.test_id == test_id)
        .options(
            selectinload(TestAssignment.student)
            .selectinload(User.profile)
        )
    )
    assignments = assign_result.scalars().all()

    out = []
    for a in assignments:
        student_name = ""
        if a.student and a.student.profile:
            student_name = f"{a.student.profile.last_name} {a.student.profile.first_name}"

        status = "new"
        if a.status == "IN_PROGRESS":
            status = "in_progress"
        elif a.status == "COMPLETED":
            status = "completed"
        elif a.status == "ASSIGNED":
            attempt_result = await db.execute(
                select(func.count(Attempt.id)).where(
                    Attempt.test_id == test_id,
                    Attempt.student_id == a.student_id,
                )
            )
            if (attempt_result.scalar() or 0) > 0:
                status = "viewed"

        progress = await _calc_student_progress(db, test_id, a.student_id, total_tasks)

        out.append({
            "assignment_id": str(a.id),
            "student_id": str(a.student_id),
            "student_name": student_name,
            "status": status,
            "assigned_at": a.assigned_at.isoformat() if a.assigned_at else None,
            **progress,
        })

    return out


@router.delete("/{test_id}/assignments/{student_id}")
async def unassign_student(
    test_id: UUID,
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    """Remove a student from a test."""
    result = await db.execute(
        select(Test).where(Test.id == test_id, Test.tutor_id == user.id)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    assign_result = await db.execute(
        select(TestAssignment).where(
            TestAssignment.test_id == test_id,
            TestAssignment.student_id == student_id,
        )
    )
    assignment = assign_result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    await db.delete(assignment)
    await db.commit()
    return {"status": "removed"}


@router.get("/{test_id}/assignments/{student_id}/answers")
async def get_student_answers(
    test_id: UUID,
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    """Get student's answers for a specific test."""
    result = await db.execute(
        select(Test).where(Test.id == test_id, Test.tutor_id == user.id)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Get the latest attempt
    attempt_result = await db.execute(
        select(Attempt).where(
            Attempt.test_id == test_id,
            Attempt.student_id == student_id,
        ).order_by(Attempt.started_at.desc())
    )
    attempt = attempt_result.scalars().first()
    if not attempt:
        raise HTTPException(status_code=404, detail="No attempts found")

    # Get tasks in order
    task_rows_result = await db.execute(
        select(TestTask, Task)
        .join(Task, Task.id == TestTask.task_id)
        .where(TestTask.test_id == test_id)
        .order_by(TestTask.order_number)
    )
    task_rows = task_rows_result.all()

    # Get answers
    answers_result = await db.execute(
        select(Answer).where(Answer.attempt_id == attempt.id)
    )
    answers_map = {str(a.task_id): a for a in answers_result.scalars().all()}

    out = []
    for tt, task in task_rows:
        answer = answers_map.get(str(task.id))
        out.append({
            "task_id": str(task.id),
            "order_number": tt.order_number,
            "type": task.type,
            "text_content": task.text_content,
            "fipi_criteria": task.fipi_criteria,
            "theme_id": str(task.theme_id),
            "student_input": answer.student_input if answer else None,
            "auto_score": answer.auto_score if answer else None,
            "manual_score": answer.manual_score if answer else None,
            "ai_feedback": answer.ai_feedback if answer else None,
            "exam_position": task.exam_position,
            "difficulty_level": task.difficulty_level,
        })

    return {
        "attempt_id": str(attempt.id),
        "status": attempt.status,
        "auto_score": attempt.auto_score,
        "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
        "finished_at": attempt.finished_at.isoformat() if attempt.finished_at else None,
        "answers": out,
    }


@router.delete("/{test_id}")
async def delete_test(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    result = await db.execute(
        select(Test).where(Test.id == test_id, Test.tutor_id == user.id)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    from app.models import Answer, Attempt

    # Delete answers linked to attempts of this test
    await db.execute(
        delete(Answer).where(
            Answer.attempt_id.in_(
                select(Attempt.id).where(Attempt.test_id == test_id)
            )
        )
    )
    # Delete attempts for this test
    await db.execute(delete(Attempt).where(Attempt.test_id == test_id))
    # Delete test_task and test_assignment links
    await db.execute(delete(TestTask).where(TestTask.test_id == test_id))
    await db.execute(delete(TestAssignment).where(TestAssignment.test_id == test_id))
    # Delete the test itself
    await db.delete(test)
    await db.commit()
    return {"status": "deleted"}


@router.delete("/{test_id}/tasks/{task_id}")
async def remove_task_from_test(
    test_id: UUID,
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    result = await db.execute(
        select(Test).where(Test.id == test_id, Test.tutor_id == user.id)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    await db.execute(
        delete(TestTask).where(TestTask.test_id == test_id, TestTask.task_id == task_id)
    )
    await db.commit()
    return {"status": "deleted"}


@router.post("/{test_id}/tasks/{task_id}/replace")
async def replace_task(
    test_id: UUID,
    task_id: UUID,
    new_type: str = Query(None, description="New task type: TEST or ESSAY"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("TUTOR")),
):
    """Replace a task in the test with another from the same theme."""
    import httpx

    result = await db.execute(
        select(Test).where(Test.id == test_id, Test.tutor_id == user.id)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Find the task to replace
    tt_result = await db.execute(
        select(TestTask).where(TestTask.test_id == test_id, TestTask.task_id == task_id)
    )
    tt = tt_result.scalar_one_or_none()
    if not tt:
        raise HTTPException(status_code=404, detail="Task not found in test")

    # Get the existing task and its theme
    task_result = await db.execute(select(Task).where(Task.id == task_id))
    existing_task = task_result.scalar_one_or_none()
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    theme_result = await db.execute(select(Theme).where(Theme.id == existing_task.theme_id))
    theme = theme_result.scalar_one_or_none()
    if not theme or not theme.fipi_code:
        raise HTTPException(status_code=404, detail="Theme or FIPI code not found for this task")

    new_theme_code = theme.fipi_code
    fetch_type = new_type if new_type else existing_task.type

    # Fetch a new task from FIPI
    try:
        async with httpx.AsyncClient(timeout=30, verify=False) as client:
            resp = await client.post(
                "https://ege.fipi.ru/bank/questions.php",
                data={"search": "1", "pagesize": "10", "proj": "068A227D253BA6C04D0C832387FD0D89", "theme": new_theme_code, "page": "1"},
                headers={"User-Agent": "Mozilla/5.0", "Referer": "https://ege.fipi.ru/bank/"},
            )
            html = resp.content.decode("windows-1251", errors="replace")
            from app.tasks.fipi_tasks import _extract_tasks_from_html
            all_tasks = _extract_tasks_from_html(html)
            if not all_tasks:
                raise HTTPException(status_code=404, detail="No tasks found on FIPI for this theme")

            # Filter by requested type
            tasks = [t for t in all_tasks if t.get("type") == fetch_type]
            if not tasks:
                raise HTTPException(status_code=404, detail=f"No {fetch_type} tasks found on FIPI for this theme")

            # Pick a task not already in the test
            existing_result = await db.execute(select(TestTask.task_id).where(TestTask.test_id == test_id))
            existing_ids = {str(r[0]) for r in existing_result.all()}

            new_task_data = None
            for t in tasks:
                if t.get("guid") not in existing_ids:
                    new_task_data = t
                    break
            if not new_task_data:
                new_task_data = tasks[0]

            # Save new task
            from app.services.content_parser import compute_text_hash
            from app.tasks.fipi_tasks import _build_text_content

            text_content = _build_text_content(new_task_data)

            new_task = Task(
                subject_id=theme.subject_id,
                theme_id=theme.id,
                type=new_task_data["type"],
                text_content=text_content,
                correct_answer_key=None,
                fipi_criteria=None,
                source_url=f"https://ege.fipi.ru/bank/questions.php?theme={new_theme_code}",
                metadata_={"text_hash": compute_text_hash(text_content), "fipi_guid": new_task_data.get("guid")},
            )
            db.add(new_task)
            await db.flush()

            # Update test_task
            tt.task_id = new_task.id
            await db.commit()

            return {"status": "replaced", "new_task_id": str(new_task.id)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
