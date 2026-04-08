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
LLM_MODEL = "llama-3.1-8b-instant"
LLM_TEMPERATURE = 0.3
TOP_K = 5

