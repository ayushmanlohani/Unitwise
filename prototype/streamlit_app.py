"""
streamlit_app.py — AKTU-Brain Prototype chat interface.

Run from the project root:
    streamlit run prototype/streamlit_app.py
"""

import sys
import os

# ---------------------------------------------------------------------------
# Path setup — add project root so Python can find the backend package
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(PROJECT_ROOT, "backend"))

import streamlit as st

from app.search.searcher import search_documents
from app.llm.answerer import generate_answer

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="AKTU-Brain Prototype", page_icon="🧠")

# ---------------------------------------------------------------------------
# Session state — chat history
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("🧠 AKTU-Brain Prototype")
st.caption("Ask anything about your Computer Networks syllabus.")

# Display existing chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Chat input & response
# ---------------------------------------------------------------------------
user_text = st.chat_input("Ask a question...")

if user_text:
    # ---- Show & save user message ----
    with st.chat_message("user"):
        st.markdown(user_text)

    st.session_state.messages.append({"role": "user", "content": user_text})

    # ---- Retrieve & generate ----
    with st.chat_message("assistant"):
        with st.spinner("Searching documents..."):
            chunks = search_documents(
                query=user_text,
                subject="computer_networks",
            )

        with st.spinner("Generating answer..."):
            result = generate_answer(
                query=user_text,
                retrieved_chunks=chunks,
            )

        # Display the answer
        st.markdown(result["answer"])

        # Display source citations
        if result["sources"]:
            st.divider()
            st.markdown("**📚 Sources**")
            for src in result["sources"]:
                st.markdown(f"- {src}")

    # ---- Save assistant response to state ----
    full_response = result["answer"]
    if result["sources"]:
        full_response += "\n\n**📚 Sources**\n" + "\n".join(
            f"- {src}" for src in result["sources"]
        )

    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )
