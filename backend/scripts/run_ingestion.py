"""
run_ingestion.py — Master script for the RAG ingestion pipeline.

Orchestrates:  Syllabus → Extract → Chunk → Index
Run from the backend/ directory:
    python scripts/run_ingestion.py
"""

import os
import sys

# ---------------------------------------------------------------------------
# Path setup — let Python find the `app` package from any working directory
# ---------------------------------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.document_index.extractor import load_syllabus, extract_text_for_unit
from app.document_index.chunker import chunk_text
from app.document_index.indexer import index_chunks


if __name__ == "__main__":

    # ----- 1. Load syllabus -----
    print("=" * 60)
    print("STEP 1 — Loading syllabus")
    print("=" * 60)
    syllabus = load_syllabus(settings.SYLLABUS_PATH)

    # ----- 2. Setup variables -----
    subject = "Computer Networks"
    book_filename = "Richard_Stevens-TCP-IP_Illustrated-EN.pdf"
    all_pages_data = []

    # Find the matching subject entry in the syllabus
    subject_entry = None
    for s in syllabus["subjects"]:
        if s["name"] == subject:
            subject_entry = s
            break

    if subject_entry is None:
        print(f"✖ Subject '{subject}' not found in syllabus.")
        sys.exit(1)

    # ----- 3. Extract text from each unit -----
    print()
    print("=" * 60)
    print("STEP 2 — Extracting text from PDF")
    print("=" * 60)

    for unit in subject_entry["units"]:
        unit_number = unit["number"]
        pages_str = unit["sources"][0]["pages"]          # e.g. "1-20"
        start_page, end_page = map(int, pages_str.split("-"))

        pages_data = extract_text_for_unit(
            subject=subject_entry["folder"],
            unit=unit_number,
            book_filename=book_filename,
            start_page=start_page,
            end_page=end_page,
        )
        all_pages_data.extend(pages_data)

    print(f"\n✔ Total pages extracted: {len(all_pages_data)}")

    # ----- 4. Chunk -----
    print()
    print("=" * 60)
    print("STEP 3 — Chunking extracted text")
    print("=" * 60)
    all_chunks = chunk_text(all_pages_data)

    # ----- 5. Index -----
    print()
    print("=" * 60)
    print("STEP 4 — Embedding & indexing into ChromaDB")
    print("=" * 60)
    index_chunks(all_chunks)

    # ----- Done -----
    print()
    print("=" * 60)
    print("🎉 Ingestion pipeline completed successfully!")
    print("=" * 60)
