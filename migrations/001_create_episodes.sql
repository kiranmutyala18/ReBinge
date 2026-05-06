-- migrations/001_create_episodes.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Run this in Supabase SQL Editor or via psql before starting the application.
-- Supabase already ships pgvector, so no separate extension install needed.
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. Enable pgvector extension (idempotent)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Episodes table
CREATE TABLE IF NOT EXISTS episodes (
    id              BIGSERIAL   PRIMARY KEY,

    -- TVmaze identifiers
    tvmaze_show_id  INTEGER     NOT NULL,
    tvmaze_ep_id    INTEGER     NOT NULL UNIQUE,

    -- Show metadata
    show_name       TEXT        NOT NULL,
    show_genres     TEXT[]      NOT NULL DEFAULT '{}',

    -- Episode metadata
    season          SMALLINT    NOT NULL CHECK (season > 0),
    episode         SMALLINT    NOT NULL CHECK (episode > 0),
    title           TEXT        NOT NULL,
    airdate         DATE,
    runtime         SMALLINT,           -- minutes
    rating          NUMERIC(3,1),       -- 0.0 – 10.0

    -- Content used to build the embedding
    summary         TEXT,
    summary_plain   TEXT,               -- HTML-stripped version of summary
    image_url       TEXT,

    -- pgvector embedding (dimension must match EMBEDDING_DIMENSION in .env)
    embedding       VECTOR(384),

    -- Housekeeping
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Trigram-based text search on title (for keyword fallback)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_episodes_title_trgm
    ON episodes USING GIN (title gin_trgm_ops);

-- 4. Fast lookup by show
CREATE INDEX IF NOT EXISTS idx_episodes_show_id
    ON episodes (tvmaze_show_id, season, episode);

-- 5. IVFFlat index for approximate nearest-neighbour search on embeddings.
--    probes=10 is a good default; increase for better recall at the cost of speed.
--    Rebuild this index after bulk inserts (REINDEX INDEX idx_episodes_embedding).
CREATE INDEX IF NOT EXISTS idx_episodes_embedding
    ON episodes USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- 6. Auto-update updated_at
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_episodes_updated_at ON episodes;
CREATE TRIGGER trg_episodes_updated_at
    BEFORE UPDATE ON episodes
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 7. Helper view: episodes with formatted season/episode label
CREATE OR REPLACE VIEW episode_summary AS
SELECT
    id,
    show_name,
    season,
    episode,
    'S' || LPAD(season::TEXT, 2, '0') || 'E' || LPAD(episode::TEXT, 2, '0') AS se_code,
    title,
    airdate,
    runtime,
    rating,
    summary_plain,
    image_url
FROM episodes;
