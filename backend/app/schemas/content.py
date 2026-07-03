from __future__ import annotations
from uuid import UUID
from pydantic import BaseModel


class TaskImportRequest(BaseModel):
    subject_id: UUID
    theme_id: UUID
    type: str  # TEST or ESSAY
    text_content: dict
    correct_answer_key: dict | None = None
    fipi_criteria: list[dict] | None = None
    source_url: str | None = None


class TaskImportResponse(BaseModel):
    task_id: UUID
    type: str
    theme_id: UUID


class BulkImportRequest(BaseModel):
    url: str
    subject_id: UUID
    theme_id: UUID


class BulkImportResponse(BaseModel):
    total_parsed: int
    imported: int
    skipped_duplicates: int
    errors: list[str]


class SubjectCreate(BaseModel):
    name: str


class ThemeCreate(BaseModel):
    subject_id: UUID
    parent_theme_id: UUID | None = None
    fipi_code: str | None = None
    name: str
