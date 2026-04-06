"""
chunker.py — Split extracted page text into smaller, overlapping chunks.

Uses LangChain's RecursiveCharacterTextSplitter with chunk size and
overlap values pulled from the central settings module.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings


def chunk_text(pages_data: list[dict]) -> list[dict]:
    """
    Split page-level text into smaller chunks for embedding.

    Args:
        pages_data: A list of dicts, each with:
            - "text"     : the full page text (str)
            - "metadata" : dict with subject, unit, book, page_number

    Returns:
        A list of dicts, one per chunk, each containing:
            - "text"     : the chunk string
            - "metadata" : a copy of the originating page's metadata
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )

    all_chunks = []

    for page in pages_data:
        chunks = splitter.split_text(page["text"])

        for chunk in chunks:
            all_chunks.append(
                {
                    "text": chunk,
                    "metadata": page["metadata"].copy(),
                }
            )

    print(
        f"✔ Chunked {len(pages_data)} page(s) into "
        f"{len(all_chunks)} chunk(s)."
    )

    return all_chunks    
