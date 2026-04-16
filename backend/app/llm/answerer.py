"""
answerer.py — Generate answers using the Groq LLM via SSE streaming.

Loads a system prompt from disk, formats the retrieved chunks into a
context block, and streams ChatGroq output token-by-token.
"""

import os

from langchain_groq import ChatGroq
from app.config import settings
from app.search.searcher import search_documents


# ---------------------------------------------------------------------------
# Helper — load the system prompt from file
# ---------------------------------------------------------------------------

def load_system_prompt() -> str:
    """
    Read the system prompt from backend/prompts/system.txt.

    Returns:
        The prompt string, or a sensible fallback if the file is missing.
    """
    prompt_path = os.path.join(os.getcwd(), "prompts", "system.txt")

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    except FileNotFoundError:
        print(
            f"⚠ System prompt not found at {prompt_path}. "
            "Using fallback prompt."
        )
        return (
            "You are a helpful academic assistant. "
            "Answer strictly based on the provided context."
        )


# ---------------------------------------------------------------------------
# Main — stream an answer from retrieved chunks
# ---------------------------------------------------------------------------

async def generate_answer_stream(query: str, subject: str, chat_history: list = None):
    """
    Async generator that yields SSE event dicts token-by-token.

    Yields:
        {"type": "content", "data": "<token>"}   — for each streamed token
        {"type": "sources", "data": [list]}       — once at the end
    """
    if chat_history is None:
        chat_history = []

    # ----- 1. Retrieve documents from ChromaDB -----
    retrieved_docs = search_documents(query=query, subject=subject)

    # ----- 2. Process context and deduplicate sources -----
    context_chunks = ""
    sources_set = set()

    for doc in retrieved_docs:
        context_chunks += doc.page_content + "\n\n"

        # BUG FIX: Use the correct metadata keys from ingestion ("book" and "page_number")
        book = doc.metadata.get("book", "Unknown")
        page = doc.metadata.get("page_number", "?")
        sources_set.add(f"{book} - Page {page}")

    sources = list(sources_set)

    # ----- 3. Format chat history into a readable string -----
    history_block = "No previous context."
    if chat_history:
        history_parts = []
        for msg in chat_history:
            role = "User" if msg.get("role") == "user" else "Assistant"
            history_parts.append(f"{role}:\n{msg.get('content')}")
        history_block = "\n\n".join(history_parts)

    # ----- 4. Build the prompt -----
    # BUG FIX: Use load_system_prompt() with the absolute path from settings,
    # not a hardcoded relative path that breaks depending on CWD.
    system_prompt_template = load_system_prompt()

    # The system.txt uses {chat_history}, {context}, {query} placeholders.
    # We use .replace() instead of .format() because the prompt contains
    # literal curly braces in LaTeX examples (e.g. \frac{}{}) that crash .format().
    formatted_system_prompt = system_prompt_template.replace(
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

    # ----- 5. Initialise the LLM -----
    # BUG FIX: Pass api_key explicitly and remove model_kwargs that Groq may reject
    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        temperature=0.2,
        model_name="llama-3.1-8b-instant",
        max_retries=3,
        request_timeout=60,
    )

    # ----- 6. Stream tokens one-by-one -----
    async for chunk in llm.astream(messages):
        if chunk.content:
            yield {"type": "content", "data": chunk.content}

    # ----- 7. Send sources as the final event -----
    if sources:
        yield {"type": "sources", "data": sources}