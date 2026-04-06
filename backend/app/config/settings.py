"""
settings.py — Central configuration for the AKTU Brain project.
All paths, API keys, and tuning constants live here.
"""

import os
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# 1. Load environment variables from .env at project root
# ---------------------------------------------------------------------------
# 1. Calculate BASE_DIR first
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir)
)

# 2. Point directly to the .env file
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH)

# 3. Check for API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if GROQ_API_KEY is None:
    raise ValueError(
        "GROQ_API_KEY is missing. "
        "Please set it in your .env file or as an environment variable."
    )

# ---------------------------------------------------------------------------
# 2. Base path — resolves to the project root regardless of working directory
#    settings.py lives at  <root>/backend/app/config/settings.py
#    so we go up three levels to reach the project root.
# ---------------------------------------------------------------------------
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir)
)

# ---------------------------------------------------------------------------
# 3. Directory / file paths (relative to project root)
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(BASE_DIR, "backend", "data", "raw")
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "backend", "vector_store")
SYLLABUS_PATH = os.path.join(BASE_DIR, "backend", "data", "syllabus.yaml")
PROMPTS_DIR = os.path.join(BASE_DIR, "backend", "prompts")

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

