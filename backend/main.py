"""
main.py — FastAPI application entry point for the Unitwise API.

Run from the project root:
    uvicorn backend.main:app --reload

Or from inside the backend/ directory:
    uvicorn main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import router
from app.config import settings
from app.config.limiter import limiter
from app.search.searcher import init_vector_store

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — pre-load heavy resources at startup, release at shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("Unitwise startup: warming up vector store and embedding model…")
    try:
        # This blocks briefly (~5–20s) but runs before any request is served,
        # so the first user never pays the cold-start penalty.
        import asyncio
        await asyncio.to_thread(init_vector_store)
        logger.info("Vector store ready.")
    except Exception:
        logger.exception("Failed to initialise vector store at startup.")
        # Continue anyway — searcher will retry lazily on first request.
    yield
    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("Unitwise shutdown.")


# ---------------------------------------------------------------------------
# Application instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Unitwise API",
    version="2.0",
    description="Backend API for the Unitwise academic assistant.",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Rate-limit middleware & error handler
# Limiter is defined in app/config/limiter.py and shared with routes.py.
# ---------------------------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# CORS — origins loaded from the CORS_ORIGINS environment variable.
# Set CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000 in
# your HF Spaces secrets (and local .env).
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Mount the versioned router
# ---------------------------------------------------------------------------
app.include_router(router, prefix="/api/v1")
