from __future__ import annotations
from uuid import UUID
from pydantic import BaseModel


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
    exam_type: str = "EGE"
