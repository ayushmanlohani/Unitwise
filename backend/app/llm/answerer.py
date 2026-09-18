"""
answerer.py — Core pipeline. Zero external routing calls.

Pipeline:
    1. Hard reject (instant regex block for obvious non-academic queries)
    2. Strict syllabus bounce (topic word/phrase matching against YAML)
    3. Explicit syllabus check (tier 1 vs tier 2 classification)
    4. Rule-based query rewriter (no API, uses chat history)
    5. ChromaDB search (strict subject filter)
    6. Groq LLaMA stream (single LLM call)

Three-Tier Response System:
    Tier 1 — Topic explicitly in YAML syllabus → answer normally
    Tier 2 — Topic matches subject but not in YAML → answer with disclaimer
    Tier 3 — Topic unrelated to subject → block completely
"""

import asyncio
import logging
import re
import yaml
from pathlib import Path
from functools import lru_cache
from langchain_groq import ChatGroq
from app.config.settings import (
    GROQ_MODEL,
    SYLLABUS_PATH,
    SUBJECT_NAMES,
    VALID_SUBJECTS,
)
from app.config.modes import MODE_PROMPTS, DEFAULT_MODE
from app.search.searcher import search_documents
from app.key_pool import MAX_REQUESTS_PER_MINUTE, get_pool_manager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pronouns that trigger query rewriting
# ---------------------------------------------------------------------------
PRONOUNS = {
    "it", "this", "that", "these", "those", "they", "them",
    "its", "their", "such", "above", "following", "mentioned",
}

# ---------------------------------------------------------------------------
# Study intent words — always pass bounce AND explicit check
# ---------------------------------------------------------------------------
STUDY_INTENTS = {
    "important", "topics", "exam", "marks", "unit", "chapter",
    "notes", "summary", "syllabus", "prepare", "preparation",
    "revision", "revise", "score", "pass", "questions", "asked",
    "frequently", "plan", "strategy", "tips",
}

# ---------------------------------------------------------------------------
# Stop words — removed before matching
# ---------------------------------------------------------------------------
STOP_WORDS = {
    "what", "when", "where", "which", "who", "whom", "how",
    "explain", "define", "describe", "tell", "give", "list",
    "with", "from", "about", "some", "more", "does", "have",
    "will", "been", "than", "then", "into", "over", "also",
    "is", "are", "was", "were", "the", "and", "for", "that",
    "this", "not", "but", "can", "your", "has", "very", "just",
    "both", "each", "few", "most", "other", "too", "because",
    "while", "use", "used", "using", "based", "between", "do",
    "get", "make", "like", "know", "need", "want", "help",
}

# ---------------------------------------------------------------------------
# Hard reject patterns — block BEFORE any syllabus check
# Extended to cover domestic/lifestyle topics
# ---------------------------------------------------------------------------
HARD_REJECT_PATTERNS = [
    # Degrees and career
    r"\b(how to|how do i|how can i).{0,30}(mba|degree|job|admission|scholarship|college|university admission)\b",
    r"\b(mba|master of business administration)\b",
    r"\bcareer (advice|tips|guidance|path|change)\b",
    r"\b(salary|income|earnings|pay scale)\b",
    # Domestic / lifestyle
    r"\b(cook|recipe|bake|food|restaurant|cuisine|dish|meal|ingredient)\b",
    r"\b(iron|ironing|laundry|wash clothes|dry cleaning)\b",
    r"\b(dry feet|skin care|hair care|beauty|makeup|fashion|clothing)\b",
    r"\b(relationship|dating|marriage|divorce|breakup)\b",
    r"\b(pet|dog|cat|animal care)\b",
    r"\b(garden|plant|flower|agriculture)\b",
    # Entertainment
    r"\b(politics|election|vote|government policy)\b",
    r"\b(cricket|football|soccer|basketball|tennis|sports score)\b",
    r"\b(movie|film|series|netflix|tv show|anime|drama)\b",
    r"\b(music|song|singer|actor|celebrity|gossip)\b",
    # Finance
    r"\b(weather|forecast|temperature today)\b",
    r"\b(stock market|investment|crypto|bitcoin|trading)\b",
    # Casual
    r"\b(joke|tell me a joke|funny|meme)\b",
    r"\bhow (are you|is your day|do you feel|old are you)\b",
    r"\b(what is your name|who are you|are you human|are you ai)\b",
]

_COMPILED_REJECTS = [re.compile(p, re.IGNORECASE) for p in HARD_REJECT_PATTERNS]


def _is_hard_rejected(query: str) -> bool:
    """Check against hard reject patterns. Instant, no API."""
    for pattern in _COMPILED_REJECTS:
        if pattern.search(query):
            logger.info("[HardReject] Blocked: '%s'", query)
            return True
    return False


# ---------------------------------------------------------------------------
# Syllabus loader — cached per subject, reads disk exactly once
# ---------------------------------------------------------------------------
@lru_cache(maxsize=10)
def _load_subject_data(subject_code: str) -> dict:
    """
    Load and cache syllabus data for one subject.
    Returns:
        topic_words:   individual words from all topics (broad bounce)
        topic_phrases: full topic strings (explicit syllabus check)
        subject_name:  human readable name
    """
    try:
        with open(SYLLABUS_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for s in data.get("subjects", []):
            if s.get("folder") == subject_code:
                topic_phrases = []
                topic_words = set()

                for unit in s.get("units", []):
                    unit_title = unit.get("title", "")
                    topic_phrases.append(unit_title.lower())

                    for word in re.split(r"\W+", unit_title.lower()):
                        if len(word) > 1:
                            topic_words.add(word)

                    for topic in unit.get("topics", []):
                        topic_phrases.append(topic.lower())
                        for word in re.split(r"\W+", topic.lower()):
                            if len(word) > 1:
                                topic_words.add(word)

                return {
                    "topic_words": topic_words,
                    "topic_phrases": topic_phrases,
                    "subject_name": s.get("name", subject_code),
                }

    except Exception as e:
        logger.error("Failed to load syllabus for %s: %s", subject_code, e)

    return {
        "topic_words": set(),
        "topic_phrases": [],
        "subject_name": subject_code,
    }


# ---------------------------------------------------------------------------
# Broad Syllabus Bounce — Tier 3 gate (block or allow)
# ---------------------------------------------------------------------------
def is_in_syllabus(query: str, subject_code: str) -> bool:
    """
    Broad check: does this query belong to this subject at all?

    Stronger matching rules:
    - Short words (< 5 chars) need at least 2 matches to pass
    - Long words (>= 5 chars) only need 1 match to pass
    - Phrase matches always pass
    """
    subject_name = SUBJECT_NAMES.get(subject_code, subject_code)
    query = re.sub(r'\bsubject\b', subject_name, query, flags=re.IGNORECASE)

    query_lower = query.lower()
    query_words = set(re.split(r"\W+", query_lower))

    # Always allow study strategy queries
    if query_words & STUDY_INTENTS:
        logger.info("[Bounce] PASS (study intent) | query='%s'", query)
        return True

    subject_data = _load_subject_data(subject_code)
    topic_words = subject_data["topic_words"]
    topic_phrases = subject_data["topic_phrases"]

    # Remove stop words and pronouns
    meaningful_words = query_words - STOP_WORDS - PRONOUNS
    meaningful_words = {w for w in meaningful_words if len(w) > 1}

    if not meaningful_words:
        logger.info("[Bounce] PASS (no meaningful words) | query='%s'", query)
        return True

    # Phrase match — strongest signal
    for phrase in topic_phrases:
        phrase_words = set(re.split(r"\W+", phrase)) - STOP_WORDS
        phrase_words = {w for w in phrase_words if len(w) > 1}
        if len(phrase_words) >= 2 and phrase_words.issubset(meaningful_words):
            logger.info(
                "[Bounce] PASS (phrase match: '%s') | query='%s'", phrase, query
            )
            return True

    matches = meaningful_words & topic_words

    # Long words (>= 5 chars) — 1 match is sufficient (specific technical terms)
    strong_matches = {w for w in matches if len(w) >= 5}
    if len(strong_matches) >= 1:
        logger.info(
            "[Bounce] PASS (strong word match=%s) | query='%s'",
            strong_matches, query
        )
        return True

    # Short words (< 5 chars) — need at least 2 matches (too generic alone)
    weak_matches = {w for w in matches if len(w) < 5}
    if len(weak_matches) >= 2:
        logger.info(
            "[Bounce] PASS (2x weak match=%s) | query='%s'",
            weak_matches, query
        )
        return True

    logger.info(
        "[Bounce] BLOCK | matches=%s | meaningful=%s | query='%s'",
        matches, meaningful_words, query,
    )
    return False


# ---------------------------------------------------------------------------
# Fuzzy word matcher — handles common misspellings
# ---------------------------------------------------------------------------
def _fuzzy_match(word: str, candidates: set, max_distance: int = 1) -> bool:
    """
    Check if word is within edit distance of any candidate.
    Handles common typos like 'nueral' vs 'neural'.
    Only applied to words >= 5 chars to avoid false positives.
    """
    if len(word) < 5:
        return word in candidates

    for candidate in candidates:
        if len(candidate) < 4:
            continue
        # Simple edit distance check
        if abs(len(word) - len(candidate)) > max_distance:
            continue
        # Count character differences
        differences = sum(
            1 for a, b in zip(word, candidate) if a != b
        ) + abs(len(word) - len(candidate))
        if differences <= max_distance:
            return True
    return False


# ---------------------------------------------------------------------------
# Explicit Syllabus Check — Tier 1 vs Tier 2 classification
# ---------------------------------------------------------------------------
def _normalise_words(text: str) -> set:
    """Normalise text into comparable word set."""
    words = set(re.split(r"\W+", text.lower()))
    words = words - STOP_WORDS - PRONOUNS
    return {w for w in words if len(w) > 1}


# Overview patterns — always Tier 1
_OVERVIEW_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r"\bwhat is (this )?subject\b",
    r"\bwhat does (this )?subject (contain|cover|include)\b",
    r"\babout (this )?subject\b",
    r"\boverview of (this )?subject\b",
    r"\bintroduction to (this )?subject\b",
    r"\bwhat (is|are) (soft computing techniques|computer network|digital image processing|essentials of machine learning|data mining and warehousing|quantum computing)\b",
]]


def is_explicitly_in_syllabus(query: str, subject_code: str) -> bool:
    """
    Tier 1 check: does the query match an actual YAML topic phrase?
    Returns True  → Tier 1 (answer normally, no disclaimer)
    Returns False → Tier 2 (answer with disclaimer)
    """
    # 1. Study intent — always Tier 1
    query_words_raw = set(query.lower().split())
    if query_words_raw & STUDY_INTENTS:
        logger.info("[ExplicitCheck] PASS (study intent) | query='%s'", query)
        return True

    # 2. Overview patterns — always Tier 1
    for pattern in _OVERVIEW_PATTERNS:
        if pattern.search(query):
            logger.info("[ExplicitCheck] PASS (overview pattern) | query='%s'", query)
            return True

    # 3. Subject Data Preparation
    subject_name = SUBJECT_NAMES.get(subject_code, subject_code)
    # Important: normalized subject words are used to strip injected context
    subject_name_words = _normalise_words(subject_name) 
    
    subject_data = _load_subject_data(subject_code)
    topic_phrases = subject_data["topic_phrases"]
    topic_words = subject_data["topic_words"]
    
    # Normalize query (this removes stop words/pronouns)
    query_words = _normalise_words(query)

    if not query_words:
        return True

    # 4. Phrase Matching (Rules 1-4)
    for phrase in topic_phrases:
        phrase_words = _normalise_words(phrase)
        if not phrase_words:
            continue

        # Rule 1 & 2: Structural matches (Exact or subset)
        if phrase_words.issubset(query_words) or query_words.issubset(phrase_words):
            logger.info("[ExplicitCheck] PASS (structural match) | query='%s'", query)
            return True

        # Rule 3: Significant overlap
        overlap_count = len(query_words & phrase_words)
        if overlap_count >= 2:
            logger.info("[ExplicitCheck] PASS (overlap=%d) | query='%s'", overlap_count, query)
            return True

        # Rule 4: Short query (1-2 words). 
        # FIX: We only allow 1-word overlap IF that word isn't just the subject name word.
        if len(query_words) <= 2 and overlap_count >= 1:
            meaningful_overlap = (query_words & phrase_words) - subject_name_words
            if meaningful_overlap:
                logger.info("[ExplicitCheck] PASS (short query match) | query='%s'", query)
                return True

    # 5. Rule 5: Fuzzy match (Misspellings)
    # FIX: Strip injected subject words ("computer", "network") so they don't 
    # trigger a false Tier 1 pass on a Tier 2 query.
    query_words_for_fuzzy = query_words - subject_name_words

    for word in query_words_for_fuzzy:
        # Handles "nueral" -> "neural"
        if len(word) >= 5 and _fuzzy_match(word, topic_words):
            logger.info("[ExplicitCheck] PASS (fuzzy match: %s) | query='%s'", word, query)
            return True

    logger.info("[ExplicitCheck] FAIL (Tier 2) | query='%s'", query)
    return False


# ---------------------------------------------------------------------------
# Memory hygiene — filter non-academic messages from history
# ---------------------------------------------------------------------------
_NON_MEMORY_PREFIXES = (
    "i can only help",
    "your question doesn't",
    "i couldn't find",
    "⚠️",
    "please wait",
    "high traffic",
    "rate limit",
    "something went wrong",
    "please mention the topic",
    "try rephrasing",
    "i specialize",
    "doesn't appear to be related",
    "could you mention",
    "usage is very high",
    "not explicitly listed",
)

_MIN_ACADEMIC_LENGTH = 150


def _is_academic_message(content: str) -> bool:
    """Returns True only if message is a real academic answer."""
    if not content or len(content.strip()) < _MIN_ACADEMIC_LENGTH:
        return False
    content_lower = content.strip().lower()
    for prefix in _NON_MEMORY_PREFIXES:
        if content_lower.startswith(prefix) or prefix in content_lower[:200]:
            return False
    return True


def _extract_last_topic(chat_history: list) -> str:
    """
    Extract most recent ACADEMIC topic from chat history.
    Skips all warnings, declines, errors, and system messages.
    """
    for msg in reversed(chat_history):
        if msg.get("role") == "assistant":
            content = msg.get("content", "").strip()
            if _is_academic_message(content):
                first_sentence = re.split(r"[.!?\n]", content)[0].strip()
                logger.info(
                    "[Memory] Valid topic found: '%s'", first_sentence[:60]
                )
                return first_sentence[:100]

    logger.info("[Memory] No valid academic message found in history.")
    return ""


# ---------------------------------------------------------------------------
# Rule-based Query Rewriter
# ---------------------------------------------------------------------------
def rewrite_query(query: str, chat_history: list, subject: str) -> str:
    subject_name = SUBJECT_NAMES.get(subject, subject)

    # Replace generic "subject" with actual subject name
    query = re.sub(r'\bsubject\b', subject_name, query, flags=re.IGNORECASE)

    query_words = set(query.lower().split())
    has_pronoun = bool(query_words & PRONOUNS)

    # Case 1: Follow-up with pronoun
    if has_pronoun and chat_history:
        last_topic = _extract_last_topic(chat_history)
        if last_topic:
            rewritten = f"{query} (referring to: {last_topic}) in {subject_name}"
            logger.info(
                "[Rewriter] Pronoun resolved | '%s' -> '%s'", query, rewritten
            )
            return rewritten
        else:
            logger.info(
                "[Rewriter] Pronoun with no valid history | query='%s'", query
            )
            return "CLARIFY_NEEDED"

    # Case 2: Subject already present
    if subject_name.lower() in query.lower() or subject.lower() in query.lower():
        logger.info("[Rewriter] Subject already present | query='%s'", query)
        return query

    # Case 3: Standard — inject subject
    rewritten = f"{query} in {subject_name}"
    logger.info("[Rewriter] Injected subject | '%s' -> '%s'", query, rewritten)
    return rewritten


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

    # ----------------------------------------------------------------
    # SEARCH
    # ----------------------------------------------------------------
    retrieved_docs = await asyncio.to_thread(
        search_documents, query=standalone, subject=subject
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
    yield {"type": "sources", "data": sources}
    yield {"type": "done", "data": ""}