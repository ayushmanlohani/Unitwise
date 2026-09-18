"""
chunker.py — Split page text into overlapping chunks.
"""

import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config.settings import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


def chunk_text(pages_data: list[dict]) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    all_chunks = []
    for page in pages_data:
        for chunk in splitter.split_text(page["text"]):
            all_chunks.append({
                "text": chunk,
                "metadata": page["metadata"].copy(),
            })

    logger.info(
        "Chunked %d pages into %d chunks.", len(pages_data), len(all_chunks)
    )
    return all_chunks