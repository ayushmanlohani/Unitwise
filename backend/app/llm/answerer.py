"""
answerer.py — Generate answers using the Groq LLM based on retrieved context.

Loads a system prompt from disk, formats the retrieved chunks into a
context block, and calls ChatGroq to produce a grounded answer.
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

async def generate_answer(query: str, subject: str, chat_history: list = None) -> dict:
    """
    Call the Groq LLM to answer a query using documents retrieved from ChromaDB.

    Args:
        query:            The user's natural-language question.
        subject:          The subject/folder name used to filter the search.
        chat_history:     List of previous messages (dict with 'role' and 'content').

    Returns:
        A dict with two keys:
            - "answer"  : the generated response text (str)
            - "sources" : a deduplicated list of source citations (list[str])
    """
    if chat_history is None:
        chat_history = []

    # ----- 1. Retrieve documents from ChromaDB -----
    retrieved_docs = search_documents(query=query, subject=subject)

    # ----- 2. Process documents for context and sources -----
    context_chunks = ""
    sources_set = set()

    for doc in retrieved_docs:
        # A: Concatenate page content into a single string
        context_chunks += doc.page_content + "\n\n"
        
        # B: Extract and format metadata for citations
        book = doc.metadata.get("book", "Unknown")
        page = doc.metadata.get("page_number", "?")
        sources_set.add(f"{book} - Page {page}")

    # Convert deduplicated set back to a list
    sources = list(sources_set)

    # ----- 3. Initialise the LLM -----
    llm = ChatGroq(
        model=settings.LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE,
    )

    # ----- 4. Build the prompt -----
    system_prompt = load_system_prompt()

    # Format chat history
    history_block = "No previous context."
    if chat_history:
        history_parts = []
        for msg in chat_history:
            role = "User" if msg.get("role") == "user" else "Assistant"
            history_parts.append(f"{role}:\n{msg.get('content')}")
        history_block = "\n\n".join(history_parts)

    messages = [
        (
            "system",
            f"{system_prompt}\n\n"
            f"--- CHAT HISTORY ---\n{history_block}\n--- END CHAT HISTORY ---\n\n"
            f"Use the following context to answer the question.\n\n"
            f"--- CONTEXT ---\n{context_chunks}\n--- END CONTEXT ---",
        ),
        ("human", query),
    ]

    # ----- 5. Call the LLM (async to avoid blocking the event loop) -----
    response = await llm.ainvoke(messages)

    # ----- 6. Return structured output -----
    return {
        "answer": response.content,
        "sources": sources,
    }