from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, Db
from app.repositories import TaskRepo
from app.schemas.task import TaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: UUID, user_id: CurrentUser, db: Db) -> TaskOut:
    return TaskOut.model_validate(TaskRepo(db).get(user_id, task_id))
