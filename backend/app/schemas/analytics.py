from __future__ import annotations
from uuid import UUID
from pydantic import BaseModel


class DynamicsPoint(BaseModel):
    date: str
    score: int


class ThemeScore(BaseModel):
    theme_id: UUID
    name: str
    success_rate: float


class DashboardResponse(BaseModel):
    student_id: UUID
    total_tests: int
    average_score: float
    dynamics: list[DynamicsPoint]
    weak_themes: list[ThemeScore]
    strong_themes: list[ThemeScore]
