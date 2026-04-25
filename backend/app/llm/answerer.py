import logging
from pathlib import Path
from langchain_groq import ChatGroq
from app.config import settings
from app.config.modes import MODE_PROMPTS, DEFAULT_MODE
from app.search.searcher import search_documents
import asyncio

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton LLM client — created once at module import, reused per request.
# ChatGroq is thread-safe and connection-pooled; constructing it per request
# adds unnecessary auth/connection overhead.
# ---------------------------------------------------------------------------
_llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    temperature=settings.LLM_TEMPERATURE,
    model_name=settings.LLM_MODEL,
    max_retries=3,
    request_timeout=60,
)

# ---------------------------------------------------------------------------
# Helper — load the system prompt from file
# ---------------------------------------------------------------------------

def load_system_prompt() -> str:
    # Uses absolute pathing so it never misses the file
    # Path(__file__) is in app/llm/answerer.py
    # .parent -> app/llm/
    # .parent.parent -> app/
    # .parent.parent.parent -> root/
    base_dir = Path(__file__).resolve().parent.parent.parent
    prompt_path = base_dir / "prompts" / "system.txt"

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        # If we see this in the frontend, we know the Linux path is broken!
        return (
            "CRITICAL ERROR: SYSTEM.TXT NOT FOUND ON SERVER.\n\n"
            "CONTEXT:\n{context}\n\n"
            "USER QUERY: {query}\n\n"
            "FALLBACK MODE INSTRUCTIONS:\n{mode_instructions}"
        )

# ---------------------------------------------------------------------------
# Main — stream an answer from retrieved chunks
# ---------------------------------------------------------------------------

async def generate_answer_stream(query: str, subject: str, chat_history: list = None, mode: str = "Academic"):
    if chat_history is None:
        chat_history = []

    # ----- 1. Retrieve documents from ChromaDB (subject-filtered + threshold) -----
    retrieved_docs = await asyncio.to_thread(
        search_documents, query=query, subject=subject
    )

    # ----- 2. Circuit Breaker — no relevant chunks found -----
    # This also acts as the off-topic gate: queries unrelated to the subject
    # will produce no chunks above the similarity threshold.
    if not retrieved_docs:
        yield {
            "type": "content",
            "data": "I couldn't find relevant information in your course materials. "
                    "Please try rephrasing your question or make sure it relates to "
                    "your selected subject."
        }
        return

    # ----- 3. Process context and deduplicate sources -----
    context_chunks = ""
    sources_set = set()

    for doc in retrieved_docs:
        context_chunks += doc.page_content + "\n\n"
        book = doc.metadata.get("book", "Unknown")
        page = doc.metadata.get("page_number", "?")
        sources_set.add(f"{book} - Page {page}")

    sources = list(sources_set)

    # ----- 4. Format chat history into a readable string -----
    history_block = "No previous context."
    if chat_history:
        history_parts = []
        for msg in chat_history:
            role = "User" if msg.get("role") == "user" else "Assistant"
            history_parts.append(f"{role}:\n{msg.get('content')}")
        history_block = "\n\n".join(history_parts)

    # ----- 5. Build the prompt -----
    system_prompt_template = load_system_prompt()

    # Get the instructions for the selected mode. Fallback to default if somehow missing.
    active_mode_text = MODE_PROMPTS.get(mode, MODE_PROMPTS[DEFAULT_MODE])

    formatted_system_prompt = system_prompt_template.replace(
        "{mode_instructions}", active_mode_text
    ).replace(
        "{chat_history}", history_block
    ).replace(
        "{context}", context_chunks
    ).replace(
        "{query}", query
    )

    messages = [
        ("system", formatted_system_prompt),
        ("human", query),
    ]

    # ----- 6. Stream tokens one-by-one -----
    async for chunk in _llm.astream(messages):
        if chunk.content:
            yield {"type": "content", "data": chunk.content}

    # ----- 7. Send sources as the final event -----
    if sources:
        yield {"type": "sources", "data": sources}