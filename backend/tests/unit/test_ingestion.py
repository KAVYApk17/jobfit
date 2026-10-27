import pytest

from app.core.errors import InvalidPdf
from app.schemas.llm import ParsedJob, ParsedResume
from app.services.ingestion import (
    MAX_PDF_BYTES,
    extract_pdf_text,
    job_chunks,
    normalize_text,
    resume_chunks,
    split_text,
)
from tests.conftest import make_pdf


def test_extracts_text_from_pdf():
    assert "Python developer" in extract_pdf_text(make_pdf("Python developer"))


def test_rejects_non_pdf():
    with pytest.raises(InvalidPdf, match="not a PDF"):
        extract_pdf_text(b"hello, I am a text file")


def test_rejects_oversize_file():
    with pytest.raises(InvalidPdf, match="5 MB"):
        extract_pdf_text(b"%PDF" + b"0" * MAX_PDF_BYTES)


def test_rejects_pdf_without_text():
    with pytest.raises(InvalidPdf, match="No text"):
        extract_pdf_text(make_pdf(""))


def test_rejects_corrupt_pdf():
    with pytest.raises(InvalidPdf):
        extract_pdf_text(b"%PDF-1.4\ngarbage")


def test_normalize_collapses_whitespace():
    assert normalize_text("  a\t\tb  \n\n\n\n c ") == "a b\n\nc"


def test_split_text_respects_max_chars():
    text = "\n\n".join(["word " * 50] * 4)
    chunks = split_text(text, max_chars=120)
    assert all(len(c) <= 120 for c in chunks)
    assert " ".join(chunks).split() == text.split()


def test_split_text_packs_short_paragraphs():
    assert split_text("one\n\ntwo\n\nthree", max_chars=100) == ["one\ntwo\nthree"]


def test_resume_chunks_one_per_bullet(parsed_resume_data):
    parsed = ParsedResume.model_validate(parsed_resume_data)
    chunks = resume_chunks(parsed, raw_text="unused")
    assert chunks[0].startswith("Software Engineer, Example Corp: Engineered")
    assert len([c for c in chunks if ": " in c and not c.startswith(("Skills", "Education"))]) == 3
    assert chunks[-2].startswith("Skills: Python")
    assert chunks[-1] == "Education: B.Tech, Computer Science, Sample University, 2020"


def test_resume_chunks_fall_back_to_raw_text(parsed_resume_data):
    parsed = ParsedResume.model_validate({**parsed_resume_data, "experience": []})
    chunks = resume_chunks(parsed, raw_text="Summary paragraph.\n\nAnother paragraph.")
    assert chunks[0] == "Summary paragraph.\nAnother paragraph."


def test_job_chunks(parsed_job_data):
    chunks = job_chunks(ParsedJob.model_validate(parsed_job_data), jd_text="unused")
    assert chunks[:4] == parsed_job_data["responsibilities"]
    assert chunks[4].startswith("Required skills: Python")
    assert chunks[5] == "Preferred skills: LangGraph, React"
