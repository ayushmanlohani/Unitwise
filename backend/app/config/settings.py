"""
settings.py — All configuration in one place.
All paths are absolute, derived from this file's location.
"""

import os
import logging as _logging
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

logger = _logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY_1")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data" / "raw"
VECTOR_STORE_DIR = str(PROJECT_ROOT / "vector_store")
SYLLABUS_PATH = PROJECT_ROOT / "data" / "syllabus.yaml"
PROMPTS_DIR = PROJECT_ROOT / "prompts"

# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GROQ_MODEL = "openai/gpt-oss-120b"
TOP_K = 7

# ---------------------------------------------------------------------------
# Valid subject codes — single source of truth
# ---------------------------------------------------------------------------
VALID_SUBJECTS = {"CN", "DIP", "EML", "SCT", "DMW", "QC"}

SUBJECT_NAMES = {
    "CN": "Computer Network",
    "DIP": "Digital Image Processing",
    "EML": "Essentials of Machine Learning",
    "SCT": "Soft Computing Techniques",
    "DMW": "Data Mining and Warehousing",
    "QC": "Quantum Computing",
}

# ---------------------------------------------------------------------------
# Groq API Key Pool
# To add a new key: add GROQ_API_KEY_N to .env and add the name here.
# ---------------------------------------------------------------------------
_GROQ_KEY_ENV_NAMES = [
    "GROQ_API_KEY_1",
    "GROQ_API_KEY_2",
    "GROQ_API_KEY_3",
    "GROQ_API_KEY_4",
    "GROQ_API_KEY_5",
    # "GROQ_API_KEY_6",
    # "GROQ_API_KEY_7",
]


def get_groq_keys() -> list[str]:
    """
    Load all available Groq API keys from environment.
    Skips missing keys gracefully — only loads what exists.
    """
    keys = []
    for name in _GROQ_KEY_ENV_NAMES:
        val = os.getenv(name)
        if val and val.strip():
            keys.append(val.strip())
            logger.info("Loaded Groq key: %s", name)
        else:
            logger.debug("Groq key not found (skipping): %s", name)

    if not keys:
        legacy = os.getenv("GROQ_API_KEY")
        if legacy:
            keys.append(legacy.strip())
            logger.warning("Using legacy GROQ_API_KEY.")

    if not keys:
        raise ValueError(
            "No Groq API keys found. "
            "Add GROQ_API_KEY_1 (and optionally _2 through _5) to .env"
        )

    logger.info("Total Groq keys loaded: %d", len(keys))
    return keys