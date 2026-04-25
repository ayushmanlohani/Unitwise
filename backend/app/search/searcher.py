"""
searcher.py — Query the ChromaDB vector store for relevant document chunks.

Connects to the persisted Chroma database, applies subject filters,
and returns the top-K most similar results that meet the relevance threshold.

Uses a **lazy-loaded singleton** so the embedding model and Chroma client
are initialised only once and reused across all subsequent requests.
Call `init_vector_store()` from the FastAPI lifespan hook to pre-warm on
startup instead of paying the load cost on the first request.
"""

import logging
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-load singleton for the Chroma vector store
# ---------------------------------------------------------------------------
_vector_store_instance: Chroma | None = None


def init_vector_store() -> None:
    """
    Explicitly initialise (warm up) the vector-store singleton.

    Call this once from the FastAPI lifespan hook so the heavy embedding
    model and ChromaDB connection are ready before the first request arrives.
    Subsequent calls to `get_vector_store()` return the cached instance.
    """
    get_vector_store()
    logger.info("Vector store initialised and ready.")


def get_vector_store() -> Chroma:
    """
    Return the shared Chroma vector-store instance (singleton).

    On the first call the embedding model is loaded and the Chroma
    client is connected.  Subsequent calls return the cached instance
    immediately.
    """
    global _vector_store_instance

    if _vector_store_instance is None:
        logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
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
        logger.info("Chroma vector store connected at %s", persist_dir)

    return _vector_store_instance


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def search_documents(query: str, subject: str, unit: int = None) -> list:
    """
    Search the vector store for chunks relevant to a query.

    Applies a subject filter so only chunks belonging to the requested
    subject are considered.  Results whose similarity score falls below
    ``settings.SIMILARITY_THRESHOLD`` are discarded; if none remain the
    function returns an empty list (which the caller treats as off-topic).

    Args:
        query:   The natural-language search string.
        subject: Subject folder code to filter on (e.g. "CN").
        unit:    Optional unit number to narrow the search further.

    Returns:
        A list of LangChain Document objects (top-K results), or an empty
        list if no relevant chunks were found for this subject.
    """
    store = get_vector_store()

    search_filter: dict = {"subject": subject}
    if unit is not None:
        search_filter["unit"] = unit

    # similarity_search_with_relevance_scores returns (Document, score) tuples
    # where score is a cosine similarity in [0, 1] (higher = more similar).
    results_with_scores = store.similarity_search_with_relevance_scores(
        query=query,
        k=settings.TOP_K,
        filter=search_filter,
    )

    # Filter out chunks that are not sufficiently similar to the query.
    relevant = [
        doc
        for doc, score in results_with_scores
        if score >= settings.SIMILARITY_THRESHOLD
    ]

    if not relevant:
        logger.info(
            "[Search] No chunks above threshold %.2f for subject=%s query='%s'",
            settings.SIMILARITY_THRESHOLD,
            subject,
            query,
        )

    return relevant
