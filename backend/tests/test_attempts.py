import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_start_attempt(client: AsyncClient, tutor_token, student_token, test_task, test_student, db):
    create_resp = await client.post(
        "/api/v1/tests",
        json={
            "title": "Попытка теста",
            "time_limit_minutes": 60,
            "tasks": [{"task_id": str(test_task.id), "order_number": 1}],
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert create_resp.status_code == 200
    test_id = create_resp.json()["test_id"]

    await client.post(
        f"/api/v1/tests/{test_id}/assign",
        json={"student_ids": [str(test_student.id)]},
        headers={"Authorization": f"Bearer {tutor_token}"},
    )

    resp = await client.post(
        f"/api/v1/attempts/0/start?test_id={test_id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["time_limit_minutes"] == 60


@pytest.mark.asyncio
async def test_save_answer_and_submit(client: AsyncClient, tutor_token, student_token, test_task, test_student, db):
    create_resp = await client.post(
        "/api/v1/tests",
        json={
            "title": "Сохранение ответа",
            "tasks": [{"task_id": str(test_task.id), "order_number": 1}],
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    test_id = create_resp.json()["test_id"]

    await client.post(
        f"/api/v1/tests/{test_id}/assign",
        json={"student_ids": [str(test_student.id)]},
        headers={"Authorization": f"Bearer {tutor_token}"},
    )

    start_resp = await client.post(
        f"/api/v1/attempts/0/start?test_id={test_id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    attempt_id = start_resp.json()["attempt_id"]

    save_resp = await client.patch(
        f"/api/v1/attempts/{attempt_id}/answers/{test_task.id}",
        json={"student_input": "1"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert save_resp.status_code == 200
    assert save_resp.json()["status"] == "saved"

    get_resp = await client.get(
        f"/api/v1/attempts/{attempt_id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert get_resp.status_code == 200

    tasks_resp = await client.get(
        f"/api/v1/attempts/{attempt_id}/tasks",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert tasks_resp.status_code == 200
    assert len(tasks_resp.json()["tasks"]) >= 1

    submit_resp = await client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert submit_resp.status_code == 200
    data = submit_resp.json()
    assert data["status"] in ("COMPLETED", "PENDING_REVIEW")
    assert data["auto_score"] >= 0


@pytest.mark.asyncio
async def test_correct_answer_grading(client: AsyncClient, tutor_token, student_token, test_task, test_student, db):
    create_resp = await client.post(
        "/api/v1/tests",
        json={
            "title": "Проверка оценки",
            "tasks": [{"task_id": str(test_task.id), "order_number": 1}],
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    test_id = create_resp.json()["test_id"]

    await client.post(
        f"/api/v1/tests/{test_id}/assign",
        json={"student_ids": [str(test_student.id)]},
        headers={"Authorization": f"Bearer {tutor_token}"},
    )

    start_resp = await client.post(
        f"/api/v1/attempts/0/start?test_id={test_id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    attempt_id = start_resp.json()["attempt_id"]

    await client.patch(
        f"/api/v1/attempts/{attempt_id}/answers/{test_task.id}",
        json={"student_input": "1"},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    submit_resp = await client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    data = submit_resp.json()
    assert data["auto_score"] == 1
    assert data["max_auto_score"] == 1


@pytest.mark.asyncio
async def test_wrong_answer_grading(client: AsyncClient, tutor_token, student_token, test_task, test_student, db):
    create_resp = await client.post(
        "/api/v1/tests",
        json={
            "title": "Неверный ответ",
            "tasks": [{"task_id": str(test_task.id), "order_number": 1}],
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    test_id = create_resp.json()["test_id"]

    await client.post(
        f"/api/v1/tests/{test_id}/assign",
        json={"student_ids": [str(test_student.id)]},
        headers={"Authorization": f"Bearer {tutor_token}"},
    )

    start_resp = await client.post(
        f"/api/v1/attempts/0/start?test_id={test_id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    attempt_id = start_resp.json()["attempt_id"]

    await client.patch(
        f"/api/v1/attempts/{attempt_id}/answers/{test_task.id}",
        json={"student_input": "2"},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    submit_resp = await client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    data = submit_resp.json()
    assert data["auto_score"] == 0


@pytest.mark.asyncio
async def test_essay_attempt_pending_review(client: AsyncClient, tutor_token, student_token, test_essay_task, test_student, db):
    create_resp = await client.post(
        "/api/v1/tests",
        json={
            "title": "Тест с эссе",
            "tasks": [{"task_id": str(test_essay_task.id), "order_number": 1}],
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    test_id = create_resp.json()["test_id"]

    await client.post(
        f"/api/v1/tests/{test_id}/assign",
        json={"student_ids": [str(test_student.id)]},
        headers={"Authorization": f"Bearer {tutor_token}"},
    )

    start_resp = await client.post(
        f"/api/v1/attempts/0/start?test_id={test_id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    attempt_id = start_resp.json()["attempt_id"]

    await client.patch(
        f"/api/v1/attempts/{attempt_id}/answers/{test_essay_task.id}",
        json={"student_input": "Реформы Петра I включали модернизацию армии, создание флота, строительство Санкт-Петербурга."},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    submit_resp = await client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    data = submit_resp.json()
    assert data["status"] == "PENDING_REVIEW"
    assert data["pending_essay_count"] >= 1
