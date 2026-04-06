"""
indexer.py — Embed text chunks and persist them in a ChromaDB vector store.

Wipes any existing vector store before re-indexing to ensure a clean state.
Uses HuggingFace sentence-transformer embeddings configured in settings.
"""

import os
import shutil

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings


def index_chunks(chunks: list) -> None:
    """
    Embed a list of text chunks and store them in ChromaDB.

    Args:
        chunks: A list of dicts, each with:
            - "text"     : the chunk string
            - "metadata" : dict with subject, unit, book, page_number

    Workflow:
        1. Wipe the existing vector store directory (if any).
        2. Initialise the HuggingFace embedding model.
        3. Separate texts and metadata into parallel lists.
        4. Call Chroma.from_texts() to embed and persist.
    """

    # ----- 1. Wipe old vector store -----
    if os.path.exists(settings.VECTOR_STORE_DIR):
        shutil.rmtree(settings.VECTOR_STORE_DIR)
        print("🗑  Old vector store wiped.")

    os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)
    print(f"📁 Vector store directory ready: {settings.VECTOR_STORE_DIR}")

    # ----- 2. Setup embeddings -----
    print(f"⏳ Loading embedding model: {settings.EMBEDDING_MODEL} ...")
    embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
    print("✔  Embedding model loaded.")

    # ----- 3. Prepare parallel lists -----
    texts = []
    metadatas = []

    for chunk in chunks:
        texts.append(chunk["text"])
        metadatas.append(chunk["metadata"])

    print(f"📦 Embedding {len(texts)} chunk(s) — this may take a moment ...")

    # ----- 4. Store in Chroma -----
    Chroma.from_texts(
        texts=texts,
        metadatas=metadatas,
        embedding=embeddings,
        persist_directory=settings.VECTOR_STORE_DIR,
    )

    print(
        f"✔  Successfully saved {len(texts)} chunk(s) "
        f"to the vector store at {settings.VECTOR_STORE_DIR}"
    )
