import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "new@test.com",
        "password": "securePass123",
        "first_name": "Иван",
        "last_name": "Петров",
        "role": "STUDENT",
        "consent_152fz": True,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "STUDENT"
    assert data["email"] == "new@test.com"


@pytest.mark.asyncio
async def test_register_no_consent_rejected(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "noconsent@test.com",
        "password": "securePass123",
        "first_name": "Иван",
        "last_name": "Петров",
        "role": "STUDENT",
        "consent_152fz": False,
    })
    assert resp.status_code == 400
    assert "consent" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "email": "dup@test.com",
        "password": "securePass123",
        "first_name": "Иван",
        "last_name": "Петров",
        "role": "STUDENT",
        "consent_152fz": True,
    }
    resp1 = await client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201
    resp2 = await client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "login@test.com",
        "password": "securePass123",
        "first_name": "Тест",
        "last_name": "Логин",
        "role": "TUTOR",
        "consent_152fz": True,
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@test.com",
        "password": "securePass123",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "wrongpw@test.com",
        "password": "securePass123",
        "first_name": "Тест",
        "last_name": "Логин",
        "role": "TUTOR",
        "consent_152fz": True,
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "wrongpw@test.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_register_student_with_invitation_code(client: AsyncClient):
    reg_resp = await client.post("/api/v1/auth/register", json={
        "email": "tutor_invite@test.com",
        "password": "securePass123",
        "first_name": "Репетитор",
        "last_name": "Тестовый",
        "role": "TUTOR",
        "consent_152fz": True,
    })
    tutor_token = reg_resp.json()["access_token"]

    code_resp = await client.post(
        "/api/v1/invitation-codes",
        json={"expires_in_days": 7},
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    code = code_resp.json()["code"]

    student_resp = await client.post("/api/v1/auth/register", json={
        "email": "student_via_code@test.com",
        "password": "securePass123",
        "first_name": "Ученик",
        "last_name": "Пригласительный",
        "role": "STUDENT",
        "invitation_code": code,
        "consent_152fz": True,
    })
    assert student_resp.status_code == 201
    assert student_resp.json()["role"] == "STUDENT"
