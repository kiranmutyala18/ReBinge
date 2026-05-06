"""
app/api/v1/endpoints/search.py
────────────────────────────────
Semantic search endpoints.

POST /api/v1/search  — primary semantic similarity search
GET  /api/v1/health  — liveness + model status check
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import get_session
from app.schemas.episode import HealthResponse, SearchRequest, SearchResponse
from app.services.embedding import get_embedding_service
from app.services.search import semantic_search

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Semantic episode search",
    description=(
        "Find episodes semantically similar to a natural-language description. "
        "Results are ranked by cosine similarity between the query embedding "
        "and each episode's pre-computed embedding."
    ),
    responses={
        422: {"description": "Validation error — check query length and limit range"},
        503: {"description": "Embedding model not ready"},
    },
)
async def search_episodes(
    request: SearchRequest,
    session: AsyncSession = Depends(get_session),
) -> SearchResponse:
    """
    Search for episodes matching a natural-language description.

    **Example queries:**
    - "the one where they get trapped in an elevator"
    - "romantic subplot at a high school reunion"
    - "cooking competition episode with a surprise twist"
    """
    try:
        return await semantic_search(request, session)
    except ValueError as exc:
        # Raised by embedding validation (wrong dimension, empty text, etc.)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("search_endpoint_error", error=str(exc), query=request.query[:80])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your search. Please try again.",
        ) from exc


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
    description="Returns application status, version, and embedding model name.",
)
async def health_check() -> HealthResponse:
    """Lightweight liveness probe — does NOT touch the database."""
    settings = get_settings()
    svc = get_embedding_service()
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        model=svc.model_name,
    )
