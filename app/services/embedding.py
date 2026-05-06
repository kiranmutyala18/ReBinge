"""
app/services/embedding.py
──────────────────────────
Embedding service backed by sentence-transformers.

Design decisions:
  • Singleton model — load once at startup, reuse for every request.
    SentenceTransformer models are ~90 MB in memory; instantiating per-request
    would exhaust RAM and add ~2 s latency on cold start.
  • Batch encoding — the service accepts both single strings and lists,
    enabling efficient bulk embedding during ingestion.
  • Normalised embeddings — we use `normalize_embeddings=True` so cosine
    similarity equals dot product, which is what pgvector's `<=>` operator
    measures. Consistency between ingestion and search is critical.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import overload

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Thread-safe wrapper around a SentenceTransformer model.

    The model is loaded synchronously (SentenceTransformer has no async API),
    so we offload encoding to a thread pool to avoid blocking the event loop.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._model_name = settings.embedding_model
        self._dimension = settings.embedding_dimension
        self._cache_dir = str(settings.embedding_cache_dir)
        self._model: SentenceTransformer | None = None

    def _load_model(self) -> SentenceTransformer:
        """
        Load the model from local cache or download from HuggingFace.
        Called once; subsequent calls return the cached instance.
        """
        if self._model is None:
            logger.info("loading_embedding_model", model=self._model_name)
            self._model = SentenceTransformer(
                self._model_name,
                cache_folder=self._cache_dir,
            )
            # Validate that the model's output dimension matches our config
            test = self._model.encode(["test"], normalize_embeddings=True)
            actual_dim = test.shape[1]
            if actual_dim != self._dimension:
                raise ValueError(
                    f"Model {self._model_name!r} produces {actual_dim}-dim embeddings, "
                    f"but EMBEDDING_DIMENSION={self._dimension} in config. "
                    "Update .env to match."
                )
            logger.info("embedding_model_loaded", model=self._model_name, dimension=actual_dim)
        return self._model

    def encode_sync(self, texts: list[str]) -> list[list[float]]:
        """
        Synchronous encoding. Use inside thread pool for async contexts.

        Returns:
            List of L2-normalised embeddings as plain Python lists.
        """
        model = self._load_model()
        embeddings: np.ndarray = model.encode(
            texts,
            normalize_embeddings=True,  # Required for cosine similarity via dot product
            show_progress_bar=False,
            batch_size=64,              # Tune based on available RAM / GPU VRAM
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    async def encode(self, texts: list[str]) -> list[list[float]]:
        """
        Async encode — offloads CPU-intensive encoding to the default executor
        so it doesn't block the FastAPI event loop.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.encode_sync, texts)

    async def encode_one(self, text: str) -> list[float]:
        """Convenience wrapper for encoding a single string."""
        results = await self.encode([text])
        return results[0]

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """
    Return the singleton EmbeddingService.
    The model is NOT loaded here — it loads lazily on first encode() call
    (or eagerly if you call warm_up() at startup).
    """
    return EmbeddingService()


async def warm_up_embedding_model() -> None:
    """
    Pre-load the model during application startup so the first search
    request doesn't pay the cold-start penalty.
    Call from the FastAPI lifespan handler.
    """
    svc = get_embedding_service()
    logger.info("warming_up_embedding_model")
    await svc.encode(["warm-up"])
    logger.info("embedding_model_ready", model=svc.model_name)
