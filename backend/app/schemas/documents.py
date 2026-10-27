from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.llm import ParsedJob, ParsedResume


class ResumeSummary(BaseModel):
    id: UUID
    filename: str
    created_at: datetime
    parsed: bool
    skills_count: int


class ResumeOut(BaseModel):
    id: UUID
    filename: str
    created_at: datetime
    parsed: ParsedResume | None


class JobIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    company: str = Field(default="", max_length=200)
    jd_text: str = Field(min_length=50, max_length=20_000)


class JobSummary(BaseModel):
    id: UUID
    title: str
    company: str
    created_at: datetime
    parsed: bool
    required_skills_count: int


class JobOut(BaseModel):
    id: UUID
    title: str
    company: str
    jd_text: str
    created_at: datetime
    parsed: ParsedJob | None
