"""PDF to text, and text to chunks for embedding."""

import io
import logging
import re

from pypdf import PdfReader

from app.core.errors import InvalidPdf
from app.schemas.llm import ParsedJob, ParsedResume

logger = logging.getLogger(__name__)

MAX_PDF_BYTES = 5 * 1024 * 1024
# Real resumes are well under this; longer text is almost always a scanned book or a wrong file.
MAX_TEXT_CHARS = 40_000


def extract_pdf_text(data: bytes) -> str:
    if len(data) > MAX_PDF_BYTES:
        raise InvalidPdf("The PDF is larger than 5 MB.")
    if not data.startswith(b"%PDF"):
        raise InvalidPdf("The file is not a PDF.")
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception:
        logger.warning("pdf extraction failed", exc_info=True)
        raise InvalidPdf("The PDF could not be read. Try exporting it again.")

    text = normalize_text("\n\n".join(pages))
    if not text:
        raise InvalidPdf("No text found in the PDF. Scanned resumes are not supported yet.")
    if len(text) > MAX_TEXT_CHARS:
        raise InvalidPdf("The PDF has too much text to be a resume.")
    return text


def normalize_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_text(text: str, max_chars: int = 600) -> list[str]:
    """Pack paragraphs into chunks of at most max_chars, splitting long paragraphs on spaces."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for piece in paragraphs:
        while len(piece) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            cut = piece.rfind(" ", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            chunks.append(piece[:cut].strip())
            piece = piece[cut:].strip()
        if current and len(current) + 1 + len(piece) > max_chars:
            chunks.append(current)
            current = piece
        else:
            current = f"{current}\n{piece}" if current else piece
    if current:
        chunks.append(current)
    return chunks


def resume_chunks(parsed: ParsedResume, raw_text: str) -> list[str]:
    """One chunk per experience bullet, so citations and grounding point at a single claim."""
    chunks: list[str] = []
    for role in parsed.experience:
        header = ", ".join(p for p in (role.title, role.company) if p)
        for bullet in role.bullets:
            bullet = bullet.strip()
            if bullet:
                chunks.append(f"{header}: {bullet}" if header else bullet)
    if not chunks:
        chunks.extend(split_text(raw_text))
    if parsed.skills:
        chunks.append("Skills: " + ", ".join(parsed.skills))
    for edu in parsed.education:
        parts = [edu.degree, edu.field, edu.institution, edu.end]
        chunks.append("Education: " + ", ".join(p for p in parts if p))
    return chunks


def job_chunks(parsed: ParsedJob, jd_text: str) -> list[str]:
    chunks = [r.strip() for r in parsed.responsibilities if r.strip()]
    if not chunks:
        chunks.extend(split_text(jd_text))
    if parsed.required_skills:
        chunks.append("Required skills: " + ", ".join(parsed.required_skills))
    if parsed.preferred_skills:
        chunks.append("Preferred skills: " + ", ".join(parsed.preferred_skills))
    return chunks
