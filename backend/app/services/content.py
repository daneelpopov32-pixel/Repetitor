from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Theme, Subject


async def get_theme_tree(db: AsyncSession, subject_id: UUID) -> dict:
    result = await db.execute(
        select(Theme)
        .where(Theme.subject_id == subject_id, Theme.parent_theme_id.is_(None))
        .options(
            selectinload(Theme.children)
            .selectinload(Theme.children)
            .selectinload(Theme.children)
        )
    )
    roots = result.scalars().unique().all()

    def build_node(theme: Theme) -> dict:
        return {
            "id": theme.id,
            "name": theme.name,
            "fipi_code": theme.fipi_code,
            "children": [build_node(c) for c in (theme.children or [])],
        }

    return {
        "subject_id": subject_id,
        "themes": [build_node(r) for r in roots],
    }


async def get_subjects(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Subject))
    subjects = result.scalars().all()
    return [{"id": s.id, "name": s.name, "exam_type": s.exam_type} for s in subjects]
