"""Contracts for every LLM call. Responses are validated against these models."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class Role(BaseModel):
    company: str
    title: str
    start: str | None
    end: str | None
    bullets: list[str]


class Education(BaseModel):
    institution: str
    degree: str | None
    field: str | None
    end: str | None


class ParsedResume(BaseModel):
    name: str | None
    total_years: float
    skills: list[str]
    experience: list[Role]
    education: list[Education]


class ParsedJob(BaseModel):
    title: str
    min_years: float | None
    required_skills: list[str]
    preferred_skills: list[str]
    responsibilities: list[str]


class SkillReason(BaseModel):
    skill: str
    status: Literal["matched", "partial", "missing"]
    reason: str
    evidence_chunk_ids: list[UUID]


class MatchExplanation(BaseModel):
    summary: str
    skills: list[SkillReason]


class BulletSuggestion(BaseModel):
    original: str
    suggested: str
    claims: list[str]
    source_chunk_ids: list[UUID]
