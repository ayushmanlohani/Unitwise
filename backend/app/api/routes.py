"""
routes.py — API routes with IP rate limiting.
"""

import json
import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.api.schemas import ChatRequest, HealthResponse
from app.llm.answerer import generate_answer_stream
from app.ratelimit import get_limiter, limit_message

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "Unitwise API v2 is live", "version": "2.0"}


@router.get("/pool-status")
def pool_status():
    """Debug endpoint — shows key pool usage."""
    from app.key_pool import get_pool_manager
    return {"keys": get_pool_manager().status()}


@router.post("/ask")
@limiter.limit("10/minute")
@limiter.limit("3/10seconds")
async def ask_question(request: Request, body: ChatRequest):
    async def event_generator():
        gate = get_limiter().check(body.user_id)
        if not gate["allowed"]:
            yield {
                "type": "content",
                "data": limit_message(
                    gate["wait_seconds"], gate["mode"], gate["active_users"]
                ),
            }
            return
        try:
            async for event in generate_answer_stream(
                query=body.query,
                subject=body.subject,
                chat_history=body.chat_history,
                mode=body.mode,
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.exception("Unhandled error in stream")
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )