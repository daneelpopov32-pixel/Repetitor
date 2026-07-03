from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine, AsyncEngine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_size=5, max_overflow=10)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Separate engine for Celery tasks to avoid connection pool conflicts
celery_engine: AsyncEngine | None = None


def get_celery_session_factory():
    global celery_engine
    if celery_engine is None:
        celery_engine = create_async_engine(
            settings.DATABASE_URL, echo=False, pool_size=2, max_overflow=5
        )
    return async_sessionmaker(celery_engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session
