import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_empty(client: AsyncClient, student_token, test_student):
    resp = await client.get(
        f"/api/v1/analytics/dashboard?student_id={test_student.id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tests"] == 0
    assert data["dynamics"] == []


@pytest.mark.asyncio
async def test_dashboard_after_test(client: AsyncClient, student_token, tutor_token, test_task, test_student, db):
    create_resp = await client.post(
        "/api/v1/tests",
        json={
            "title": "Для дашборда",
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

    await client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    dash_resp = await client.get(
        f"/api/v1/analytics/dashboard?student_id={test_student.id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert dash_resp.status_code == 200
    data = dash_resp.json()
    assert data["total_tests"] >= 1
    assert len(data["dynamics"]) >= 1
    assert data["average_score"] >= 0


@pytest.mark.asyncio
async def test_tutor_students_summary(client: AsyncClient, tutor_token):
    resp = await client.get(
        "/api/v1/analytics/tutor/students",
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_invitation_code_generation(client: AsyncClient, tutor_token):
    resp = await client.post(
        "/api/v1/invitation-codes",
        json={"expires_in_days": 7},
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "code" in data
    assert "expires_at" in data
