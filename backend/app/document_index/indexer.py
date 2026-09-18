"""
indexer.py — High-speed embedding and ChromaDB storage.

Features:
- Saves embeddings to numpy cache so re-runs skip encoding entirely
- Uses raw chromadb client — no LangChain wrapper confusion
- Processes in safe batches of 5000
- Compatible with searcher.py exactly
"""

import os
import shutil
import logging
import numpy as np
import torch
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from app.config.settings import VECTOR_STORE_DIR, EMBEDDING_MODEL, VALID_SUBJECTS

logger = logging.getLogger(__name__)

# Must match searcher.py exactly
COLLECTION_NAME = "unitwise_chunks"
CACHE_DIR = str(Path(VECTOR_STORE_DIR).parent / "embeddings_cache")
BATCH_SIZE = 5000


def index_chunks(chunks: list) -> int:
    # ── 1. Validate ──
    valid_chunks = [
        c for c in chunks
        if c.get("metadata", {}).get("subject") in VALID_SUBJECTS
        and c.get("text", "").strip()
    ]
    texts = [c["text"] for c in valid_chunks]
    metadatas = [c["metadata"] for c in valid_chunks]
    total = len(texts)
    logger.info("Validated %d chunks.", total)

    # ── 2. Wipe old vector store ──
    if os.path.exists(VECTOR_STORE_DIR):
        shutil.rmtree(VECTOR_STORE_DIR)
        logger.info("Old vector store wiped.")
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)

    # ── 3. Encode (with numpy cache) ──
    cache_file = Path(CACHE_DIR) / "embeddings.npy"
    texts_cache_file = Path(CACHE_DIR) / "texts.npy"

    if cache_file.exists() and texts_cache_file.exists():
        cached_texts = np.load(str(texts_cache_file), allow_pickle=True).tolist()
        if cached_texts == texts:
            logger.info("✅ Cache hit — loading embeddings from disk. Skipping encoding.")
            embeddings_array = np.load(str(cache_file))
        else:
            logger.info("Cache mismatch — re-encoding.")
            embeddings_array = _encode(texts)
            _save_cache(embeddings_array, texts, cache_file, texts_cache_file)
    else:
        logger.info("No cache found — encoding from scratch.")
        embeddings_array = _encode(texts)
        _save_cache(embeddings_array, texts, cache_file, texts_cache_file)

    # ── 4. Store in ChromaDB ──
    logger.info("Storing vectors in ChromaDB...")
    client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)

    # Always start fresh
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [str(i) for i in range(total)]
    embeddings_list = embeddings_array.tolist()

    for i in range(0, total, BATCH_SIZE):
        end = min(i + BATCH_SIZE, total)
        collection.add(
            ids=ids[i:end],
            embeddings=embeddings_list[i:end],
            documents=texts[i:end],
            metadatas=metadatas[i:end],
        )
        logger.info(
            "Stored batch %d/%d (%d chunks)",
            i // BATCH_SIZE + 1,
            (total + BATCH_SIZE - 1) // BATCH_SIZE,
            end - i,
        )

    logger.info("✅ Successfully indexed %d chunks.", total)
    return total


def _encode(texts: list) -> np.ndarray:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info("Encoding on device: %s", device)
    model = SentenceTransformer(EMBEDDING_MODEL, device=device)
    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    return embeddings


def _save_cache(embeddings: np.ndarray, texts: list, cache_file: Path, texts_file: Path):
    np.save(str(cache_file), embeddings)
    np.save(str(texts_file), np.array(texts, dtype=object))
    logger.info("✅ Embeddings cached to disk at %s", cache_file)