"""
app/api/v1/router.py
──────────────────────
Central router for API version 1.
Add new endpoint modules here as the API grows.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.search import router as search_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(search_router, tags=["search"])
