"""Celery tasks. Each one keeps its tasks row in step: queued -> running -> done or failed."""

import logging
from collections.abc import Callable
from uuid import UUID

from celery import Task as CeleryTask
from celery.exceptions import Reject
from celery.signals import worker_process_init
from sqlalchemy.orm import Session

from app.clients.embeddings import get_embedder
from app.config import get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.db import SessionLocal
from app.repositories import TaskRepo
from app.services.documents import JobService, ResumeService
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


@worker_process_init.connect
def init_worker_process(**_) -> None:
    configure_logging(get_settings().log_level)
    # Load the model once per worker process instead of on the first job.
    get_embedder()


def _run(celery_task: CeleryTask, task_id: str, user_id: str, work: Callable[[Session], object]) -> None:
    tid, uid = UUID(task_id), UUID(user_id)
    log = {"task_id": task_id}
    with SessionLocal() as db:
        tasks = TaskRepo(db)
        tasks.mark_running(uid, tid)
        db.commit()
        try:
            work(db)
            tasks.mark_done(uid, tid)
            db.commit()
            logger.info("task done", extra=log)
            return
        except Exception as exc:
            db.rollback()
            error = exc.message if isinstance(exc, AppError) else "Unexpected error while processing."
            retryable = exc.retryable if isinstance(exc, AppError) else True
            attempt = celery_task.request.retries
            logger.warning("task error", extra=log, exc_info=not isinstance(exc, AppError))

            if retryable and attempt < MAX_RETRIES:
                tasks.mark_retrying(uid, tid, error)
                db.commit()
                raise celery_task.retry(exc=exc, countdown=2 ** (attempt + 1))

            tasks.mark_failed(uid, tid, error)
            db.commit()
            # requeue=False sends the message to the dead-letter queue.
            raise Reject(str(exc), requeue=False)


@celery_app.task(name="jobfit.parse_resume", bind=True, max_retries=MAX_RETRIES)
def parse_resume(self: CeleryTask, task_id: str, user_id: str, resume_id: str) -> None:
    _run(self, task_id, user_id, lambda db: ResumeService(db).parse(UUID(user_id), UUID(resume_id)))


@celery_app.task(name="jobfit.parse_job", bind=True, max_retries=MAX_RETRIES)
def parse_job(self: CeleryTask, task_id: str, user_id: str, job_id: str) -> None:
    _run(self, task_id, user_id, lambda db: JobService(db).parse(UUID(user_id), UUID(job_id)))
