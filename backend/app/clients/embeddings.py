"""Local Sentence Transformers embeddings; no network call after the first model download."""

from functools import lru_cache


class Embedder:
    def __init__(self, model_name: str):
        # Imported lazily: torch is slow to load and the API only needs it for chat.
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # Normalized vectors make cosine similarity a plain dot product.
        return self._model.encode(texts, batch_size=32, normalize_embeddings=True).tolist()


@lru_cache
def get_embedder() -> Embedder:
    from app.config import get_settings

    return Embedder(get_settings().embedding_model)
