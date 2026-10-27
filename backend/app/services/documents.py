"""Resume and job description intake (API side) and parsing (worker side)."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.clients.embeddings import Embedder, get_embedder
from app.clients.llm import LLMClient, get_llm_client
from app.models import Task, TaskKind
from app.repositories import JobRepo, ResumeRepo, TaskRepo
from app.schemas.llm import ParsedJob, ParsedResume
from app.services.ingestion import extract_pdf_text, job_chunks, resume_chunks
from app.services.prompts import render_prompt
from app.services.queue import enqueue
from app.vectorstore import Chunk, PgVectorStore, VectorStore

RESUME_PROMPT = "parse_resume_v1"
JOB_PROMPT = "parse_job_v1"


class _Parser:
    def __init__(
        self,
        db: Session,
        llm: LLMClient | None = None,
        embedder: Embedder | None = None,
        store: VectorStore | None = None,
    ):
        self.db = db
        self._llm = llm
        self._embedder = embedder
        self.store = store or PgVectorStore(db)
        self.tasks = TaskRepo(db)

    # The API never loads the LLM client or the embedding model; only the worker does.
    @property
    def llm(self) -> LLMClient:
        return self._llm or get_llm_client()

    @property
    def embedder(self) -> Embedder:
        return self._embedder or get_embedder()

    def _replace_chunks(self, user_id: UUID, source_type: str, source_id: UUID, texts: list[str]) -> None:
        # Delete first so a retried task overwrites its chunks instead of duplicating them.
        vectors = self.embedder.encode(texts)
        self.store.delete_source(user_id, source_id)
        self.store.add(
            user_id,
            [
                Chunk(source_type=source_type, source_id=source_id, position=i, text=t, embedding=v)
                for i, (t, v) in enumerate(zip(texts, vectors, strict=True))
            ],
        )


class ResumeService(_Parser):
    def __init__(self, db: Session, **kwargs):
        super().__init__(db, **kwargs)
        self.resumes = ResumeRepo(db)

    def upload(self, user_id: UUID, filename: str, data: bytes) -> Task:
        raw_text = extract_pdf_text(data)
        resume = self.resumes.create(user_id, filename[:255], raw_text)
        task = self.tasks.create(user_id, TaskKind.PARSE_RESUME, resume.id)
        self.db.commit()
        enqueue(self.db, task, "jobfit.parse_resume", str(resume.id))
        return task

    def parse(self, user_id: UUID, resume_id: UUID) -> ParsedResume:
        resume = self.resumes.get(user_id, resume_id)
        prompt = render_prompt(RESUME_PROMPT, resume_text=resume.raw_text)
        parsed = self.llm.structured(prompt, ParsedResume)
        self._replace_chunks(user_id, "resume", resume.id, resume_chunks(parsed, resume.raw_text))
        resume.parsed = parsed.model_dump(mode="json")
        return parsed

    def delete(self, user_id: UUID, resume_id: UUID) -> None:
        self.resumes.get(user_id, resume_id)  # 404 before touching chunks
        self.store.delete_source(user_id, resume_id)
        self.resumes.delete(user_id, resume_id)
        self.db.commit()


class JobService(_Parser):
    def __init__(self, db: Session, **kwargs):
        super().__init__(db, **kwargs)
        self.jobs = JobRepo(db)

    def create(self, user_id: UUID, title: str, company: str, jd_text: str) -> Task:
        job = self.jobs.create(user_id, title.strip(), company.strip(), jd_text.strip())
        task = self.tasks.create(user_id, TaskKind.PARSE_JOB, job.id)
        self.db.commit()
        enqueue(self.db, task, "jobfit.parse_job", str(job.id))
        return task

    def parse(self, user_id: UUID, job_id: UUID) -> ParsedJob:
        job = self.jobs.get(user_id, job_id)
        prompt = render_prompt(JOB_PROMPT, title=job.title, company=job.company or "not given", jd_text=job.jd_text)
        parsed = self.llm.structured(prompt, ParsedJob)
        self._replace_chunks(user_id, "jd", job.id, job_chunks(parsed, job.jd_text))
        job.parsed = parsed.model_dump(mode="json")
        return parsed
