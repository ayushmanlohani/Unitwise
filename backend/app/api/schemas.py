"""
schemas.py — Request and response models.
"""

from typing import List, Dict
from pydantic import BaseModel, field_validator
from app.config.settings import VALID_SUBJECTS


class ChatRequest(BaseModel):
    query: str
    subject: str
    chat_history: List[Dict[str, str]] = []
    mode: str = "Academic"

    @field_validator("subject")
    @classmethod
    def subject_must_be_valid(cls, v: str) -> str:
        if v not in VALID_SUBJECTS:
            raise ValueError(f"Invalid subject '{v}'. Must be one of {VALID_SUBJECTS}")
        return v

    @field_validator("query")
    @classmethod
    def query_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be empty.")
        return v.strip()


class HealthResponse(BaseModel):
    status: str
    version: str