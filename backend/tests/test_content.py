import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_subjects(client: AsyncClient, test_subject):
    resp = await client.get("/api/v1/themes/subjects")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["name"] == "История"


@pytest.mark.asyncio
async def test_get_theme_tree(client: AsyncClient, test_subject, test_theme):
    resp = await client.get(f"/api/v1/themes/tree?subject_id={test_subject.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["subject_id"] == str(test_subject.id)
    assert len(data["themes"]) >= 1
    assert data["themes"][0]["name"] == "Древний мир"
    assert data["themes"][0]["fipi_code"] == "1"


@pytest.mark.asyncio
async def test_create_subject(client: AsyncClient, tutor_token):
    resp = await client.post(
        "/api/v1/content/subjects",
        json={"name": "Обществознание"},
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Обществознание"


@pytest.mark.asyncio
async def test_create_theme(client: AsyncClient, tutor_token, test_subject):
    resp = await client.post(
        "/api/v1/content/themes",
        json={
            "subject_id": str(test_subject.id),
            "name": "Реформы Петра I",
            "fipi_code": "2.1",
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Реформы Петра I"
    assert data["fipi_code"] == "2.1"


@pytest.mark.asyncio
async def test_student_cannot_create_subject(client: AsyncClient, student_token):
    resp = await client.post(
        "/api/v1/content/subjects",
        json={"name": "Хакинг"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp.status_code == 403
