from __future__ import annotations
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel


class ThemeNode(BaseModel):
    id: UUID
    name: str
    fipi_code: str | None = None
    children: list[ThemeNode] = []


class ThemeTreeResponse(BaseModel):
    subject_id: UUID
    themes: list[ThemeNode]
