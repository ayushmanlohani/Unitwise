"""
answerer.py — Generate answers using the Groq LLM based on retrieved context.

Loads a system prompt from disk, formats the retrieved chunks into a
numbered context block, and calls ChatGroq to produce a grounded answer.
"""

import os

from langchain_groq import ChatGroq

from app.config import settings


# ---------------------------------------------------------------------------
# Helper — load the system prompt from file
# ---------------------------------------------------------------------------

def load_system_prompt() -> str:
    """
    Read the system prompt from backend/prompts/system.txt.

    Returns:
        The prompt string, or a sensible fallback if the file is missing.
    """
    prompt_path = os.path.join(settings.PROMPTS_DIR, "system.txt")

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
# Main — generate an answer from retrieved chunks
# ---------------------------------------------------------------------------

async def generate_answer(query: str, retrieved_chunks: list) -> dict:
    """
    Call the Groq LLM to answer a query using retrieved document chunks.

    Args:
        query:            The user's natural-language question.
        retrieved_chunks: A list of LangChain Document objects returned by
                          the vector-store search.

    Returns:
        A dict with two keys:
            - "answer"  : the generated response text (str)
            - "sources" : a deduplicated list of source citations (list[str])
    """

    # ----- 1. Initialise the LLM -----
    llm = ChatGroq(
        model=settings.LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE,
    )

    # ----- 2. Format context from retrieved chunks -----
    context_parts = []
    sources = set()

    for i, chunk in enumerate(retrieved_chunks, start=1):
        text = chunk.page_content
        meta = chunk.metadata

        book = meta.get("book", "Unknown")
        page = meta.get("page_number", "?")

        context_parts.append(
            f"[{i}] (Source: {book}, Page {page})\n{text}"
        )
        sources.add(f"{book}, Page {page}")

    context_block = "\n\n".join(context_parts)

    # ----- 3. Build the prompt -----
    system_prompt = load_system_prompt()

    messages = [
        (
            "system",
            f"{system_prompt}\n\n"
            f"Use the following context to answer the question.\n\n"
            f"--- CONTEXT ---\n{context_block}\n--- END CONTEXT ---",
        ),
        ("human", query),
    ]

    # ----- 4. Call the LLM (async to avoid blocking the event loop) -----
    response = await llm.ainvoke(messages)

    # ----- 5. Return structured output -----
    return {
        "answer": response.content,
        "sources": sorted(sources),
    }
