# ReBinge — Semantic Episode Recommender

Find sitcom episodes by describing what you remember about them.

> "the one where they get trapped in an elevator"
> "romantic subplot at a high school reunion"

Powered by **FastAPI** + **Sentence Transformers** + **Supabase pgvector**.

---

## Architecture

```
User query
    ↓
FastAPI  →  EmbeddingService (all-MiniLM-L6-v2)
                ↓ 384-dim vector
            Supabase PostgreSQL + pgvector
                ↓ cosine similarity (<=>)
            Ranked episode results
```

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- A [Supabase](https://supabase.com) project (free tier works)

### 2. Install

```bash
git clone https://github.com/you/rerush
cd rerush
make install
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env — fill in SUPABASE_URL, SUPABASE_ANON_KEY,
# SUPABASE_SERVICE_ROLE_KEY, and DATABASE_URL
```

### 4. Apply database migration

Open your Supabase project → SQL Editor, paste and run:
```
migrations/001_create_episodes.sql
```

This creates the `episodes` table with a pgvector index.

### 5. Ingest episodes

```bash
# Seinfeld (TVmaze show ID 66)
make ingest-seinfeld

# Friends (TVmaze show ID 112)
make ingest-friends

# Any show by ID
python -m scripts.ingest_tvmaze 526 --embed   # The Office
```

### 6. Start the API

```bash
make dev
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

---

## API

### `POST /api/v1/search`

```json
{
  "query": "the one where nobody can agree on what to watch",
  "limit": 5,
  "show_name": "Seinfeld",
  "min_similarity": 0.4
}
```

**Response:**
```json
{
  "query": "...",
  "count": 5,
  "results": [
    {
      "id": 42,
      "show_name": "Seinfeld",
      "se_code": "S04E11",
      "title": "The Contest",
      "summary_plain": "...",
      "similarity": 0.87
    }
  ]
}
```

### `GET /api/v1/health`

```json
{ "status": "ok", "version": "0.1.0", "model": "all-MiniLM-L6-v2" }
```

---

## Development

```bash
make test        # Run tests
make lint        # Ruff + mypy
make format      # Auto-fix
```

---

## TVmaze Show IDs (Popular Sitcoms)

| Show | ID |
|------|-----|
| Seinfeld | 66 |
| Friends | 112 |
| The Office (US) | 526 |
| Parks and Recreation | 1396 |
| Brooklyn Nine-Nine | 49 |
| It's Always Sunny in Philadelphia | 74 |
| Arrested Development | 3969 |
| 30 Rock | 150 |
| Community | 112 |
| Curb Your Enthusiasm | 310 |

Find any show: `https://api.tvmaze.com/search/shows?q=YOUR+SHOW+NAME`

---

## Embedding Notes

- **Model**: `all-MiniLM-L6-v2` — 384 dimensions, ~80 MB, fast CPU inference
- **Input text**: `episode_title + " " + summary_plain`
- **Similarity metric**: cosine similarity via pgvector `<=>` operator
- **Index**: IVFFlat with `lists=100` (rebuild after bulk inserts: `REINDEX INDEX idx_episodes_embedding`)
- **Threshold**: Default `0.3` — adjust `SIMILARITY_THRESHOLD` in `.env`
