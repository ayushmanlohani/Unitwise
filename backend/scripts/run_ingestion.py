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

    # ----- 2 & 3. Dynamically Extract ALL Subjects and Books -----
    all_pages_data = []

    print()
    print("=" * 60)
    print("STEP 2 — Extracting text from PDFs")
    print("=" * 60)

    # Loop through every subject in the YAML
    for subject_entry in syllabus["subjects"]:
        subject_name = subject_entry["name"]
        subject_folder = subject_entry["folder"]
        
        print(f"\n➤ Processing Subject: {subject_name} ({subject_folder})")

        # Create a dictionary to easily find the PDF filename using the short_name
        book_map = {book["short_name"]: book["file"] for book in subject_entry["books"]}

        # Loop through every unit in this subject
        for unit in subject_entry["units"]:
            unit_number = unit["number"]
            
            # Loop through every source/book listed in this specific unit
            for source in unit["sources"]:
                book_short_name = source["book"]
                book_filename = book_map.get(book_short_name)

                if not book_filename:
                    print(f"  ⚠ Error: PDF filename for '{book_short_name}' not found in book list. Skipping.")
                    continue

                pages_str = str(source["pages"])
                
                try:
                    start_page, end_page = map(int, pages_str.split("-"))
                    
                    pages_data = extract_text_for_unit(
                        subject=subject_folder,
                        unit=unit_number,
                        book_filename=book_filename,
                        start_page=start_page,
                        end_page=end_page,
                    )
                    all_pages_data.extend(pages_data)
                except Exception as e:
                    print(f"  ⚠ Failed to extract pages {pages_str} from {book_filename}: {e}")

    print(f"\n✔ Total pages extracted across ALL subjects: {len(all_pages_data)}")

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
