import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin, user_fk

# all-MiniLM-L6-v2 produces 384-dim vectors; a new embedding model needs a migration.
EMBEDDING_DIM = 384


class Resume(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "resumes"

    user_id: Mapped[uuid.UUID] = user_fk()
    filename: Mapped[str] = mapped_column(String(255))
    raw_text: Mapped[str] = mapped_column(Text)
    parsed: Mapped[dict | None] = mapped_column(JSONB)


class Job(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "jobs"

    user_id: Mapped[uuid.UUID] = user_fk()
    title: Mapped[str] = mapped_column(String(200))
    company: Mapped[str] = mapped_column(String(200), default="")
    jd_text: Mapped[str] = mapped_column(Text)
    parsed: Mapped[dict | None] = mapped_column(JSONB)


class Chunk(IdMixin, Base):
    """source_id points to a resume or a job depending on source_type, so it has no FK."""

    __tablename__ = "chunks"
    __table_args__ = (
        Index("ix_chunks_user_source_type", "user_id", "source_type"),
        Index(
            "ix_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    user_id: Mapped[uuid.UUID] = user_fk()
    source_type: Mapped[str] = mapped_column(String(10))
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    position: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
