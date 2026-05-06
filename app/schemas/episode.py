"""
app/schemas/episode.py
───────────────────────
Pydantic v2 schemas for API request validation and response serialisation.

We keep these separate from the SQLAlchemy models so the API contract
can evolve independently of the database schema.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


# ── Shared base ───────────────────────────────────────────────────────────────

class EpisodeBase(BaseModel):
    """Fields shared by create and response schemas."""
    model_config = ConfigDict(from_attributes=True)  # Allow ORM → schema conversion

    tvmaze_show_id: int = Field(..., gt=0, description="TVmaze show identifier")
    tvmaze_ep_id:   int = Field(..., gt=0, description="TVmaze episode identifier")
    show_name:      str = Field(..., min_length=1, max_length=255)
    show_genres:    list[str] = Field(default_factory=list)
    season:         int = Field(..., gt=0, le=999)
    episode:        int = Field(..., gt=0, le=999)
    title:          str = Field(..., min_length=1, max_length=512)
    airdate:        date | None = None
    runtime:        int | None = Field(None, gt=0, le=600)
    rating:         Decimal | None = Field(None, ge=0, le=10)
    summary:        str | None = None
    summary_plain:  str | None = None
    image_url:      str | None = None


# ── Create ────────────────────────────────────────────────────────────────────

class EpisodeCreate(EpisodeBase):
    """
    Schema for bulk-inserting episodes (used by the ingestion script).
    The embedding is optional at creation time — the embedding service
    fills it in during a subsequent pass.
    """
    embedding: list[float] | None = None

    @field_validator("embedding")
    @classmethod
    def validate_embedding_dim(cls, v: list[float] | None) -> list[float] | None:
        if v is not None and len(v) != 384:
            raise ValueError(f"Embedding must have 384 dimensions, got {len(v)}")
        return v


# ── Response ──────────────────────────────────────────────────────────────────

class EpisodeResponse(EpisodeBase):
    """Full episode representation returned by the API."""
    id:         int
    se_code:    str = Field(..., description="Formatted season/episode, e.g. S01E03")
    created_at: datetime
    updated_at: datetime

    # Never expose raw embeddings to API consumers
    model_config = ConfigDict(from_attributes=True)


# ── Search ────────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    """
    Payload for the semantic search endpoint.

    The `query` field is free-form natural language — e.g.
    "the one where they get stuck in a room together"
    or "romantic subplot with a misunderstanding at the airport"
    """
    query: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Natural-language description of the episode you're looking for",
        examples=[
            "the one where everyone argues at Thanksgiving dinner",
            "episode about a road trip gone wrong",
        ],
    )
    limit: int = Field(
        10,
        ge=1,
        le=50,
        description="Maximum number of results to return",
    )
    show_name: str | None = Field(
        None,
        description="Optionally restrict search to a specific show",
    )
    min_similarity: float = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity threshold (0 = anything, 1 = exact)",
    )


class SearchResultItem(BaseModel):
    """A single episode result enriched with its similarity score."""
    model_config = ConfigDict(from_attributes=True)

    id:            int
    show_name:     str
    se_code:       str
    title:         str
    summary_plain: str | None
    airdate:       date | None
    rating:        Decimal | None
    image_url:     str | None
    similarity:    float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score")


class SearchResponse(BaseModel):
    """Paginated search results."""
    query:   str
    count:   int
    results: list[SearchResultItem]


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status:  str
    version: str
    model:   str
