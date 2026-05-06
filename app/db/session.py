"""
app/db/session.py
──────────────────
Async database engine and session factory.

We use SQLAlchemy's async engine over asyncpg so we get:
  • A proper connection pool
  • Type-safe query building (optional)
  • Easy migration path to raw SQL when needed (for pgvector queries)

The raw asyncpg connection is exposed via `get_raw_conn()` for pgvector
similarity searches, which benefit from PostgreSQL's native array syntax.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return the singleton async engine (create if needed)."""
    global _engine  # noqa: PLW0603
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url_str,
            # Pool settings — tune for your Supabase plan
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,   # Recycle connections every 30 min
            pool_pre_ping=True,  # Validate connections before use
            echo=not settings.is_production,  # Log SQL in dev
        )
        logger.info("database_engine_created", url=settings.database_url_str.split("@")[-1])
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the singleton session factory."""
    global _session_factory  # noqa: PLW0603
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,  # Keep attributes accessible after commit
            autoflush=False,
        )
    return _session_factory


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager that yields a session and handles commit/rollback.

    Usage:
        async with get_db_session() as session:
            result = await session.execute(...)
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_raw_conn() -> AsyncGenerator[AsyncConnection, None]:
    """
    Yield a raw SQLAlchemy async connection.
    Used for pgvector similarity queries that require casting to vector type.

    Usage:
        async with get_raw_conn() as conn:
            result = await conn.execute(text("SELECT ..."), {"embedding": ...})
    """
    engine = get_engine()
    async with engine.connect() as conn:
        yield conn


async def close_db() -> None:
    """Dispose the engine pool. Call on application shutdown."""
    global _engine  # noqa: PLW0603
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        logger.info("database_engine_closed")


# ── FastAPI dependency ────────────────────────────────────────────────────────

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency. Inject with:
        session: AsyncSession = Depends(get_session)
    """
    async with get_db_session() as session:
        yield session
