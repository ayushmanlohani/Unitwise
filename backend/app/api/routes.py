"""
routes.py — API route definitions for the Unitwise backend.

Endpoints:
    GET  /health  →  Quick liveness check.
    POST /ask     →  Accept a question + subject, return an LLM-grounded answer.
"""

from fastapi import APIRouter, HTTPException

from app.api.schemas import ChatRequest, ChatResponse
from app.search.searcher import search_documents
from app.llm.answerer import generate_answer

# ---------------------------------------------------------------------------
# Router instance — mounted by main.py under the /api/v1 prefix
# ---------------------------------------------------------------------------
router = APIRouter()


# ---------------------------------------------------------------------------
# GET /health — lightweight liveness probe
# ---------------------------------------------------------------------------
@router.get("/health")
def health_check():
    """Return a simple status message to confirm the API is running."""
    return {"status": "Unitwise API is live"}


# ---------------------------------------------------------------------------
# POST /ask — core Q&A endpoint
# ---------------------------------------------------------------------------
@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """
    Accept a student's question, retrieve relevant chunks from the
    vector store, and return an LLM-generated answer with sources.

    Raises:
        HTTPException 500 if any step in the pipeline fails.
    """
    try:
        # 1. Retrieve the most relevant document chunks
        chunks = search_documents(
            query=request.query,
            subject=request.subject,
        )

        # 2. Generate an answer grounded in those chunks (awaited — non-blocking)
        result = await generate_answer(
            query=request.query,
            retrieved_chunks=chunks,
            chat_history=request.chat_history,
        )

        # 3. Map the dict returned by generate_answer → ChatResponse
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
