import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_test(client: AsyncClient, tutor_token, test_task):
    resp = await client.post(
        "/api/v1/tests",
        json={
            "title": "Тест по истории",
            "time_limit_minutes": 30,
            "tasks": [{"task_id": str(test_task.id), "order_number": 1}],
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Тест по истории"
    assert data["time_limit_minutes"] == 30


@pytest.mark.asyncio
async def test_create_test_no_time_limit(client: AsyncClient, tutor_token, test_task):
    resp = await client.post(
        "/api/v1/tests",
        json={
            "title": "Без таймера",
            "tasks": [{"task_id": str(test_task.id), "order_number": 1}],
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["time_limit_minutes"] is None


@pytest.mark.asyncio
async def test_assign_test(client: AsyncClient, tutor_token, test_student, test_task):
    create_resp = await client.post(
        "/api/v1/tests",
        json={
            "title": "Тест для назначения",
            "tasks": [{"task_id": str(test_task.id), "order_number": 1}],
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    test_id = create_resp.json()["test_id"]

    resp = await client.post(
        f"/api/v1/tests/{test_id}/assign",
        json={"student_ids": [str(test_student.id)]},
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert resp.status_code == 200
    assignments = resp.json()
    assert len(assignments) == 1
    assert assignments[0]["status"] == "ASSIGNED"


@pytest.mark.asyncio
async def test_student_cannot_create_test(client: AsyncClient, student_token, test_task):
    resp = await client.post(
        "/api/v1/tests",
        json={
            "title": "Нельзя",
            "tasks": [{"task_id": str(test_task.id), "order_number": 1}],
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp.status_code == 403
