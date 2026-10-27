"""Sample LLM outputs must validate against every Pydantic contract."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.llm import BulletSuggestion, MatchExplanation, ParsedJob, ParsedResume


def test_parsed_resume_fixture_validates(parsed_resume_data):
    parsed = ParsedResume.model_validate(parsed_resume_data)
    assert parsed.total_years == 5
    assert parsed.experience[0].bullets


def test_parsed_job_fixture_validates(parsed_job_data):
    parsed = ParsedJob.model_validate(parsed_job_data)
    assert parsed.min_years == 4
    assert "Docker" in parsed.required_skills


def test_match_explanation_rejects_unknown_status():
    with pytest.raises(ValidationError):
        MatchExplanation.model_validate(
            {"summary": "s", "skills": [{"skill": "Docker", "status": "maybe", "reason": "r", "evidence_chunk_ids": []}]}
        )


def test_bullet_suggestion_validates():
    chunk_id = uuid4()
    suggestion = BulletSuggestion.model_validate(
        {"original": "a", "suggested": "b", "claims": ["Python"], "source_chunk_ids": [str(chunk_id)]}
    )
    assert suggestion.source_chunk_ids == [chunk_id]
