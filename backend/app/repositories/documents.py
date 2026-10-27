"""Resume and job access. Every query is scoped by user_id; another user's row reads as not found."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.models import Job, Resume


class ResumeRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: UUID, filename: str, raw_text: str) -> Resume:
        resume = Resume(user_id=user_id, filename=filename, raw_text=raw_text)
        self.db.add(resume)
        self.db.flush()
        return resume

    def list(self, user_id: UUID) -> Sequence[Resume]:
        stmt = select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
        return self.db.scalars(stmt).all()

    def get(self, user_id: UUID, resume_id: UUID) -> Resume:
        resume = self.db.scalar(select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id))
        if resume is None:
            raise NotFound("Resume not found")
        return resume

    def set_parsed(self, user_id: UUID, resume_id: UUID, parsed: dict) -> None:
        self.get(user_id, resume_id).parsed = parsed

    def delete(self, user_id: UUID, resume_id: UUID) -> None:
        self.db.delete(self.get(user_id, resume_id))


class JobRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: UUID, title: str, company: str, jd_text: str) -> Job:
        job = Job(user_id=user_id, title=title, company=company, jd_text=jd_text)
        self.db.add(job)
        self.db.flush()
        return job

    def list(self, user_id: UUID) -> Sequence[Job]:
        stmt = select(Job).where(Job.user_id == user_id).order_by(Job.created_at.desc())
        return self.db.scalars(stmt).all()

    def get(self, user_id: UUID, job_id: UUID) -> Job:
        job = self.db.scalar(select(Job).where(Job.id == job_id, Job.user_id == user_id))
        if job is None:
            raise NotFound("Job not found")
        return job

    def set_parsed(self, user_id: UUID, job_id: UUID, parsed: dict) -> None:
        self.get(user_id, job_id).parsed = parsed
