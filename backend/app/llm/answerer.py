"""
answerer.py — Core pipeline. Zero external routing calls.

Pipeline:
    1. Gate (checkquestion.py): hard reject -> bounce -> explicit check -> rewrite
    2. ChromaDB search (strict subject filter)
    3. Groq gpt-oss-120b stream (single LLM call)

Three-Tier Response System (gate lives in checkquestion.py):
    Tier 1 — Topic explicitly in YAML syllabus → answer normally
    Tier 2 — Topic matches subject but not in YAML → answer with disclaimer
    Tier 3 — Topic unrelated to subject → block completely
"""

import asyncio
import logging
import time
from pathlib import Path
from functools import lru_cache
from langchain_groq import ChatGroq
from app.config.settings import (
    GROQ_MODEL,
    SYLLABUS_PATH,
    SUBJECT_NAMES,
)
from app.config.modes import MODE_PROMPTS, DEFAULT_MODE
from app.llm.checkquestion import (
    _is_hard_rejected,
    is_in_syllabus,
    is_explicitly_in_syllabus,
    rewrite_query,
)
from app.search.searcher import search_documents
from app.key_pool import MAX_REQUESTS_PER_MINUTE, get_pool_manager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt loader — cached
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _load_system_prompt() -> str:
    prompt_path = Path(SYLLABUS_PATH).parent.parent / "prompts" / "system.txt"
    try:
        return prompt_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        logger.error("system.txt not found at %s", prompt_path)
        return (
            "You are an academic assistant. Use the context below to answer.\n\n"
            "CONTEXT:\n{context}\n\n"
            "QUERY: {query}\n\n"
            "{mode_instructions}"
        )


# ---------------------------------------------------------------------------
# Main stream generator
# ---------------------------------------------------------------------------
async def generate_answer_stream(
    query: str,
    subject: str,
    chat_history: list = None,
    mode: str = "Academic",
):
    """
    Full pipeline with three-tier response system.

    Fresh query  → hard reject → bounce → explicit check → rewrite → search → stream
    Follow-up    → hard reject → rewrite → hard reject(rewritten) → bounce → explicit check → search → stream
    """
    if chat_history is None:
        chat_history = []

    started = time.perf_counter()
    has_history = len(chat_history) > 0

    # ----------------------------------------------------------------
    # STEP 1: Hard reject — runs on EVERY query, fresh or follow-up
    # ----------------------------------------------------------------
    if _is_hard_rejected(query):
        yield {
            "type": "content",
            "data": (
                f"I can only help with **{SUBJECT_NAMES.get(subject, subject)}** "
                f"syllabus topics. Please ask a question related to your subject."
            ),
        }
        return

    # ----------------------------------------------------------------
    # FRESH QUERY: bounce → explicit check → rewrite
    # ----------------------------------------------------------------
    if not has_history:
        if not is_in_syllabus(query, subject):
            logger.info("[Pipeline] Blocked fresh query: '%s'", query)
            yield {
                "type": "content",
                "data": (
                    f"I can only help with **{SUBJECT_NAMES.get(subject, subject)}** "
                    f"topics. Your question doesn't appear to be related to the syllabus. "
                    f"Try asking about a specific topic from your subject."
                ),
            }
            return

        explicit_in_syllabus = is_explicitly_in_syllabus(query, subject)
        standalone = rewrite_query(query, chat_history, subject)

    # ----------------------------------------------------------------
    # FOLLOW-UP: rewrite → hard reject → bounce → explicit check
    # ----------------------------------------------------------------
    else:
        standalone = rewrite_query(query, chat_history, subject)

        # Clarification needed
        if standalone == "CLARIFY_NEEDED":
            yield {
                "type": "content",
                "data": (
                    "Could you mention the topic name explicitly? "
                    "I want to make sure I give you the right explanation."
                ),
            }
            return

        # Hard reject the rewritten query too
        if _is_hard_rejected(standalone):
            yield {
                "type": "content",
                "data": (
                    f"I can only help with **{SUBJECT_NAMES.get(subject, subject)}** "
                    f"syllabus topics."
                ),
            }
            return

        if not is_in_syllabus(standalone, subject):
            logger.info(
                "[Pipeline] Blocked follow-up: '%s' -> '%s'", query, standalone
            )
            yield {
                "type": "content",
                "data": (
                    f"I can only help with **{SUBJECT_NAMES.get(subject, subject)}** "
                    f"topics. Your question doesn't appear to be related to the syllabus."
                ),
            }
            return

        explicit_in_syllabus = is_explicitly_in_syllabus(standalone, subject)

    logger.info(
        "[Timing] gate=%.0fms | subject=%s | query='%s'",
        (time.perf_counter() - started) * 1000, subject, query,
    )

    # ----------------------------------------------------------------
    # SEARCH
    # ----------------------------------------------------------------
    search_started = time.perf_counter()
    retrieved_docs = await asyncio.to_thread(
        search_documents, query=standalone, subject=subject
    )
    logger.info(
        "[Timing] search=%.0fms | subject=%s",
        (time.perf_counter() - search_started) * 1000, subject,
    )

    if not retrieved_docs:
        logger.warning(
            "[Pipeline] No results | subject=%s | query='%s'", subject, standalone
        )
        yield {
            "type": "content",
            "data": (
                f"I couldn't find relevant information for this topic in your "
                f"**{SUBJECT_NAMES.get(subject, subject)}** materials. "
                f"Try rephrasing your question or be more specific about the topic."
            ),
        }
        return

    # ----------------------------------------------------------------
    # BUILD CONTEXT
    # ----------------------------------------------------------------
    context_chunks = "\n\n".join(doc.page_content for doc in retrieved_docs)

    sources_set = set()
    for doc in retrieved_docs:
        book = doc.metadata.get("book", "Unknown")
        page = doc.metadata.get("page_number", "?")
        sources_set.add(f"{book} — Page {page}")

    sources = sorted(sources_set)

    # ----------------------------------------------------------------
    # BUILD CHAT HISTORY BLOCK
    # ----------------------------------------------------------------
    if chat_history:
        history_block = "\n\n".join(
            f"{'User' if m.get('role') == 'user' else 'Assistant'}:\n{m.get('content', '')}"
            for m in chat_history
        )
    else:
        history_block = "No previous context."

    # ----------------------------------------------------------------
    # BUILD PROMPT
    # ----------------------------------------------------------------
    system_template = _load_system_prompt()
    active_mode = MODE_PROMPTS.get(mode, MODE_PROMPTS[DEFAULT_MODE])

    system_prompt = (
        system_template
        .replace("{mode_instructions}", active_mode)
        .replace("{subject}", subject)
        .replace("{chat_history}", history_block)
        .replace("{context}", context_chunks)
        .replace("{query}", standalone)
    )

    messages = [
        ("system", system_prompt),
        ("human", standalone),
    ]

    # ----------------------------------------------------------------
    # TIER 2 DISCLAIMER — yield before answer if not in syllabus explicitly
    # ----------------------------------------------------------------
    if not explicit_in_syllabus:
        yield {
            "type": "content",
            "data": (
                f"> ⚠️ **Note:** This topic is not explicitly listed in your "
                f"**{SUBJECT_NAMES.get(subject, subject)}** syllabus, "
                f"but here is an explanation based on related course material."
                f"\n\n---\n\n"
            ),
        }

    # ----------------------------------------------------------------
    # STREAM FROM GROQ — using key pool
    # ----------------------------------------------------------------
    pool = get_pool_manager()
    key_state = await pool.acquire()

    if key_state is None:
        wait_seconds = round(pool.seconds_until_any_key_free())
        yield {
            "type": "content",
            "data": (
                f"⚠️ **Usage is very high right now.** "
                f"Please wait **{wait_seconds} seconds** and ask your question again."
            ),
        }
        return

    llm = ChatGroq(
        api_key=key_state.key,
        model_name=GROQ_MODEL,
        temperature=0.0,
        max_retries=2,
        timeout=60,
    )

    try:
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield {"type": "content", "data": chunk.content}
        key_state.record_success()

    except Exception as e:
        error_str = str(e).lower()
        key_state.record_error()

        if any(code in error_str for code in ["429", "rate limit"]):
            key_state.requests_this_minute = MAX_REQUESTS_PER_MINUTE
            wait_seconds = round(key_state.seconds_until_reset)
            yield {
                "type": "content",
                "data": (
                    f"⚠️ **Usage is very high right now.** "
                    f"Please wait **{wait_seconds} seconds** and ask your question again."
                ),
            }
        elif any(code in error_str for code in ["413", "too large"]):
            yield {
                "type": "content",
                "data": "⚠️ **Response too large.** Try asking about a more specific topic.",
            }
        else:
            logger.exception("Groq streaming error on key #%d", key_state.index)
            yield {
                "type": "content",
                "data": "⚠️ **Error:** Something went wrong. Please try again.",
            }
        return

    # ----------------------------------------------------------------
    # DONE
    # ----------------------------------------------------------------
    logger.info(
        "[Timing] total=%.0fms | subject=%s | query='%s'",
        (time.perf_counter() - started) * 1000, subject, query,
    )
    yield {"type": "sources", "data": sources}
    yield {"type": "done", "data": ""}