"""
tests/integration/test_search.py
──────────────────────────────────
Integration tests for the /api/v1/search endpoint.

These tests mock the embedding service and database session so they
run without a real Supabase instance — useful in CI.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.db.session import get_session
from app.schemas.episode import SearchResponse, SearchResultItem


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_search_results() -> list[SearchResultItem]:
    return [
        SearchResultItem(
            id=1,
            show_name="Seinfeld",
            se_code="S04E11",
            title="The Contest",
            summary_plain="The gang makes a bet about self-restraint.",
            airdate=None,
            rating=9.5,
            image_url=None,
            similarity=0.92,
        ),
    ]


@pytest.fixture
def client():
    return TestClient(app)


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestSearchEndpoint:
    def test_search_returns_results(self, client, mock_search_results):
        with (
            patch("app.api.v1.endpoints.search.semantic_search", new_callable=AsyncMock) as mock_search,
        ):
            mock_search.return_value = SearchResponse(
                query="self restraint bet episode",
                count=1,
                results=mock_search_results,
            )
            # Override DB dependency
            app.dependency_overrides[get_session] = lambda: AsyncMock()

            response = client.post(
                "/api/v1/search",
                json={"query": "self restraint bet episode"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["show_name"] == "Seinfeld"
        assert data["results"][0]["similarity"] == 0.92

        app.dependency_overrides.clear()

    def test_search_validates_short_query(self, client):
        response = client.post("/api/v1/search", json={"query": "hi"})
        assert response.status_code == 422

    def test_search_validates_limit_range(self, client):
        response = client.post(
            "/api/v1/search",
            json={"query": "episode about a contest", "limit": 999},
        )
        assert response.status_code == 422

    def test_health_endpoint(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "model" in data

    def test_root_returns_metadata(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "name" in response.json()
