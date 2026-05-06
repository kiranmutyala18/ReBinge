"""
app/models/episode.py
──────────────────────
SQLAlchemy ORM model for the `episodes` table.

pgvector's Vector type is mapped via the `pgvector.sqlalchemy` integration,
which handles the Python list ↔ PostgreSQL vector casting transparently.
"""

from datetime import date, datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    DATE,
    NUMERIC,
    TEXT,
    TIMESTAMP,
    CheckConstraint,
    SmallInteger,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base — all models inherit from this."""
    pass


class Episode(Base):
    """
    Represents a single TV episode, enriched with a semantic embedding.

    The `embedding` column stores a 384-dimensional vector produced by
    all-MiniLM-L6-v2 over a concatenation of the episode's title + summary.
    pgvector uses this for cosine-similarity nearest-neighbour search.
    """

    __tablename__ = "episodes"
    __table_args__ = (
        UniqueConstraint("tvmaze_ep_id", name="uq_episodes_tvmaze_ep_id"),
        CheckConstraint("season > 0",  name="chk_episodes_season_positive"),
        CheckConstraint("episode > 0", name="chk_episodes_episode_positive"),
    )

    # ── Primary key ───────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ── TVmaze identifiers ────────────────────────────────────────────────────
    tvmaze_show_id: Mapped[int] = mapped_column(nullable=False, index=True)
    tvmaze_ep_id:   Mapped[int] = mapped_column(nullable=False, unique=True)

    # ── Show metadata ─────────────────────────────────────────────────────────
    show_name:   Mapped[str]       = mapped_column(TEXT, nullable=False)
    show_genres: Mapped[list[str]] = mapped_column(ARRAY(TEXT), nullable=False, default=list)

    # ── Episode metadata ──────────────────────────────────────────────────────
    season:  Mapped[int]          = mapped_column(SmallInteger, nullable=False)
    episode: Mapped[int]          = mapped_column(SmallInteger, nullable=False)
    title:   Mapped[str]          = mapped_column(TEXT, nullable=False)
    airdate: Mapped[date | None]  = mapped_column(DATE)
    runtime: Mapped[int | None]   = mapped_column(SmallInteger)
    rating:  Mapped[Decimal | None] = mapped_column(NUMERIC(3, 1))

    # ── Content ───────────────────────────────────────────────────────────────
    summary:       Mapped[str | None] = mapped_column(TEXT)
    summary_plain: Mapped[str | None] = mapped_column(TEXT)  # HTML-stripped
    image_url:     Mapped[str | None] = mapped_column(TEXT)

    # ── Embedding (pgvector) ─────────────────────────────────────────────────
    # Dimension must match EMBEDDING_DIMENSION in .env (default 384)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384))

    # ── Housekeeping ──────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Episode show={self.show_name!r} "
            f"S{self.season:02d}E{self.episode:02d} "
            f"title={self.title!r}>"
        )

    @property
    def se_code(self) -> str:
        """Return a formatted season/episode code like S01E03."""
        return f"S{self.season:02d}E{self.episode:02d}"

    @property
    def embedding_text(self) -> str:
        """
        The text that gets embedded.
        Concatenating title + summary gives the model richer context.
        """
        parts = [self.title]
        if self.summary_plain:
            parts.append(self.summary_plain)
        return " ".join(parts)
