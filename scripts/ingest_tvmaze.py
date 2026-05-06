"""
scripts/ingest_tvmaze.py
─────────────────────────
TVmaze data ingestion script.

Usage:
    python -m scripts.ingest_tvmaze --show-id 66  # Seinfeld
    python -m scripts.ingest_tvmaze --show-id 112 # Friends
    python -m scripts.ingest_tvmaze --show-id 66 --embed  # Ingest + embed in one pass

What it does:
  1. Fetches show metadata and all episodes from TVmaze's free public API
  2. Strips HTML from summaries (TVmaze returns <p> tags in summaries)
  3. Upserts episodes into the `episodes` table (idempotent — safe to re-run)
  4. Optionally computes and stores embeddings for all new/updated episodes

TVmaze API docs: https://www.tvmaze.com/api
Rate limit: ~20 requests/second (we use 0.2s delay = 5/s to be polite)
"""

import asyncio
import re
import time
from typing import Any

import httpx
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.session import close_db, get_db_session
from app.schemas.episode import EpisodeCreate
from app.services.search import embed_episodes_batch

# ── Bootstrap ─────────────────────────────────────────────────────────────────
configure_logging()
logger = get_logger("rerush.ingest")
console = Console()
app = typer.Typer(help="ReRush TVmaze ingestion CLI")
settings = get_settings()


# ── HTML stripping ────────────────────────────────────────────────────────────

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def strip_html(html: str | None) -> str | None:
    """Remove HTML tags and collapse whitespace."""
    if not html:
        return None
    text = _HTML_TAG_RE.sub(" ", html)
    return _WHITESPACE_RE.sub(" ", text).strip() or None


# ── TVmaze API client ─────────────────────────────────────────────────────────

class TVmazeClient:
    """
    Thin async wrapper around the TVmaze REST API.
    Uses tenacity for automatic retry on transient failures.
    """

    BASE_URL = str(settings.tvmaze_base_url).rstrip("/")

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client
        self._delay = settings.tvmaze_rate_limit_delay

    async def _get(self, path: str) -> Any:
        """GET with exponential-backoff retry on 429 / 5xx."""
        url = f"{self.BASE_URL}{path}"
        await asyncio.sleep(self._delay)  # Polite rate limiting
        response = await self._client.get(url, timeout=30.0)
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_show(self, show_id: int) -> dict:
        """Fetch show metadata including genres."""
        return await self._get(f"/shows/{show_id}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_episodes(self, show_id: int) -> list[dict]:
        """
        Fetch all episodes for a show in a single request.
        TVmaze returns episodes sorted by airdate.
        """
        return await self._get(f"/shows/{show_id}/episodes")


# ── Transformation ────────────────────────────────────────────────────────────

def tvmaze_episode_to_schema(
    ep: dict,
    show_id: int,
    show_name: str,
    show_genres: list[str],
) -> EpisodeCreate | None:
    """
    Map a raw TVmaze episode dict to our EpisodeCreate schema.
    Returns None if the episode is missing required fields.
    """
    # TVmaze uses null for unaired specials; skip them
    if ep.get("season") is None or ep.get("number") is None:
        return None

    summary_raw = ep.get("summary") or ep.get("summery")  # TVmaze typo in older records
    summary_plain = strip_html(summary_raw)
    image_url = None
    if ep.get("image"):
        image_url = ep["image"].get("medium") or ep["image"].get("original")

    return EpisodeCreate(
        tvmaze_show_id=show_id,
        tvmaze_ep_id=ep["id"],
        show_name=show_name,
        show_genres=show_genres,
        season=ep["season"],
        episode=ep["number"],
        title=ep.get("name") or f"Episode {ep['number']}",
        airdate=ep.get("airdate") or None,
        runtime=ep.get("runtime"),
        rating=ep.get("rating", {}).get("average") if ep.get("rating") else None,
        summary=summary_raw,
        summary_plain=summary_plain,
        image_url=image_url,
    )


# ── Database upsert ───────────────────────────────────────────────────────────

from sqlalchemy import text  # noqa: E402 — placed here to keep imports grouped above


async def upsert_episodes(episodes: list[EpisodeCreate]) -> list[int]:
    """
    Upsert a batch of episodes and return the list of inserted/updated IDs.

    Uses ON CONFLICT DO UPDATE so the script is idempotent — re-running it
    will refresh metadata (title, rating, summary) without duplicating rows.
    """
    if not episodes:
        return []

    upsert_sql = text("""
        INSERT INTO episodes (
            tvmaze_show_id, tvmaze_ep_id, show_name, show_genres,
            season, episode, title, airdate, runtime, rating,
            summary, summary_plain, image_url
        )
        SELECT
            d.tvmaze_show_id::int,
            d.tvmaze_ep_id::int,
            d.show_name,
            d.show_genres::text[],
            d.season::smallint,
            d.episode::smallint,
            d.title,
            d.airdate::date,
            d.runtime::smallint,
            d.rating::numeric,
            d.summary,
            d.summary_plain,
            d.image_url
        FROM UNNEST(
            CAST(:show_ids AS int[]),
            CAST(:ep_ids AS int[]),
            CAST(:show_names AS text[]),
            CAST(:genres AS text[]),
            CAST(:seasons AS smallint[]),
            CAST(:episodes_nums AS smallint[]),
            CAST(:titles AS text[]),
            CAST(:airdates AS date[]),
            CAST(:runtimes AS smallint[]),
            CAST(:ratings AS numeric[]),
            CAST(:summaries AS text[]),
            CAST(:summaries_plain AS text[]),
            CAST(:image_urls AS text[])
        ) AS d(
            tvmaze_show_id, tvmaze_ep_id, show_name, show_genres,
            season, episode, title, airdate, runtime, rating,
            summary, summary_plain, image_url
        )
        ON CONFLICT (tvmaze_ep_id) DO UPDATE SET
            title          = EXCLUDED.title,
            rating         = EXCLUDED.rating,
            summary        = EXCLUDED.summary,
            summary_plain  = EXCLUDED.summary_plain,
            image_url      = EXCLUDED.image_url,
            updated_at     = now()
        RETURNING id
    """)

    def _val(ep: EpisodeCreate, attr: str) -> Any:
        v = getattr(ep, attr)
        return str(v) if v is not None else None

    params = {
        "show_ids":       [ep.tvmaze_show_id for ep in episodes],
        "ep_ids":         [ep.tvmaze_ep_id   for ep in episodes],
        "show_names":     [ep.show_name      for ep in episodes],
        "genres": [[ep.show_genres] if isinstance(ep.show_genres, str) else ep.show_genres for ep in episodes],
        "seasons":        [ep.season         for ep in episodes],
        "episodes_nums":  [ep.episode        for ep in episodes],
        "titles":         [ep.title          for ep in episodes],
        "airdates":       [ep.airdate        for ep in episodes],
        "runtimes":       [ep.runtime        for ep in episodes],
        "ratings":        [_val(ep, "rating") for ep in episodes],
        "summaries":      [ep.summary        for ep in episodes],
        "summaries_plain":[ep.summary_plain  for ep in episodes],
        "image_urls":     [ep.image_url      for ep in episodes],
    }

    async with get_db_session() as session:
        result = await session.execute(upsert_sql, params)
        rows = result.fetchall()

    return [row[0] for row in rows]


# ── CLI commands ──────────────────────────────────────────────────────────────

@app.command()
def ingest(
    show_id: int = typer.Argument(..., help="TVmaze show ID (e.g. 66 for Seinfeld)"),
    embed: bool = typer.Option(False, "--embed", help="Also compute embeddings after ingesting"),
    batch_size: int = typer.Option(50, "--batch-size", help="Embedding batch size"),
) -> None:
    """
    Ingest all episodes for a show from TVmaze into the database.

    Run without --embed to import metadata only (fast).
    Run with --embed to import metadata AND compute embeddings (slower, GPU recommended).
    """
    asyncio.run(_ingest(show_id, embed, batch_size))


async def _ingest(show_id: int, embed: bool, batch_size: int) -> None:
    start = time.perf_counter()

    async with httpx.AsyncClient(headers={"User-Agent": "ReRush/0.1 (https://github.com/you/rerush)"}) as http:
        client = TVmazeClient(http)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:

            # ── Fetch show metadata ───────────────────────────────────────────
            task = progress.add_task("Fetching show metadata…", total=None)
            show_data = await client.get_show(show_id)
            show_name   = show_data["name"]
            show_genres = show_data.get("genres") or []
            progress.update(task, completed=1, total=1, description=f"Show: [bold]{show_name}[/bold]")
            logger.info("show_fetched", show_id=show_id, show_name=show_name, genres=show_genres)

            # ── Fetch all episodes ────────────────────────────────────────────
            task = progress.add_task("Fetching episodes…", total=None)
            raw_episodes = await client.get_episodes(show_id)
            progress.update(task, completed=1, total=1, description=f"Fetched {len(raw_episodes)} episodes")

            # ── Transform ─────────────────────────────────────────────────────
            episodes: list[EpisodeCreate] = []
            for ep in raw_episodes:
                schema = tvmaze_episode_to_schema(ep, show_id, show_name, show_genres)
                if schema:
                    episodes.append(schema)

            skipped = len(raw_episodes) - len(episodes)
            if skipped:
                logger.warning("episodes_skipped_invalid", count=skipped)

            # ── Upsert ────────────────────────────────────────────────────────
            task = progress.add_task("Upserting episodes…", total=len(episodes))
            inserted_ids = await upsert_episodes(episodes)
            progress.update(task, completed=len(episodes), description=f"Upserted {len(inserted_ids)} episodes")

            # ── Embed (optional) ──────────────────────────────────────────────
            if embed and inserted_ids:
                task = progress.add_task("Computing embeddings…", total=len(inserted_ids))
                batches = [inserted_ids[i:i + batch_size] for i in range(0, len(inserted_ids), batch_size)]

                async with get_db_session() as session:
                    for batch in batches:
                        await embed_episodes_batch(batch, session)
                        progress.advance(task, len(batch))

    elapsed = time.perf_counter() - start
    console.print(
        f"\n✅  [green]Done![/green] Ingested [bold]{len(inserted_ids)}[/bold] episodes "
        f"from [bold]{show_name}[/bold] in {elapsed:.1f}s"
    )
    if not embed:
        console.print("   Run with [bold]--embed[/bold] to compute semantic embeddings.")

    await close_db()


if __name__ == "__main__":
    app()
