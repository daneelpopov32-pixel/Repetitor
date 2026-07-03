from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class TestTaskItem(BaseModel):
    task_id: UUID
    order_number: int


class TestCreateRequest(BaseModel):
    title: str
    time_limit_minutes: int | None = None
    tasks: list[TestTaskItem]


class TestResponse(BaseModel):
    test_id: UUID
    title: str
    time_limit_minutes: int | None = None
    created_at: datetime


class TestAssignRequest(BaseModel):
    student_ids: list[UUID]


class AssignmentResponse(BaseModel):
    assignment_id: UUID
    student_id: UUID
    status: str
