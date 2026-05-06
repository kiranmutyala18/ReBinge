"""
tests/unit/test_embedding.py
─────────────────────────────
Unit tests for the embedding service.

We mock the SentenceTransformer to avoid loading the model in CI.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.services.embedding import EmbeddingService


class TestEmbeddingService:
    """Tests for EmbeddingService."""

    @pytest.fixture
    def mock_model(self):
        """Return a mock SentenceTransformer that produces random 384-d embeddings."""
        model = MagicMock()
        model.encode.return_value = np.random.rand(2, 384).astype(np.float32)
        return model

    def test_encode_sync_returns_correct_shape(self, mock_model):
        svc = EmbeddingService()
        svc._model = mock_model

        mock_model.encode.return_value = np.random.rand(3, 384).astype(np.float32)

        result = svc.encode_sync(["text one", "text two", "text three"])

        assert len(result) == 3
        assert all(len(emb) == 384 for emb in result)

    def test_encode_sync_calls_with_normalize(self, mock_model):
        svc = EmbeddingService()
        svc._model = mock_model

        mock_model.encode.return_value = np.random.rand(1, 384).astype(np.float32)

        svc.encode_sync(["hello"])

        call_kwargs = mock_model.encode.call_args.kwargs
        assert call_kwargs.get("normalize_embeddings") is True

    @pytest.mark.asyncio
    async def test_encode_one_returns_flat_list(self, mock_model):
        svc = EmbeddingService()
        svc._model = mock_model

        mock_model.encode.return_value = np.random.rand(1, 384).astype(np.float32)

        result = await svc.encode_one("single text")

        assert isinstance(result, list)
        assert len(result) == 384

    def test_dimension_mismatch_raises(self):
        svc = EmbeddingService()
        svc._dimension = 768  # Wrong dimension for the model

        bad_model = MagicMock()
        bad_model.encode.return_value = np.random.rand(1, 384).astype(np.float32)

        with pytest.raises(ValueError, match="384"):
            svc._load_model.__wrapped__(svc) if hasattr(svc._load_model, "__wrapped__") else None
            # Simulate model returning 384 when we expect 768
            svc._model = None
            with patch("sentence_transformers.SentenceTransformer", return_value=bad_model):
                svc._load_model()


# ── Utility function tests ────────────────────────────────────────────────────

from scripts.ingest_tvmaze import strip_html  # noqa: E402


class TestStripHtml:
    def test_strips_paragraph_tags(self):
        result = strip_html("<p>Hello <b>world</b>.</p>")
        assert result == "Hello world."

    def test_collapses_whitespace(self):
        result = strip_html("<p>  Too   many   spaces  </p>")
        assert result == "Too many spaces"

    def test_handles_none(self):
        assert strip_html(None) is None

    def test_handles_empty_string(self):
        assert strip_html("") is None

    def test_handles_plain_text(self):
        assert strip_html("plain text") == "plain text"
