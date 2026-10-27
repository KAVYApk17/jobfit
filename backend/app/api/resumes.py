from uuid import UUID

from fastapi import APIRouter, Response, UploadFile

from app.api.deps import CurrentUser, Db
from app.repositories import ResumeRepo
from app.schemas.documents import ResumeOut, ResumeSummary
from app.schemas.task import TaskAccepted
from app.services.documents import ResumeService
from app.services.ingestion import MAX_PDF_BYTES

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("", status_code=202, response_model=TaskAccepted)
def upload_resume(file: UploadFile, user_id: CurrentUser, db: Db) -> TaskAccepted:
    # Read one byte past the limit so oversize files are rejected without loading them whole.
    data = file.file.read(MAX_PDF_BYTES + 1)
    task = ResumeService(db).upload(user_id, file.filename or "resume.pdf", data)
    return TaskAccepted(task_id=task.id, status=task.status)


@router.get("", response_model=list[ResumeSummary])
def list_resumes(user_id: CurrentUser, db: Db) -> list[ResumeSummary]:
    return [
        ResumeSummary(
            id=r.id,
            filename=r.filename,
            created_at=r.created_at,
            parsed=r.parsed is not None,
            skills_count=len((r.parsed or {}).get("skills", [])),
        )
        for r in ResumeRepo(db).list(user_id)
    ]


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: UUID, user_id: CurrentUser, db: Db) -> ResumeOut:
    r = ResumeRepo(db).get(user_id, resume_id)
    return ResumeOut(id=r.id, filename=r.filename, created_at=r.created_at, parsed=r.parsed)


@router.delete("/{resume_id}", status_code=204)
def delete_resume(resume_id: UUID, user_id: CurrentUser, db: Db) -> Response:
    ResumeService(db).delete(user_id, resume_id)
    return Response(status_code=204)
