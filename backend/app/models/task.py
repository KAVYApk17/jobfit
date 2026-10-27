import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin, user_fk


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class TaskKind(StrEnum):
    PARSE_RESUME = "parse_resume"
    PARSE_JOB = "parse_job"


class Task(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "tasks"

    user_id: Mapped[uuid.UUID] = user_fk()
    kind: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(10), default=TaskStatus.QUEUED)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    result_ref: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    error: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
