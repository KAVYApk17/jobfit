from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, Db
from app.repositories import JobRepo
from app.schemas.documents import JobIn, JobOut, JobSummary
from app.schemas.task import TaskAccepted
from app.services.documents import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", status_code=202, response_model=TaskAccepted)
def create_job(body: JobIn, user_id: CurrentUser, db: Db) -> TaskAccepted:
    task = JobService(db).create(user_id, body.title, body.company, body.jd_text)
    return TaskAccepted(task_id=task.id, status=task.status)


@router.get("", response_model=list[JobSummary])
def list_jobs(user_id: CurrentUser, db: Db) -> list[JobSummary]:
    return [
        JobSummary(
            id=j.id,
            title=j.title,
            company=j.company,
            created_at=j.created_at,
            parsed=j.parsed is not None,
            required_skills_count=len((j.parsed or {}).get("required_skills", [])),
        )
        for j in JobRepo(db).list(user_id)
    ]


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: UUID, user_id: CurrentUser, db: Db) -> JobOut:
    j = JobRepo(db).get(user_id, job_id)
    return JobOut(id=j.id, title=j.title, company=j.company, jd_text=j.jd_text, created_at=j.created_at, parsed=j.parsed)
