from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Chunk as ChunkRow
from app.vectorstore.base import Chunk, ScoredChunk, SourceType


class PgVectorStore:
    """Vector search in SQL, always filtered by user_id."""

    def __init__(self, db: Session):
        self.db = db

    def add(self, user_id: UUID, chunks: list[Chunk]) -> None:
        self.db.add_all(
            ChunkRow(
                user_id=user_id,
                source_type=c.source_type,
                source_id=c.source_id,
                position=c.position,
                text=c.text,
                embedding=c.embedding,
            )
            for c in chunks
        )
        self.db.flush()

    def search(
        self,
        user_id: UUID,
        query_vec: list[float],
        source_type: SourceType | None = None,
        k: int = 5,
        source_id: UUID | None = None,
    ) -> list[ScoredChunk]:
        distance = ChunkRow.embedding.cosine_distance(query_vec)
        stmt = select(ChunkRow, distance.label("distance")).where(ChunkRow.user_id == user_id)
        if source_type is not None:
            stmt = stmt.where(ChunkRow.source_type == source_type)
        if source_id is not None:
            stmt = stmt.where(ChunkRow.source_id == source_id)
        stmt = stmt.order_by(distance).limit(k)
        return [
            ScoredChunk(
                id=row.id,
                source_type=row.source_type,
                source_id=row.source_id,
                position=row.position,
                text=row.text,
                score=1.0 - dist,
            )
            for row, dist in self.db.execute(stmt)
        ]

    def delete_source(self, user_id: UUID, source_id: UUID) -> None:
        self.db.execute(delete(ChunkRow).where(ChunkRow.user_id == user_id, ChunkRow.source_id == source_id))
