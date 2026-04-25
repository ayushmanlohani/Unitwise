"""
schemas.py — Pydantic models for the Unitwise API request / response layer.

These schemas enforce input validation on incoming requests and guarantee
a consistent JSON shape on every response.
"""

from typing import List, Dict, Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Valid values — kept in sync with syllabus.yaml and modes.py
# ---------------------------------------------------------------------------

SubjectCode = Literal["CN", "DIP", "EML", "SCT", "DMW", "QC"]
ModeName = Literal["Academic", "Simplified", "Exam Prep", "Revision", "Analogy"]


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """
    Body of a POST /ask request.

    Attributes:
        query:        The student's natural-language question (max 500 chars).
        subject:      Subject folder code — must be one of the 6 valid codes.
        chat_history: Optional list of previous messages in the conversation.
        mode:         Response style — must be one of the 5 valid mode names.
    """
    query: str = Field(..., min_length=1, max_length=500)
    subject: SubjectCode
    chat_history: List[Dict[str, str]] = []
    mode: ModeName = "Academic"


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------

class ChatResponse(BaseModel):
    """
    Shape returned by the POST /ask endpoint.

    Attributes:
        answer:  The LLM-generated answer grounded in retrieved context.
        sources: A list of source citations (e.g. "Book X, Page 42").
    """
    answer: str
    sources: list[str]
