# Unitwise Upgrade Plan — RAG + Eval

## BG story
- Built Unitwise in a hurry as B.Tech mini-project. Shipped working RAG fast with simple fixes: flat 1000/200 recursive chunking, pure cosine search (`TOP_K=7` in code), regex + word-match syllabus gate, single global index.
- Now leveling it up: fix core retrieval quality first, then add eval gateway to prove pipeline finds right chunks and LLM answers without hallucination. Goal = interview-ready "RAG system with eval" story.

## Order of work
1. **Stage 0 — checkquestion split + thin golden set & latency baseline** (guard for all refactors)
2. **Stage 1 — Retrieval-lite (Cross-encoder reranker, 15 → 7)**
3. **Stage 2 — Gate tune (small)**
4. **Stage 3 — Heavy eval gateway, local-only** (very last, one-shot)
5. **Deferred — Chunking v2 & User uploads**

---

## Stage 0 — checkquestion split + thin golden set & latency baseline
- **What**: Split gate out first, then ~35 Q/A guard set. No chicken-egg: `checkquestion.py` exists before anything imports it.
- **Why**: `answerer.py` crowded. Split is move-only, zero behavior change. Golden set then guards every later stage.
- **Specifics**:
  - Step 1 — split: extract all gate helpers + `rewrite_query` + word lists (`is_in_syllabus`, `is_explicitly_in_syllabus`, `_is_hard_rejected`, `_load_subject_data`, `_normalise_words`, `_fuzzy_match`, `_OVERVIEW_PATTERNS`, `PRONOUNS`, `STOP_WORDS`, `STUDY_INTENTS`) + memory hygiene block (`_extract_last_topic`, `_is_academic_message`, `_NON_MEMORY_PREFIXES`, `_MIN_ACADEMIC_LENGTH`) into `backend/app/llm/checkquestion.py`. `answerer.py` keeps only `_load_system_prompt` + `generate_answer_stream` and imports rest. Aligns with README. Verify `pytest` + `pytest-asyncio` already in `backend/requirements.txt`. Create `backend/tests/conftest.py` with mock syllabus fixtures.
  - Step 2 — golden: new `backend/eval/golden.jsonl` (fields: `query, subject, tier, chat_history, expected_sources, must_contain`). 10 Tier-1, 10 Tier-2, 10 Tier-3, ~5 follow-ups.
  - Subjects must be in `VALID_SUBJECTS` (`CN, DIP, EML, SCT, DMW, QC`) or subject filter drops them silently.
  - Step 3 — runner + baseline: new `backend/eval/__init__.py` (empty, makes `python -m eval.run_thin` work from `backend/`), new `backend/eval/run_thin.py` (gate + search, no LLM, pass/fail per Q, imports from `checkquestion.py`). Add timing logs in `searcher.py` + `answerer.py`.
  - Fast, local. Note: first run cold-loads embedding model so >1 min; warm runs <1 min before and after every stage.

---

## Stage 1 — Retrieval-lite (Cross-encoder reranker, 15 → 7)
- **What**: Keep ChromaDB cosine search for fast candidate retrieval (15), add lightweight cross-encoder reranker down to final 7 for the LLM.
- **Why**: Cosine top-7 returns noisy near-misses; retrieve-15 + rerank-to-7 keeps recall high while context stays tight, fast, and accurate.
- **Specifics**:
  - Touch: `backend/app/search/searcher.py` + `backend/app/config/settings.py`. Replace single `TOP_K=7` with `CANDIDATE_TOP_K=15` (Chroma retrieve) and `FINAL_TOP_K=7` (reranker output to LLM). Old docs said 15 — new truth is retrieve-15/rerank-7.
  - Model: `cross-encoder/ms-marco-MiniLM-L-6-v2` (~80MB, loaded once via singleton pattern).
  - **Silent cosine fallback**: wrap reranker in try/except. On load fail or OOM, log warning and fall back to cosine top-7. No crash, zero downtime.
  - HF note: +80MB download on boot, bi-encoder + cross-encoder both in RAM. Cold start slower; warm queries must stay within +500ms budget (~200-350ms expected).
  - Validate: Stage 0 chunk-relevance hit rate must improve.
  - Interview line: *"Retrieve-15/rerank-7 with a cross-encoder for strictly higher relevance, paired with silent cosine fallback to guarantee stability on resource-constrained hosting."*

---

## Stage 2 — Gate tune (small)
- **What**: Tune the 3-tier syllabus gate in `checkquestion.py`, don't rewrite.
- **Why**: Rule-based gate is fast and cheap, but has edge-case false passes/blocks. Tuning with tests makes it robust.
- **Specifics**:
  - Touch: `backend/app/llm/checkquestion.py` (`HARD_REJECT_PATTERNS`, `STOP_WORDS`, overlap thresholds) + add `backend/tests/test_gate.py`.
  - Write failing unit tests for known edge-case queries first, then tune regex and word matching until tests pass.
  - Explicitly NOT doing: LLM classifier gate (avoids adding API cost and 1s+ latency).
  - Interview line: *"Evaluated an LLM classifier gate, but retained an optimized rule-based gate with regression test coverage to keep latency at 0ms and preserve API rate limits."*

---

## Stage 3 — Heavy eval gateway, local-only (last)
- **What**: Offline evaluation scripts with strict checks + LLM judge. No endpoint, no auth — runs on local server only, mentioned in repo for interviews. Never on user live path.
- **Why**: Quantifies retrieval accuracy and verifies the LLM answers without hallucinations. Live queries just answer + cite; this checks logs offline.
- **Specifics**:
  - New: `backend/eval/judge.py` (strict + LLM), run via `python -m eval.run_thin` / `python -m eval.judge` locally from `backend/`. No `/eval/run` endpoint. Git-track `golden.jsonl`, git-ignore `eval/results/` logs.
  - Model pinned: `openai/gpt-oss-120b` everywhere (LLaMA deferred). Update README model name when eval lands.
  - Metrics:
    - **Chunk recall**: expected pages in final top-7?
    - **Faithfulness (both)**: strict = cited `book+page` must be in retrieved top-7; LLM judge reads answer + chunks and scores claim support.
    - **Citation correctness**: strict filter first, LLM scores passers.
    - **Gate accuracy**: Tier-3 block rate and Tier-2 disclaimer rate.
    - **Latency percentiles**: p50 and p95 from Stage 0 timing logs.
  - Run on-demand (Groq cost/rate limit control).

---

## Deferred

### A. Chunking v2
- **Why deferred**: Current `RecursiveCharacterTextSplitter` (1000/200 per page, page boundaries preserved) is solid. Re-chunking = local re-index only (PDFs already in `data/raw/`, no redownload) but full re-encode for marginal gains. Reranking gives higher retrieval lift with zero re-index friction.

### B. User uploads (per-user private)
- **Why deferred**: Requires multi-tenant Chroma namespaces (`collection per user` or `user_id` metadata filtering), per-request auth scoping, and async ingestion queues. Global index stays clean.
- **Interview line**: *"Scoped design to per-user namespaces for strict tenant isolation; deferred to keep the core global syllabus index rock-solid first."*
