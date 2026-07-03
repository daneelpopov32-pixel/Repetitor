from datetime import datetime

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models import User, Profile, Tenant, Subject, Theme, Task
from app.utils.security import hash_password, create_access_token

TEST_DB_URL = "postgresql+asyncpg://repetitor:repetitor@localhost:5432/repetitor_test"


@pytest_asyncio.fixture(loop_scope="session")
async def engine():
    eng = create_async_engine(TEST_DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def db(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(loop_scope="session")
async def client(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(loop_scope="session")
async def test_tenant(db):
    tenant = Tenant(name="Test Tenant")
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


@pytest_asyncio.fixture(loop_scope="session")
async def test_tutor(db, test_tenant):
    user = User(
        tenant_id=test_tenant.id,
        email="tutor@test.com",
        password_hash=hash_password("testpass123"),
        role="TUTOR",
    )
    db.add(user)
    await db.flush()
    profile = Profile(
        user_id=user.id,
        first_name="Тест",
        last_name="Репетитор",
        consent_152fz_at=datetime.utcnow(),
    )
    db.add(profile)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture(loop_scope="session")
async def test_student(db, test_tenant):
    user = User(
        tenant_id=test_tenant.id,
        email="student@test.com",
        password_hash=hash_password("testpass123"),
        role="STUDENT",
    )
    db.add(user)
    await db.flush()
    profile = Profile(
        user_id=user.id,
        first_name="Тест",
        last_name="Ученик",
        birth_date=datetime(2008, 5, 15).date(),
        consent_152fz_at=datetime.utcnow(),
    )
    db.add(profile)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture(loop_scope="session")
def tutor_token(test_tutor):
    return create_access_token(test_tutor.id, test_tutor.role)


@pytest_asyncio.fixture(loop_scope="session")
def student_token(test_student):
    return create_access_token(test_student.id, test_student.role)


@pytest_asyncio.fixture(loop_scope="session")
async def test_subject(db):
    subject = Subject(name="История")
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    return subject


@pytest_asyncio.fixture(loop_scope="session")
async def test_theme(db, test_subject):
    theme = Theme(subject_id=test_subject.id, fipi_code="1", name="Древний мир")
    db.add(theme)
    await db.commit()
    await db.refresh(theme)
    return theme


@pytest_asyncio.fixture(loop_scope="session")
async def test_task(db, test_subject, test_theme):
    task = Task(
        subject_id=test_subject.id,
        theme_id=test_theme.id,
        type="TEST",
        text_content={"text": "Столица России?", "options": ["Москва", "Питер", "Казань"]},
        correct_answer_key={"type": "single_choice", "correct_answer": 1},
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@pytest_asyncio.fixture(loop_scope="session")
async def test_essay_task(db, test_subject, test_theme):
    task = Task(
        subject_id=test_subject.id,
        theme_id=test_theme.id,
        type="ESSAY",
        text_content={"text": "Опишите реформы Петра I"},
        fipi_criteria=[
            {"id": "criterion_1", "name": "Названа причина", "max_score": 1},
            {"id": "criterion_2", "name": "Приведён пример", "max_score": 2},
        ],
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task
