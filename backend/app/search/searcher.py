"""
searcher.py — Query ChromaDB with strict subject filtering + cross-encoder rerank.

Retrieve CANDIDATE_TOP_K via cosine, rerank to FINAL_TOP_K.
Silent cosine fallback: any reranker failure returns top cosine docs.
Singleton pattern: models loaded once, reused forever.
"""

import logging
import time
import torch
from sentence_transformers import SentenceTransformer
import chromadb
from app.config.settings import (
    VECTOR_STORE_DIR,
    EMBEDDING_MODEL,
    CANDIDATE_TOP_K,
    FINAL_TOP_K,
    RERANKER_MODEL,
)

logger = logging.getLogger(__name__)

COLLECTION_NAME = "unitwise_chunks"

_model = None
_client = None
_collection = None
_reranker = None
_reranker_failed = False


def _get_model():
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Loading embedding model on %s...", device)
        _model = SentenceTransformer(EMBEDDING_MODEL, device=device)
        logger.info("Embedding model ready.")
    return _model


def _get_reranker():
    """Load cross-encoder once. Returns None on failure (fallback mode)."""
    global _reranker, _reranker_failed
    if _reranker is not None or _reranker_failed:
        return _reranker
    try:
        from sentence_transformers import CrossEncoder
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Loading reranker %s on %s...", RERANKER_MODEL, device)
        _reranker = CrossEncoder(RERANKER_MODEL, device=device)
        logger.info("Reranker ready.")
    except Exception as e:
        _reranker_failed = True
        logger.warning("Reranker load failed, cosine fallback: %s", e)
    return _reranker


def _rerank(query: str, docs: list) -> list:
    """Score query-vs-chunk pairs, return top FINAL_TOP_K. Falls back to cosine order."""
    if len(docs) <= FINAL_TOP_K:
        return docs
    reranker = _get_reranker()
    if reranker is None:
        return docs[:FINAL_TOP_K]
    try:
        pairs = [(query, d.page_content) for d in docs]
        scores = reranker.predict(pairs)
        ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
        return [d for _, d in ranked[:FINAL_TOP_K]]
    except Exception as e:
        logger.warning("Rerank failed, cosine fallback: %s", e)
        return docs[:FINAL_TOP_K]


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
        n_results=CANDIDATE_TOP_K,
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

    rerank_started = time.perf_counter()
    docs = _rerank(query, docs)
    rerank_ms = (time.perf_counter() - rerank_started) * 1000

    logger.info(
        "Found %d results for subject=%s in %.0fms (rerank %.0fms)",
        len(docs), subject, (time.perf_counter() - started) * 1000, rerank_ms,
    )
    return docs
