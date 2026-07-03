import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_review_queue(client: AsyncClient, tutor_token):
    resp = await client.get(
        "/api/v1/review/queue",
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_grade_answer(client: AsyncClient, tutor_token, student_token, test_essay_task, test_student, db):
    create_resp = await client.post(
        "/api/v1/tests",
        json={
            "title": "Для проверки",
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
        json={"student_input": "Ответ ученика"},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    await client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    queue_resp = await client.get(
        "/api/v1/review/queue",
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    queue = queue_resp.json()
    assert len(queue) >= 1

    answer_id = queue[0]["answer_id"]

    grade_resp = await client.post(
        "/api/v1/review/grade",
        json={
            "answer_id": answer_id,
            "scores": {"criterion_1": 1, "criterion_2": 2},
            "comment": "Хороший ответ",
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert grade_resp.status_code == 200
    data = grade_resp.json()
    assert data["manual_score"] == 3
    assert data["attempt_status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_student_cannot_access_review(client: AsyncClient, student_token):
    resp = await client.get(
        "/api/v1/review/queue",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp.status_code == 403
