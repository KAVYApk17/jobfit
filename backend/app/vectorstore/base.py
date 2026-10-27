from dataclasses import dataclass
from typing import Literal, Protocol
from uuid import UUID

SourceType = Literal["resume", "jd"]


@dataclass(frozen=True)
class Chunk:
    source_type: SourceType
    source_id: UUID
    position: int
    text: str
    embedding: list[float]


@dataclass(frozen=True)
class ScoredChunk:
    id: UUID
    source_type: SourceType
    source_id: UUID
    position: int
    text: str
    score: float  # cosine similarity, higher is closer


class VectorStore(Protocol):
    def add(self, user_id: UUID, chunks: list[Chunk]) -> None: ...

    def search(
        self,
        user_id: UUID,
        query_vec: list[float],
        source_type: SourceType | None = None,
        k: int = 5,
        source_id: UUID | None = None,
    ) -> list[ScoredChunk]: ...

    def delete_source(self, user_id: UUID, source_id: UUID) -> None: ...
