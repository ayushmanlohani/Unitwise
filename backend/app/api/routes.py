"""
routes.py — API route definitions for the Unitwise backend.

Endpoints:
    GET  /health  →  Quick liveness check.
    POST /ask     →  Accept a question + subject, return an LLM-grounded answer.
"""

import json
import traceback
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.api.schemas import ChatRequest, ChatResponse
from app.llm.answerer import generate_answer_stream
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
@router.post("/ask")
async def ask_question(request: ChatRequest):
    async def event_generator():
        try:
            # 2. Prevent Backend Buffering: Iterate over the async stream
            async for event in generate_answer_stream(
                query=request.query,
                subject=request.subject,
                chat_history=request.chat_history
            ):
                # 1. The Delimiter Requirement: Strict JSON dump followed exactly by \n\n
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"

    # 3. SSE Required Headers: Prevent browser/proxy buffering
    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )