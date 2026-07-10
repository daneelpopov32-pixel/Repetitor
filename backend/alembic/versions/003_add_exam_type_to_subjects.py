"""add exam_type to subjects

Revision ID: 003_add_exam_type
Revises: 4787e938e827
Create Date: 2026-07-09 16:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '003_add_exam_type'
down_revision: Union[str, None] = '4787e938e827'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('subjects', sa.Column('exam_type', sa.String(length=10), nullable=False, server_default='EGE'))
    op.execute("UPDATE subjects SET exam_type = 'EGE' WHERE exam_type IS NULL")


def downgrade() -> None:
    op.drop_column('subjects', 'exam_type')
