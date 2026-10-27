"""Publishes work to RabbitMQ by task name, so the API never imports worker code."""

import logging

from sqlalchemy.orm import Session

from app.core.errors import QueueUnavailable
from app.models import Task
from app.repositories import TaskRepo
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def enqueue(db: Session, task: Task, name: str, *args: str) -> None:
    """Publish after the task row is committed, so the worker always finds it."""
    try:
        # The Celery id equals our task id, so a redelivered message maps to the same row.
        celery_app.send_task(name, args=[str(task.id), str(task.user_id), *args], task_id=str(task.id))
    except Exception:
        logger.exception("enqueue failed", extra={"task_id": str(task.id)})
        TaskRepo(db).mark_failed(task.user_id, task.id, "Could not queue the job.")
        db.commit()
        raise QueueUnavailable("The job queue is unavailable. Please try again shortly.")
