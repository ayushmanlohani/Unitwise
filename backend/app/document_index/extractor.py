"""
extractor.py — Extract text from PDFs using syllabus page ranges.
"""

import fitz
import yaml
import logging
from pathlib import Path
from app.config.settings import DATA_DIR, SYLLABUS_PATH

logger = logging.getLogger(__name__)


def load_syllabus() -> dict:
    with open(SYLLABUS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def extract_text_for_unit(
    subject: str,
    unit: int,
    book_filename: str,
    start_page: int,
    end_page: int,
) -> list[dict]:
    pdf_path = Path(DATA_DIR) / subject / book_filename

    if not pdf_path.is_file():
        logger.error("PDF not found: %s", pdf_path)
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.info(
        "Extracting pages %d-%d from %s (subject=%s, unit=%d)",
        start_page, end_page, book_filename, subject, unit,
    )

    pages_output = []
    doc = fitz.open(str(pdf_path))

    for page_num in range(start_page, end_page + 1):
        page_index = page_num - 1
        if page_index < 0 or page_index >= len(doc):
            logger.warning(
                "Page %d out of range for %s (has %d pages). Skipping.",
                page_num, book_filename, len(doc),
            )
            continue

        text = doc.load_page(page_index).get_text("text")
        if text.strip():
            pages_output.append({
                "text": text,
                "metadata": {
                    "subject": subject,
                    "unit": unit,
                    "book": book_filename,
                    "page_number": page_num,
                },
            })

    doc.close()
    logger.info(
        "Extracted %d pages for unit %d of %s", len(pages_output), unit, subject
    )
    return pages_output