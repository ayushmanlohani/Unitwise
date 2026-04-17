import asyncio
from pathlib import Path
from langchain_groq import ChatGroq
from app.config import settings
from app.search.searcher import search_documents
from app.llm.checkquestion import is_question_in_syllabus

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

        return (
            "You are a strict academic assistant. You MUST ONLY answer questions "
            "based on the provided context.\n\n"
            "CONTEXT:\n{context}\n\n"
            "USER QUERY: {query}\n\n"
            "If the context does not contain the answer, reply exactly with: "
            "'I can only answer questions related to your engineering syllabus.'"
        )

# ---------------------------------------------------------------------------
# Main — stream an answer from retrieved chunks
# ---------------------------------------------------------------------------

async def generate_answer_stream(query: str, subject: str, chat_history: list = None, mode: str = "Academic"):
    if chat_history is None:
        chat_history = []

    # ----- 0. Syllabus Gate — runs in a thread to avoid blocking the event loop -----
    syllabus_valid = await asyncio.to_thread(
        is_question_in_syllabus, query=query, subject=subject
    )

    if not syllabus_valid:
        # ── HARD EXIT: Yield decline and terminate the generator ──
        yield {
            "type": "content",
            "data": "I specialize in helping you with your syllabus topics. "
                    "Please ask a question related to your selected engineering subject."
        }
        # Nothing below this point can execute — the generator ends here.
        return


    # ----- 1. Retrieve documents from ChromaDB -----
    retrieved_docs = await asyncio.to_thread(
        search_documents, query=query, subject=subject
    )

    # ----- 2. Circuit Breaker (Kill Switch) -----
    if not retrieved_docs:
        yield {
            "type": "content",
            "data": "I couldn't find relevant information in your course materials. "
                    "Please try rephrasing your question."
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

    # ----- 6. Initialise the LLM -----
    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        temperature=0.0,
        model_name="llama-3.1-8b-instant",
        max_retries=3,
        request_timeout=60,
    )

    # ----- 7. Stream tokens one-by-one -----
    async for chunk in llm.astream(messages):
        if chunk.content:
            yield {"type": "content", "data": chunk.content}

    # ----- 8. Send sources as the final event -----
    if sources:
        yield {"type": "sources", "data": sources}