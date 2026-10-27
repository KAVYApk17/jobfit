from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.models import Task, TaskStatus


class TaskRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: UUID, kind: str, result_ref: UUID) -> Task:
        task = Task(user_id=user_id, kind=kind, status=TaskStatus.QUEUED, attempts=0, result_ref=result_ref)
        self.db.add(task)
        self.db.flush()
        return task

    def get(self, user_id: UUID, task_id: UUID) -> Task:
        task = self.db.scalar(select(Task).where(Task.id == task_id, Task.user_id == user_id))
        if task is None:
            raise NotFound("Task not found")
        return task

    # Status updates are plain UPDATEs so they are no-ops if the user deleted their data mid-task.
    def _update(self, user_id: UUID, task_id: UUID, **values) -> None:
        stmt = update(Task).where(Task.id == task_id, Task.user_id == user_id).values(updated_at=func.now(), **values)
        self.db.execute(stmt)

    def mark_running(self, user_id: UUID, task_id: UUID) -> None:
        self._update(user_id, task_id, status=TaskStatus.RUNNING, attempts=Task.attempts + 1)

    def mark_retrying(self, user_id: UUID, task_id: UUID, error: str) -> None:
        self._update(user_id, task_id, status=TaskStatus.QUEUED, error=error)

    def mark_done(self, user_id: UUID, task_id: UUID) -> None:
        self._update(user_id, task_id, status=TaskStatus.DONE, error=None)

    def mark_failed(self, user_id: UUID, task_id: UUID, error: str) -> None:
        self._update(user_id, task_id, status=TaskStatus.FAILED, error=error)
