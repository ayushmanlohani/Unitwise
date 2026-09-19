"""
searcher.py — Query ChromaDB with strict subject filtering.

Uses raw chromadb + SentenceTransformer directly.
Must use same COLLECTION_NAME as indexer.py.
Singleton pattern: model loaded once, reused forever.
"""

import logging
import time
import torch
from sentence_transformers import SentenceTransformer
import chromadb
from app.config.settings import VECTOR_STORE_DIR, EMBEDDING_MODEL, TOP_K

logger = logging.getLogger(__name__)

COLLECTION_NAME = "unitwise_chunks"

_model = None
_client = None
_collection = None


def _get_model():
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Loading embedding model on %s...", device)
        _model = SentenceTransformer(EMBEDDING_MODEL, device=device)
        logger.info("Embedding model ready.")
    return _model


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
        _collection = _client.get_collection(name=COLLECTION_NAME)
        logger.info("ChromaDB collection '%s' loaded.", COLLECTION_NAME)
    return _collection


def search_documents(query: str, subject: str, unit: int = None) -> list:
    started = time.perf_counter()
    model = _get_model()
    collection = _get_collection()

    query_embedding = model.encode(query, convert_to_numpy=True).tolist()

    where_filter = {"subject": {"$eq": subject}}
    if unit is not None:
        where_filter = {
            "$and": [
                {"subject": {"$eq": subject}},
                {"unit": {"$eq": unit}},
            ]
        }

    logger.info("Searching | subject=%s | query='%s'", subject, query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=TOP_K,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    # Convert raw chromadb results to LangChain-style Document objects
    # so answerer.py doesn't need to change
    from langchain_core.documents import Document
    docs = []
    if results and results["documents"] and results["documents"][0]:
        for doc_text, metadata in zip(
            results["documents"][0],
            results["metadatas"][0],
        ):
            docs.append(Document(page_content=doc_text, metadata=metadata))

    logger.info(
        "Found %d results for subject=%s in %.0fms",
        len(docs), subject, (time.perf_counter() - started) * 1000,
    )
    return docs
