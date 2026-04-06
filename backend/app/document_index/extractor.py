"""
extractor.py — Extract text from PDF pages based on a YAML syllabus config.

Provides two functions:
  • load_syllabus()  – parse the syllabus YAML file.
  • extract_text_for_unit() – pull page-level text from a PDF for a given unit.
"""

import fitz  # PyMuPDF
import yaml
import os

from app.config.settings import DATA_DIR


# ---------------------------------------------------------------------------
# 1. YAML loader
# ---------------------------------------------------------------------------

def load_syllabus(yaml_path: str) -> dict:
    """
    Open and parse a YAML syllabus file.

    Args:
        yaml_path: Absolute or relative path to the YAML file.

    Returns:
        A dictionary representing the parsed YAML content.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            syllabus = yaml.safe_load(f)
        print(f"✔ Syllabus loaded successfully from {yaml_path}")
        return syllabus

    except FileNotFoundError:
        print(f"✖ Syllabus file not found: {yaml_path}")
        raise

    except yaml.YAMLError as e:
        print(f"✖ Error parsing YAML file: {e}")
        raise


# ---------------------------------------------------------------------------
# 2. PDF text extractor
# ---------------------------------------------------------------------------

def extract_text_for_unit(
    subject: str,
    unit: int,
    book_filename: str,
    start_page: int,
    end_page: int,
) -> list[dict]:
    """
    Extract text from a range of PDF pages for a specific subject unit.

    The PDF is located at  DATA_DIR / <subject> / <book_filename>.
    Page numbers use **1-based** book numbering (the same numbers printed on
    the page).  Internally, PyMuPDF uses 0-based indexing, so the function
    handles the conversion automatically.

    Args:
        subject:       Subject folder name (e.g. "computer_networks").
        unit:          Unit number (used only for metadata).
        book_filename: Name of the PDF file inside the subject folder.
        start_page:    First book page to extract (1-based, inclusive).
        end_page:      Last book page to extract (1-based, inclusive).

    Returns:
        A list of dicts, one per page, each containing:
            - "text"     : the extracted page text (str)
            - "metadata" : dict with keys subject, unit, book, page_number
    """
    pdf_path = os.path.join(DATA_DIR, subject, book_filename)

    # --- safety check ---
    if not os.path.isfile(pdf_path):
        print(f"✖ PDF not found: {pdf_path}")
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    print(
        f"📄 Extracting pages {start_page} to {end_page} "
        f"from {book_filename}..."
    )

    pages_output = []

    doc = fitz.open(pdf_path)

    for page_num in range(start_page, end_page + 1):
        # PyMuPDF pages are 0-indexed; book page 1 → index 0
        page_index = page_num - 1

        if page_index < 0 or page_index >= len(doc):
            print(
                f"  ⚠ Page {page_num} is out of range "
                f"(PDF has {len(doc)} pages). Skipping."
            )
            continue

        page = doc.load_page(page_index)
        text = page.get_text("text")

        pages_output.append(
            {
                "text": text,
                "metadata": {
                    "subject": subject,
                    "unit": unit,
                    "book": book_filename,
                    "page_number": page_num,
                },
            }
        )

    doc.close()

    print(
        f"  ✔ Extracted {len(pages_output)} page(s) for "
        f"Unit {unit} of {subject}."
    )

    return pages_output
