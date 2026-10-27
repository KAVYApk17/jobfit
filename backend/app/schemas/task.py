from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TaskAccepted(BaseModel):
    task_id: UUID
    status: str


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kind: str
    status: str
    attempts: int
    result_ref: UUID | None
    error: str | None
    created_at: datetime
    updated_at: datetime
