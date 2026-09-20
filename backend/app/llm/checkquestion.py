"""
checkquestion.py - Syllabus gate: is this question allowed, and how do we rewrite it.

Pure rule-based, zero API calls, zero latency. Moved out of answerer.py
(Stage 0 split, no behaviour change).

Pipeline position:
    1. Hard reject (instant regex block for obvious non-academic queries)
    2. Strict syllabus bounce (topic word/phrase matching against YAML)
    3. Explicit syllabus check (tier 1 vs tier 2 classification)
    4. Rule-based query rewriter (no API, uses chat history)

Three-Tier Response System:
    Tier 1 - Topic explicitly in YAML syllabus -> answer normally
    Tier 2 - Topic matches subject but not in YAML -> answer with disclaimer
    Tier 3 - Topic unrelated to subject -> block completely
"""

import difflib
import logging
import re
import yaml
from functools import lru_cache
from app.config.settings import SYLLABUS_PATH, SUBJECT_NAMES

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
# Subject abbreviations — "in ML" means "in machine learning"
# ---------------------------------------------------------------------------
SUBJECT_ABBR = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "dl": "deep learning",
    "cn": "computer network",
    "qc": "quantum computing",
}

_ABBR_RE = re.compile(
    r"\b(%s)\b" % "|".join(SUBJECT_ABBR), re.IGNORECASE
)

# Typo similarity bar (difflib ratio). 0.8 catches repeated-letter
# typos like "fuzzzzy" while still blocking unrelated words.
TYPO_RATIO = 0.8


def _expand_abbr(text: str) -> str:
    """Replace whole-word subject abbreviations with full names."""
    return _ABBR_RE.sub(lambda m: SUBJECT_ABBR[m.group(0).lower()], text)


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
    query = _expand_abbr(query)

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

    # Short query (1 meaningful word) — exact match passes (e.g. "OSI", "TCP").
    # Exact only, no fuzzy, so junk like "pasta" still blocks.
    if len(meaningful_words) == 1 and len(matches) == 1:
        logger.info(
            "[Bounce] PASS (short exact match=%s) | query='%s'",
            matches, query
        )
        return True

    # Typo tolerance — a long word close to a topic word passes.
    # difflib catches deletions/insertions ("overfiting") that the
    # position-based _fuzzy_match misses. Block path only, stdlib only.
    for word in meaningful_words:
        if len(word) < 6:
            continue
        for candidate in topic_words:
            if len(candidate) < 5:
                continue
            if abs(len(word) - len(candidate)) > 2:
                continue
            if difflib.SequenceMatcher(None, word, candidate).ratio() >= TYPO_RATIO:
                logger.info(
                    "[Bounce] PASS (typo match: '%s'~'%s') | query='%s'",
                    word, candidate, query,
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

    query = _expand_abbr(query)

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

    # Typo correction — map unknown long words onto the closest topic word
    # ("overfiting" -> "overfitting") so Rules 1-4 judge intent, not spelling.
    # Only corrects words missing from topic_words; exact words untouched.
    corrected = set()
    for word in query_words:
        if word in topic_words or len(word) < 6:
            corrected.add(word)
            continue
        best, best_ratio = word, 0.0
        for candidate in topic_words:
            if len(candidate) < 5 or abs(len(word) - len(candidate)) > 2:
                continue
            ratio = difflib.SequenceMatcher(None, word, candidate).ratio()
            if ratio > best_ratio:
                best, best_ratio = candidate, ratio
        if best_ratio >= TYPO_RATIO:
            logger.info(
                "[ExplicitCheck] Typo fix: '%s' -> '%s' | query='%s'",
                word, best, query,
            )
            corrected.add(best)
        else:
            corrected.add(word)
    query_words = corrected

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
    # A single shared word (exact or plural) is not enough for Tier 1 —
    # require 2+ fuzzy hits so near-miss topics fall to Tier 2 (disclaimer).
    query_words_for_fuzzy = query_words - subject_name_words

    fuzzy_hits = [
        word for word in query_words_for_fuzzy
        # Handles "nueral" -> "neural"
        if len(word) >= 5 and _fuzzy_match(word, topic_words)
    ]
    if len(fuzzy_hits) >= 2:
        logger.info("[ExplicitCheck] PASS (fuzzy match: %s) | query='%s'", fuzzy_hits, query)
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
