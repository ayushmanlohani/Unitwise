"""
schemas.py — Pydantic models for the Unitwise API request / response layer.

These schemas enforce input validation on incoming requests and guarantee
a consistent JSON shape on every response.
"""

from typing import List, Dict
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """
    Body of a POST /ask request.

    Attributes:
        query:   The student's natural-language question.
        subject: The subject to search within (e.g. "computer_networks").
        chat_history: Optional list of previous messages in the conversation.
    """
    query: str
    subject: str
    chat_history: List[Dict[str, str]] = []


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
