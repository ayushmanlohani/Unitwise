"""
searcher.py — Query the ChromaDB vector store for relevant document chunks.

Connects to the persisted Chroma database, applies optional subject/unit
filters, and returns the top-K most similar results.

Uses a **lazy-loaded singleton** so the embedding model and Chroma client
are initialised only once and reused across all subsequent requests.
"""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings


# ---------------------------------------------------------------------------
# Lazy-load singleton for the Chroma vector store
# ---------------------------------------------------------------------------
# Why a singleton?
#   • HuggingFaceEmbeddings downloads / loads model weights on first use.
#   • Chroma opens a persistent SQLite connection to the vector store.
#   Both are expensive to create but safe to reuse, so we initialise once
#   and cache the instance for the lifetime of the process.
# ---------------------------------------------------------------------------
_vector_store_instance = None


def get_vector_store() -> Chroma:
    """
    Return the shared Chroma vector-store instance.

    On the first call the embedding model is loaded and the Chroma
    client is connected.  Subsequent calls return the cached instance
    immediately (singleton pattern).
    """
    global _vector_store_instance

    if _vector_store_instance is None:
        embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)

        # Resolve to an absolute path so it works regardless of CWD
        # searcher.py lives at  <root>/backend/app/search/searcher.py
        # .parent.parent.parent  →  <root>/backend/
        persist_dir = str(
            Path(__file__).resolve().parent.parent.parent / "vector_store"
        )

        _vector_store_instance = Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings,
        )

    return _vector_store_instance


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def search_documents(query: str, subject: str, unit: int = None) -> list:
    """
    Search the vector store for chunks relevant to a query.

    Args:
        query:   The natural-language search string.
        subject: Subject folder name to filter on (e.g. "computer_networks").
        unit:    Optional unit number to narrow the search further.

    Returns:
        A list of LangChain Document objects (top-K results).
    """

    store = get_vector_store()

    # ── DIAGNOSTIC: filter temporarily disabled to isolate DB vs filter issue ──
    # normalised_subject = subject.strip().lower().replace(" ", "_")
    # search_filter = {"subject": normalised_subject}
    # if unit is not None:
    #     search_filter["unit"] = unit

    return store.similarity_search(
        query=query,
        k=settings.TOP_K,
        # filter=search_filter,  # DIAGNOSTIC: re-enable after test
    )
