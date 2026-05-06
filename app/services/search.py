"""
app/services/search.py
───────────────────────
Semantic search over episodes using pgvector cosine similarity.

Query flow:
  1. Embed the user's natural-language query string → 384-d float vector
  2. Issue a pgvector `<=>` (cosine distance) query against the episodes table
  3. Convert raw distance → similarity score (similarity = 1 - distance)
  4. Filter by threshold and return ranked results

Why raw SQL instead of SQLAlchemy ORM?
  pgvector's `<=>` operator works in SQLAlchemy with the pgvector extension,
  but parameterised vector literals (`$1::vector`) are cleaner and faster
  in asyncpg than going through the ORM layer.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.episode import SearchRequest, SearchResponse, SearchResultItem
from app.services.embedding import get_embedding_service

logger = get_logger(__name__)


async def semantic_search(
    request: SearchRequest,
    session: AsyncSession,
) -> SearchResponse:
    """
    Perform semantic similarity search over the episodes table.

    Args:
        request: Validated search request (query text, limit, optional filters).
        session: Active async database session.

    Returns:
        SearchResponse with ranked episodes and their similarity scores.
    """
    settings = get_settings()
    svc = get_embedding_service()

    # ── 1. Embed the query ────────────────────────────────────────────────────
    logger.info("semantic_search_start", query=request.query[:80], limit=request.limit)
    query_embedding: list[float] = await svc.encode_one(request.query)

    # ── 2. Build the SQL query ────────────────────────────────────────────────
    #
    # pgvector's `<=>` is the cosine DISTANCE operator (0 = identical, 2 = opposite).
    # We convert to cosine SIMILARITY: similarity = 1 - distance.
    #
    # The CAST to ::vector is required; asyncpg sends Python lists as TEXT,
    # so PostgreSQL needs an explicit type hint to interpret it as a vector.
    #
    min_similarity = max(request.min_similarity, settings.similarity_threshold)

    where_clauses = ["embedding IS NOT NULL", "(1 - (embedding <=> :embedding::vector)) >= :threshold"]
    params: dict = {
        "embedding": str(query_embedding),  # '[0.1, 0.2, ...]' format pgvector expects
        "threshold": min_similarity,
        "limit": min(request.limit, settings.max_search_limit),
    }

    if request.show_name:
        where_clauses.append("LOWER(show_name) = LOWER(:show_name)")
        params["show_name"] = request.show_name

    where_sql = " AND ".join(where_clauses)

    sql = text(f"""
        SELECT
            id,
            show_name,
            'S' || LPAD(season::TEXT, 2, '0') || 'E' || LPAD(episode::TEXT, 2, '0') AS se_code,
            title,
            summary_plain,
            airdate,
            rating,
            image_url,
            ROUND((1 - (embedding <=> :embedding::vector))::NUMERIC, 4) AS similarity
        FROM episodes
        WHERE {where_sql}
        ORDER BY embedding <=> :embedding::vector
        LIMIT :limit
    """)

    # ── 3. Execute ────────────────────────────────────────────────────────────
    result = await session.execute(sql, params)
    rows = result.mappings().all()

    # ── 4. Map rows → response schema ────────────────────────────────────────
    items = [
        SearchResultItem(
            id=row["id"],
            show_name=row["show_name"],
            se_code=row["se_code"],
            title=row["title"],
            summary_plain=row["summary_plain"],
            airdate=row["airdate"],
            rating=row["rating"],
            image_url=row["image_url"],
            similarity=float(row["similarity"]),
        )
        for row in rows
    ]

    logger.info(
        "semantic_search_complete",
        query=request.query[:80],
        results_count=len(items),
        top_similarity=items[0].similarity if items else None,
    )

    return SearchResponse(query=request.query, count=len(items), results=items)


async def embed_episodes_batch(
    episode_ids: list[int],
    session: AsyncSession,
) -> dict[int, str]:
    """
    Fetch episodes by ID, compute embeddings, and update the database.

    Returns a dict mapping episode_id → status ('ok' | 'skipped' | 'error').

    Used by:
      - The ingestion script (scripts/ingest_tvmaze.py) after inserting raw records
      - A potential background worker for re-embedding on model updates
    """
    svc = get_embedding_service()
    results: dict[int, str] = {}

    if not episode_ids:
        return results

    # Fetch episodes that need embedding
    fetch_sql = text("""
        SELECT id, title, summary_plain
        FROM episodes
        WHERE id = ANY(:ids)
        ORDER BY id
    """)
    rows = (await session.execute(fetch_sql, {"ids": episode_ids})).mappings().all()

    if not rows:
        logger.warning("embed_batch_no_rows_found", ids=episode_ids)
        return {ep_id: "skipped" for ep_id in episode_ids}

    # Compute embeddings
    texts = [f"{row['title']} {row['summary_plain'] or ''}".strip() for row in rows]
    ids   = [row["id"] for row in rows]

    try:
        embeddings = await svc.encode(texts)
    except Exception as exc:
        logger.error("embed_batch_encoding_failed", error=str(exc))
        return {ep_id: "error" for ep_id in episode_ids}

    # Bulk update using unnest for efficiency
    update_sql = text("""
        UPDATE episodes
        SET embedding = data.embedding::vector
        FROM (
            SELECT
                UNNEST(:ids::bigint[])        AS id,
                UNNEST(:embeddings::text[])   AS embedding
        ) AS data
        WHERE episodes.id = data.id
    """)
    await session.execute(
        update_sql,
        {
            "ids": ids,
            "embeddings": [str(emb) for emb in embeddings],
        },
    )
    await session.commit()

    for ep_id in ids:
        results[ep_id] = "ok"

    logger.info("embed_batch_complete", count=len(ids))
    return results
