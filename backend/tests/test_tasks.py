import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_import_task_success(client: AsyncClient, tutor_token, test_subject, test_theme):
    resp = await client.post(
        "/api/v1/content/tasks/import",
        json={
            "subject_id": str(test_subject.id),
            "theme_id": str(test_theme.id),
            "type": "TEST",
            "text_content": {"text": "Когда началась Великая Отечественная война?", "options": ["1941", "1945", "1939"]},
            "correct_answer_key": {"type": "single_choice", "correct_answer": 1},
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "task_id" in data
    assert data["type"] == "TEST"


@pytest.mark.asyncio
async def test_import_task_duplicate_rejected(client: AsyncClient, tutor_token, test_subject, test_theme):
    payload = {
        "subject_id": str(test_subject.id),
        "theme_id": str(test_theme.id),
        "type": "TEST",
        "text_content": {"text": "Дубликат задания", "options": ["A", "B"]},
        "correct_answer_key": {"type": "single_choice", "correct_answer": 1},
    }
    resp1 = await client.post(
        "/api/v1/content/tasks/import",
        json=payload,
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert resp1.status_code == 200

    resp2 = await client.post(
        "/api/v1/content/tasks/import",
        json=payload,
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_import_essay_requires_criteria(client: AsyncClient, tutor_token, test_subject, test_theme):
    resp = await client.post(
        "/api/v1/content/tasks/import",
        json={
            "subject_id": str(test_subject.id),
            "theme_id": str(test_theme.id),
            "type": "ESSAY",
            "text_content": {"text": "Раскройте тему"},
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert resp.status_code == 400
    assert "criteria" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_import_essay_with_criteria(client: AsyncClient, tutor_token, test_subject, test_theme):
    resp = await client.post(
        "/api/v1/content/tasks/import",
        json={
            "subject_id": str(test_subject.id),
            "theme_id": str(test_theme.id),
            "type": "ESSAY",
            "text_content": {"text": "Раскройте тему реформ"},
            "fipi_criteria": [
                {"id": "c1", "name": "Причина", "max_score": 1},
                {"id": "c2", "name": "Пример", "max_score": 2},
            ],
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["type"] == "ESSAY"


@pytest.mark.asyncio
async def test_import_test_requires_key(client: AsyncClient, tutor_token, test_subject, test_theme):
    resp = await client.post(
        "/api/v1/content/tasks/import",
        json={
            "subject_id": str(test_subject.id),
            "theme_id": str(test_theme.id),
            "type": "TEST",
            "text_content": {"text": "Вопрос без ключа"},
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert resp.status_code == 400
    assert "correct_answer_key" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient, tutor_token, test_task):
    resp = await client.get(
        "/api/v1/content/tasks",
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) >= 1


@pytest.mark.asyncio
async def test_list_tasks_filter_by_type(client: AsyncClient, tutor_token, test_task, test_essay_task):
    resp = await client.get(
        "/api/v1/content/tasks?task_type=ESSAY",
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    tasks = data["tasks"]
    assert all(t["type"] == "ESSAY" for t in tasks)
