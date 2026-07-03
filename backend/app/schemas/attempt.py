from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class AnswerSaveRequest(BaseModel):
    student_input: str


class AnswerSaveResponse(BaseModel):
    status: str
    updated_at: datetime


class AttemptStartResponse(BaseModel):
    attempt_id: UUID
    status: str
    started_at: datetime
    time_limit_minutes: int | None = None
    server_time: datetime


class TaskListItem(BaseModel):
    task_id: UUID
    order_number: int
    type: str
    text_content: dict


class AttemptTasksResponse(BaseModel):
    attempt_id: UUID
    tasks: list[TaskListItem]


class SubmitResponse(BaseModel):
    attempt_id: UUID
    status: str
    auto_score: int
    max_auto_score: int
    pending_essay_count: int


class AttemptDetailResponse(BaseModel):
    attempt_id: UUID
    status: str
    started_at: datetime | None = None
    time_limit_minutes: int | None = None
    server_time: datetime
