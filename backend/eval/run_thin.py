"""
run_thin.py — Thin eval: gate + search only. No LLM, no API cost.

Reads eval/golden.jsonl and checks, per question:
    1. Gate verdict matches the expected tier
    2. Retrieval brings back an expected source (book + page range)
    3. Retrieval brings back anything at all for the subject

Ground truth for expected_sources comes from the page ranges declared in
data/syllabus.yaml, never from what search happens to return — otherwise the
baseline would pass on day one and prove nothing.

must_contain is NOT checked here: it needs the answer text, so it belongs to
the Stage 3 judge. It stays in the golden file as the contract.

Run from backend/ so `app.*` imports resolve:
    python -m eval.run_thin
"""

import json
import time
from pathlib import Path

from app.llm.checkquestion import (
    _is_hard_rejected,
    is_explicitly_in_syllabus,
    is_in_syllabus,
    rewrite_query,
)
from app.search.searcher import search_documents

GOLDEN_PATH = Path(__file__).resolve().parent / "golden.jsonl"

# Gate verdicts that mean "the LLM must never be reached".
BLOCKED = ("hard_reject", "bounce_block", "clarify")


def gate_verdict(query: str, subject: str, chat_history: list) -> tuple:
    """
    Replay the gate in the same order as answerer.generate_answer_stream.

    Returns (standalone_query_or_None, verdict) where verdict is 1, 2 or one
    of BLOCKED.
    """
    if _is_hard_rejected(query):
        return None, "hard_reject"

    if not chat_history:
        if not is_in_syllabus(query, subject):
            return None, "bounce_block"
        explicit = is_explicitly_in_syllabus(query, subject)
        return rewrite_query(query, chat_history, subject), (1 if explicit else 2)

    standalone = rewrite_query(query, chat_history, subject)

    if standalone == "CLARIFY_NEEDED":
        return None, "clarify"
    if _is_hard_rejected(standalone):
        return None, "hard_reject"
    if not is_in_syllabus(standalone, subject):
        return None, "bounce_block"

    explicit = is_explicitly_in_syllabus(standalone, subject)
    return standalone, (1 if explicit else 2)


def source_hits(docs: list, expected_sources: list) -> int:
    """How many of the expected sources turned up in the retrieved docs."""
    hits = 0
    for expected in expected_sources:
        for doc in docs:
            meta = doc.metadata
            if meta.get("book") != expected["book"]:
                continue
            page = meta.get("page_number")
            if page is None:
                continue
            low, high = expected["pages"]
            if low <= page <= high:
                hits += 1
                break
    return hits


def percentile(values: list, pct: int) -> float:
    """Nearest-rank percentile — no numpy needed for a 35 row eval."""
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, min(len(ordered), round(pct / 100 * len(ordered))))
    return ordered[rank - 1]


def load_golden() -> list:
    with open(GOLDEN_PATH, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> int:
    entries = load_golden()
    print("Unitwise thin eval - gate + search, no LLM")
    print("Golden: %s (%d questions)" % (GOLDEN_PATH, len(entries)))
    print("")

    gate_pass = 0
    retrieval_pass = 0
    overall_pass = 0
    gate_times = []
    search_times = []

    for index, entry in enumerate(entries, start=1):
        query = entry["query"]
        subject = entry["subject"]
        expected_tier = entry["tier"]
        expected_sources = entry.get("expected_sources") or []

        started = time.perf_counter()
        standalone, verdict = gate_verdict(
            query, subject, entry.get("chat_history") or []
        )
        gate_ms = (time.perf_counter() - started) * 1000
        gate_times.append(gate_ms)

        if expected_tier == 3:
            gate_ok = verdict in BLOCKED
        else:
            gate_ok = verdict == expected_tier

        search_ms = 0.0
        if verdict in BLOCKED:
            search_ok = True
            detail = "blocked by %s" % verdict
        else:
            search_started = time.perf_counter()
            docs = search_documents(standalone, subject)
            search_ms = (time.perf_counter() - search_started) * 1000
            search_times.append(search_ms)

            if expected_sources:
                hits = source_hits(docs, expected_sources)
                search_ok = hits > 0
                detail = "expected sources %d/%d" % (hits, len(expected_sources))
            else:
                search_ok = len(docs) > 0
                detail = "%d chunks, no expected source" % len(docs)

        passed = gate_ok and search_ok
        gate_pass += 1 if gate_ok else 0
        retrieval_pass += 1 if search_ok else 0
        overall_pass += 1 if passed else 0

        verdict_label = verdict if isinstance(verdict, str) else "tier%d" % verdict
        print(
            "[%02d] %s tier=%d -> %s | %s | %.0fms | %s"
            % (
                index,
                "PASS" if passed else "FAIL",
                expected_tier,
                verdict_label,
                subject,
                gate_ms + search_ms,
                detail,
            )
        )
        print("     %s" % query)

    total = len(entries)
    print("")
    print("Summary")
    print("  gate      : %d/%d" % (gate_pass, total))
    print("  retrieval : %d/%d" % (retrieval_pass, total))
    print("  overall   : %d/%d" % (overall_pass, total))
    print(
        "  latency   : gate p50=%.0fms p95=%.0fms | search p50=%.0fms p95=%.0fms"
        % (
            percentile(gate_times, 50),
            percentile(gate_times, 95),
            percentile(search_times, 50),
            percentile(search_times, 95),
        )
    )

    return 0 if overall_pass == total else 1


if __name__ == "__main__":
    raise SystemExit(main())