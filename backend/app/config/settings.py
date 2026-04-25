"""
settings.py — Central configuration for the AKTU Brain project.
All paths, API keys, and tuning constants live here.
"""

import os
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# 1. Absolute path anchoring
#    settings.py lives at  <root>/backend/app/config/settings.py
#    CURRENT_DIR  → .../backend/app/config
#    PROJECT_ROOT → .../  (three levels up)
#    All paths derived below are therefore absolute and CWD-independent.
# ---------------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))

# ---------------------------------------------------------------------------
# 2. Load environment variables from .env at project root
# ---------------------------------------------------------------------------
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=ENV_PATH)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if GROQ_API_KEY is None:
    raise ValueError(
        "GROQ_API_KEY is missing. "
        "Please set it in your .env file or as an environment variable."
    )

# CORS — comma-separated list of allowed origins read from the environment.
# Set CORS_ORIGINS in your HF Spaces secrets (and local .env) like:
#   CORS_ORIGINS=https://unitwise.vercel.app,http://localhost:3000
_raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS: list[str] = [o.strip() for o in _raw_cors.split(",") if o.strip()]

# ---------------------------------------------------------------------------
# 3. Absolute directory / file paths (derived from PROJECT_ROOT)
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(PROJECT_ROOT, "backend", "data", "raw")
VECTOR_STORE_DIR = os.path.join(PROJECT_ROOT, "backend", "vector_store")
SYLLABUS_PATH = os.path.join(PROJECT_ROOT, "backend", "data", "syllabus.yaml")
PROMPTS_DIR = os.path.join(PROJECT_ROOT, "backend", "prompts")

# ---------------------------------------------------------------------------
# 4. Chunking constants
# ---------------------------------------------------------------------------
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# ---------------------------------------------------------------------------
# 5. Model & retrieval constants
# ---------------------------------------------------------------------------
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
# llama-3.3-70b-versatile follows system-prompt rules reliably (vs 8b-instant)
LLM_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = 0.0
# 8 subject-filtered chunks give better precision than 15 unfiltered ones
TOP_K = 8
# Minimum cosine similarity for a retrieved chunk to be considered relevant.
# Queries that produce no chunk above this threshold are treated as off-topic.
SIMILARITY_THRESHOLD = 0.30

