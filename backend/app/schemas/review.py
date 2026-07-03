from __future__ import annotations
from uuid import UUID
from pydantic import BaseModel


class AiCheckRequest(BaseModel):
    task_id: UUID
    student_answer: str


class AiCheckResponse(BaseModel):
    ai_feedback: str
    suggested_scores: dict[str, int]


class GradeRequest(BaseModel):
    answer_id: UUID
    scores: dict[str, int]
    comment: str = ""


class GradeResponse(BaseModel):
    answer_id: UUID
    manual_score: int
    status: str
    attempt_status: str
