"""
main.py — FastAPI application entry point for the Unitwise API.

Run from the project root:
    uvicorn backend.main:app --reload

Or from inside the backend/ directory:
    uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

# ---------------------------------------------------------------------------
# Application instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Unitwise API",
    version="1.0",
    description="Backend API for the Unitwise academic assistant.",
)

# ---------------------------------------------------------------------------
# CORS — allow the React dev server during local development
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],   # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Mount the versioned router
# ---------------------------------------------------------------------------
app.include_router(router, prefix="/api/v1")
