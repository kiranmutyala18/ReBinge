.PHONY: install dev test lint format migrate ingest help

# ── Setup ─────────────────────────────────────────────────────────────────────
install:
	pip install -e ".[dev]"
	cp -n .env.example .env || true
	@echo "✅  Installed. Edit .env with your Supabase credentials."

# ── Development server ────────────────────────────────────────────────────────
dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# ── Database migrations ───────────────────────────────────────────────────────
migrate:
	@echo "Apply migration via Supabase SQL Editor or psql:"
	@echo "  psql \$$DATABASE_URL < migrations/001_create_episodes.sql"

# ── Ingestion ─────────────────────────────────────────────────────────────────
ingest-seinfeld:
	python -m scripts.ingest_tvmaze 66 --embed

ingest-friends:
	python -m scripts.ingest_tvmaze 112 --embed

ingest-office:
	python -m scripts.ingest_tvmaze 526 --embed

# ── Tests ─────────────────────────────────────────────────────────────────────
test:
	pytest -v

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

# ── Linting ───────────────────────────────────────────────────────────────────
lint:
	ruff check .
	mypy app/

format:
	ruff format .
	ruff check --fix .

# ── Help ──────────────────────────────────────────────────────────────────────
help:
	@echo "ReRush — available commands:"
	@echo "  make install           Install dependencies"
	@echo "  make dev               Start dev server with hot reload"
	@echo "  make migrate           Print migration instructions"
	@echo "  make ingest-seinfeld   Ingest Seinfeld episodes"
	@echo "  make ingest-friends    Ingest Friends episodes"
	@echo "  make ingest-office     Ingest The Office episodes"
	@echo "  make test              Run all tests"
	@echo "  make lint              Run ruff + mypy"
	@echo "  make format            Auto-fix lint issues"
