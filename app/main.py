"""
app/main.py
────────────
FastAPI application factory.

Using the lifespan context manager (instead of deprecated @app.on_event)
to manage startup and shutdown tasks:
  • Startup:  configure logging, warm up the embedding model, verify DB
  • Shutdown: drain the connection pool

Keep this file thin — business logic lives in services/, not here.
"""
from dotenv import load_dotenv
load_dotenv() 


from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.session import close_db, get_raw_conn
from app.services.embedding import warm_up_embedding_model


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifecycle.

    FastAPI calls the code before `yield` on startup,
    and the code after `yield` on shutdown.
    """
    settings = get_settings()

    # ── Startup ───────────────────────────────────────────────────────────────
    configure_logging()
    logger = get_logger("rerush.startup")

    logger.info(
        "application_starting",
        env=settings.app_env,
        version=settings.app_version,
    )

    # Pre-load the embedding model so the first request is fast
    await warm_up_embedding_model()

    # Verify database connectivity
    try:
        async with get_raw_conn() as conn:
            await conn.execute("SELECT 1")
        logger.info("database_connection_verified")
    except Exception as exc:
        logger.error("database_connection_failed", error=str(exc))
        # Don't abort startup — the DB may become available shortly

    logger.info("application_ready", host=settings.host, port=settings.port)

    yield  # ← application is running

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("application_shutting_down")
    await close_db()
    logger.info("application_shutdown_complete")


def create_app() -> FastAPI:
    """Application factory — returns a configured FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title="ReRush API",
        description=(
            "Semantic episode recommender for sitcoms. "
            "Find episodes by describing what you remember about them."
        ),
        version=settings.app_version,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Tighten `allow_origins` for production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global exception handler ──────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger = get_logger("rerush.exceptions")
        logger.error(
            "unhandled_exception",
            path=str(request.url),
            method=request.method,
            error=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred."},
        )

    # ── Routes ────────────────────────────────────────────────────────────────
    app.include_router(api_router)

    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {"name": "ReRush API", "version": settings.app_version, "docs": "/docs"}

    return app


# Module-level app instance (used by uvicorn)
app = create_app()
