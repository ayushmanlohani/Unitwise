"""
judge.py — Heavy eval gateway, local-only. Never on user live path.

Strict checks run by default (no API cost):
    1. Gate accuracy: verdict matches expected tier (Tier-3 must block).
    2. Chunk recall: expected book+page present in final top-7?
    3. Answer-material proxy: must_contain word appears in retrieved chunks?
       (Tier-3 checks the block reply instead — no search runs.)
    4. Latency: gate/search p50 + p95.

Optional LLM pass (--llm, on-demand Groq cost):
    5. Generates one answer per non-blocked query with gpt-oss-120b,
       using the same chunks the live pipeline sends to the LLM.
    6. Citation correctness (strict): every cited book+page must be a
       subset of the retrieved top-7.
    7. Faithfulness (LLM judge): one temperature-0 call scores whether
       all answer claims are backed by the chunks. PASS/FAIL only.

Run from backend/ so `app.*` imports resolve:
    python -m eval.judge              # strict only, free
    python -m eval.judge --llm        # + Groq answers + LLM judge
    python -m eval.judge --llm --limit 5 --subject CN

Results go to eval/results/judge_<timestamp>.json (git-ignored).
Golden file stays git-tracked as the contract.
"""

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

from eval.run_thin import (
    BLOCKED,
    gate_verdict,
    load_golden,
    percentile,
    source_hits,
)
from app.config.settings import GROQ_MODEL
from app.search.searcher import search_documents

RESULTS_DIR = Path(__file__).resolve().parent / "results"
BLOCK_REPLY = "I can only help with"


def chunk_text(docs: list) -> str:
    """Join retrieved chunk text for proxy + LLM checks."""
    return "\n\n".join(d.page_content for d in docs)


def must_in_chunks(must_list: list, text: str) -> bool:
    """Strict proxy: every must_contain word appears in retrieved chunks?"""
    lowered = text.lower()
    return all(m.lower() in lowered for m in must_list)


def retrieved_sources(docs: list) -> set:
    """Set of (book, page) pairs in the final top-7."""
    out = set()
    for doc in docs:
        meta = doc.metadata
        book = meta.get("book")
        page = meta.get("page_number")
        if book is not None and page is not None:
            out.add((book, page))
    return out


def cited_sources(answer: str) -> set:
    """Parse 'Book.pdf — Page N' cites from an answer. Empty set if none."""
    found = set()
    for book, page in re.findall(
        r"([\w\-.]+\.pdf)\s*[—\-–,]\s*[Pp]age\s*(\d+)", answer
    ):
        found.add((book, int(page)))
    return found


def citation_subset(answer: str, docs: list) -> bool:
    """Strict citation check: every cite must come from the top-7. No cites = True."""
    cited = cited_sources(answer)
    if not cited:
        return True
    return cited.issubset(retrieved_sources(docs))


def _groq_key(slot: int) -> str:
    """Round-robin over the key pool so eval spreads TPM across keys."""
    from app.config.settings import get_groq_keys

    keys = get_groq_keys()
    return keys[slot % len(keys)]


def _call_with_retry(make_call, slot: int):
    """One retry on 429: wait out the minute window, try the next key."""
    import time as _time

    try:
        return make_call(slot)
    except Exception as e:
        if "429" not in str(e):
            raise
        _time.sleep(65)
        return make_call(slot + 1)


def generate_answer(query: str, docs: list, slot: int) -> str:
    """One Groq answer call using the same chunks as the live pipeline."""
    from langchain_groq import ChatGroq
    from app.config.settings import get_groq_keys

    labeled = []
    for doc in docs:
        meta = doc.metadata
        labeled.append(
            "SOURCE: %s page %s\n%s"
            % (meta.get("book", "Unknown"), meta.get("page_number", "?"), doc.page_content)
        )
    context = "\n\n".join(labeled)

    def _ask(slot: int) -> str:
        llm = ChatGroq(
            api_key=_groq_key(slot),
            model_name=GROQ_MODEL,
            temperature=0.0,
            max_retries=2,
            timeout=60,
        )
        messages = [
            (
                "system",
                "Answer only from the context below. Each chunk starts with "
                "a SOURCE line giving the exact file name and page. Cite "
                "every fact as 'FileName.pdf - Page N' copying the SOURCE "
                "line exactly. If the context lacks the answer, say so."
                "\n\nCONTEXT:\n" + context,
            ),
            ("human", query),
        ]
        return llm.invoke(messages).content or ""

    return _call_with_retry(_ask, slot)


def llm_faithfulness(query: str, answer: str, docs: list, slot: int) -> str:
    """One temperature-0 judge call. Returns PASS, FAIL, or ERROR."""
    from langchain_groq import ChatGroq

    def _judge(slot: int) -> str:
        llm = ChatGroq(
            api_key=_groq_key(slot),
            model_name=GROQ_MODEL,
            temperature=0.0,
            max_retries=1,
            timeout=60,
        )
        verdict = llm.invoke(
            [
                (
                    "system",
                    "You score faithfulness. Reply with exactly one word: "
                    "PASS if every claim in the answer is backed by the chunks, "
                    "else FAIL.",
                ),
                (
                    "human",
                    "QUERY:\n%s\n\nANSWER:\n%s\n\nCHUNKS:\n%s"
                    % (query, answer, chunk_text(docs)[:12000]),
                ),
            ]
        ).content.strip().upper()
        return "PASS" if "PASS" in verdict else ("FAIL" if "FAIL" in verdict else "ERROR")

    return _call_with_retry(_judge, slot)


def main() -> int:
    parser = argparse.ArgumentParser(description="Unitwise heavy eval gateway (local-only)")
    parser.add_argument("--llm", action="store_true", help="Also run Groq answers + LLM judge (costs API)")
    parser.add_argument("--limit", type=int, default=0, help="Only score first N golden rows (0 = all)")
    parser.add_argument("--subject", default="", help="Only score one subject, e.g. CN")
    args = parser.parse_args()

    entries = load_golden()
    if args.subject:
        entries = [e for e in entries if e["subject"] == args.subject]
    if args.limit > 0:
        entries = entries[: args.limit]

    print("Unitwise heavy judge - strict%s" % (" + LLM" if args.llm else " only, no API"))
    print("Golden rows: %d | model: %s" % (len(entries), GROQ_MODEL))
    print("")

    rows = []
    gate_ok_n = recall_ok_n = proxy_ok_n = 0
    cite_ok_n = faith_ok_n = llm_n = 0
    gate_times, search_times = [], []
    recall_sum, recall_n = 0.0, 0

    for index, entry in enumerate(entries, start=1):
        query = entry["query"]
        subject = entry["subject"]
        tier = entry["tier"]
        expected = entry.get("expected_sources") or []
        must = entry.get("must_contain") or []

        started = time.perf_counter()
        standalone, verdict = gate_verdict(query, subject, entry.get("chat_history") or [])
        gate_ms = (time.perf_counter() - started) * 1000
        gate_times.append(gate_ms)

        gate_ok = (verdict in BLOCKED) if tier == 3 else (verdict == tier)

        row = {
            "index": index,
            "query": query,
            "subject": subject,
            "tier": tier,
            "verdict": verdict if isinstance(verdict, str) else int(verdict),
            "gate_ok": bool(gate_ok),
        }

        if verdict in BLOCKED:
            # Tier-3: no search runs live either — the block reply IS the
            # contract. Golden Tier-3 rows carry must_contain with the
            # reply text, so strict proxy = contract words match reply.
            proxy_ok = all(m in BLOCK_REPLY for m in must)
            row.update({"blocked_by": verdict, "recall": None, "proxy_ok": bool(proxy_ok)})
            recall_ok = True
        else:
            search_started = time.perf_counter()
            docs = search_documents(standalone, subject)
            search_ms = (time.perf_counter() - search_started) * 1000
            search_times.append(search_ms)
            row["search_ms"] = round(search_ms, 1)

            if expected:
                hits = source_hits(docs, expected)
                recall = hits / len(expected)
                recall_ok = hits > 0
                recall_sum += recall
                recall_n += 1
                row.update({"recall": round(recall, 3), "hits": "%d/%d" % (hits, len(expected))})
            else:
                # Tier-2 rows carry no expected pages: recall = got anything?
                recall_ok = len(docs) > 0
                row.update({"recall": None, "chunks": len(docs)})

            text = chunk_text(docs)
            proxy_ok = must_in_chunks(must, text)
            row["proxy_ok"] = bool(proxy_ok)

            if args.llm:
                try:
                    answer = generate_answer(standalone, docs, llm_n * 2)
                    row["answer_chars"] = len(answer)
                    row["answer_excerpt"] = answer[:1500]
                    row["must_in_answer"] = bool(must_in_chunks(must, answer))
                    row["citation_ok"] = bool(citation_subset(answer, docs))
                    row["faithfulness"] = llm_faithfulness(standalone, answer, docs, llm_n * 2 + 1)
                    llm_n += 1
                    cite_ok_n += 1 if row["citation_ok"] else 0
                    faith_ok_n += 1 if row["faithfulness"] == "PASS" else 0
                except Exception as e:
                    row["llm_error"] = str(e)[:200]

        gate_ok_n += 1 if gate_ok else 0
        recall_ok_n += 1 if recall_ok else 0
        proxy_ok_n += 1 if proxy_ok else 0
        row.update({"recall_ok": bool(recall_ok), "gate_ms": round(gate_ms, 1)})
        rows.append(row)

        flag = "PASS" if (gate_ok and recall_ok and proxy_ok) else "FAIL"
        print("[%02d] %s tier=%d -> %s | recall=%s proxy=%s" % (
            index, flag, tier, row["verdict"],
            row.get("hits", row.get("chunks", "blocked")),
            "ok" if proxy_ok else "MISS",
        ))

    total = len(rows)
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / ("judge_%s.json" % stamp)
    summary = {
        "timestamp": stamp,
        "model": GROQ_MODEL,
        "llm_pass": bool(args.llm),
        "total": total,
        "gate_accuracy": round(gate_ok_n / total, 3) if total else 0.0,
        "chunk_recall_pass_rate": round(recall_ok_n / total, 3) if total else 0.0,
        "mean_recall": round(recall_sum / recall_n, 3) if recall_n else 0.0,
        "answer_material_proxy": round(proxy_ok_n / total, 3) if total else 0.0,
        "gate_p50_ms": round(percentile(gate_times, 50), 1),
        "gate_p95_ms": round(percentile(gate_times, 95), 1),
        "search_p50_ms": round(percentile(search_times, 50), 1),
        "search_p95_ms": round(percentile(search_times, 95), 1),
    }
    if args.llm and llm_n:
        summary.update({
            "llm_rows": llm_n,
            "citation_pass_rate": round(cite_ok_n / llm_n, 3),
            "faithfulness_pass_rate": round(faith_ok_n / llm_n, 3),
        })
    out_path.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2), encoding="utf-8")

    print("")
    print("Summary")
    for key, value in summary.items():
        print("  %s: %s" % (key, value))
    print("  results: %s" % out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
