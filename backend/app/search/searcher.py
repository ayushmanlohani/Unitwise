"""
searcher.py — Query the ChromaDB vector store for relevant document chunks.

Connects to the persisted Chroma database, applies optional subject/unit
filters, and returns the top-K most similar results.
"""

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings


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

    # ----- 1. Setup embedding model -----
    embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)

    # ----- 2. Connect to the persisted Chroma store -----
    db = Chroma(
        persist_directory=settings.VECTOR_STORE_DIR,
        embedding_function=embeddings,
    )

    # ----- 3. Build metadata filter -----
    search_filter = {"subject": subject}

    if unit is not None:
        search_filter["unit"] = unit

    # ----- 4. Run similarity search -----
    results = db.similarity_search(
        query=query,
        k=settings.TOP_K,
        filter=search_filter,
    )

    return results
