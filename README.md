<div align="center">

<img src="frontend/public/unitwise-logo.png" width="90" alt="Unitwise logo" />

# Unitwise

**A syllabus-locked study companion for B.Tech students.**

Ask a question from your course and get an exam-ready answer built from your prescribed textbooks, down to the book and page it came from.

**[Try the live demo →](https://unitwise-weld.vercel.app/)**

![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/Frontend-React%2019-61DAFB?logo=react&logoColor=black)
![Groq](https://img.shields.io/badge/LLM-gpt--oss--120b-F55036)
![ChromaDB](https://img.shields.io/badge/Vector%20Store-ChromaDB-F4643B)
![Supabase](https://img.shields.io/badge/Auth%20%2B%20DB-Supabase-3FCF8E?logo=supabase&logoColor=white)

</div>

---

https://github.com/user-attachments/assets/3eb4e046-0c9e-4117-ace8-391dd63d9d39

---

## Unitwise in 30 seconds

Exam in two days, no notes? Unitwise answers questions **strictly from the indexed syllabus** of six B.Tech subjects (Computer Networks, Digital Image Processing, Machine Learning, Soft Computing, Data Mining and Quantum Computing) and shows the textbook and page behind every answer.

- **Syllabus-locked:** off-topic questions are blocked before the LLM is ever called
- **Cited answers:** every response ships with its sources, down to the book and page
- **Five study modes:** Academic, Simplified, Exam Prep, Revision, Analogy
- **Streaming:** answers render token by token over Server-Sent Events
- **Math done right:** full LaTeX output, because PDF extraction mangles equations
- **Evaluated:** a golden test suite scores the gate, retrieval and answers on every change

This README is layered: the next few sections give you the full picture, and everything after that goes a step deeper. Read as far as you need.

---

## The complete RAG checklist

Everything a serious retrieval-augmented system needs, and where it lives in Unitwise.

| Piece | Implementation |
|---|---|
| Document ingestion | PyMuPDF page-range extraction, driven by `syllabus.yaml` |
| Chunking | `RecursiveCharacterTextSplitter`, 1000 chars with 200 overlap |
| Embeddings | `all-MiniLM-L6-v2` (384-dim, sentence-transformers) |
| Vector store | ChromaDB, persistent, cosine HNSW, subject-locked metadata filter |
| Reranking | `ms-marco-MiniLM` cross-encoder, 15 candidates down to the top 7 |
| Query guardrails | Deterministic three-tier syllabus gate, zero LLM calls, about 2 ms |
| Query rewriting | Rule-based pronoun resolution with memory hygiene |
| Generation | `openai/gpt-oss-120b` at temperature 0, five study modes |
| Citations | Book and page metadata surfaced with every answer |
| Streaming | SSE with throttled client-side rendering |
| LLM key management | Key pool with least-loaded selection and instant 429 failover |
| Rate limiting | Dual layer: per-IP plus adaptive per-user fair share |
| Evaluation | Golden-set evals: gate accuracy, chunk recall, faithfulness, citations |
| Testing | pytest suite covering the gate, key pool and rate limiter |
| Auth and persistence | Supabase: Google OAuth, email/password, chat history in Postgres |

---

## How a question flows

```
User question
   │
   ▼
FastAPI ──── per-IP rate limit (slowapi) + per-user adaptive limit
   │
   ▼
Syllabus gate ──── pure rules: hard-reject regexes, topic matching, query rewrite
   │                   off-subject → friendly block, zero LLM cost
   ▼
ChromaDB ──── retrieve 15 candidates (cosine, subject metadata filter)
   │
   ▼
Cross-encoder rerank ──── distill to the top 7 chunks
   │
   ▼
gpt-oss-120b via Groq key pool ──── answer streamed token by token over SSE
   │
   ▼
Frontend renders answer + sources ──── persisted to Supabase
```

---

## The syllabus gate, three tiers

The gate is the part most RAG demos skip. It is entirely rule-based (compiled regexes plus word and phrase matching against `syllabus.yaml`), so it costs nothing, adds about 2 ms and behaves identically on every run.

| Tier | Meaning | What the user gets |
|---|---|---|
| **1. In syllabus** | Matches a listed unit or topic | Clean answer, no noise |
| **2. Related** | On-subject but not listed | Answer plus a clear disclaimer that the topic sits outside the listed syllabus |
| **3. Off-subject** | Cookware, cricket, MBA advice, jokes | Blocked immediately, zero LLM cost |

Matching has real depth. Whole-phrase matches pass outright. Words of five or more characters need a single hit, shorter words need two, and typo tolerance (`difflib`, ratio 0.8+) lets *overfiting* and *fuzzzzy* through. Abbreviations expand (*in ML* becomes machine learning) and aliases get canonicalised (*qubit* becomes quantum bits). Study-strategy questions like *important topics for the exam* always pass.

---

## Two-stage retrieval

1. **Recall:** the query is embedded and ChromaDB returns the 15 nearest chunks, filtered strictly by subject metadata so a CN question can never pull QC pages.
2. **Precision:** a `ms-marco-MiniLM-L-6-v2` cross-encoder scores every query-chunk pair jointly and keeps the top 7. If the reranker ever fails to load or score, retrieval falls back to plain cosine order, so the answer degrades instead of erroring out.

Measured on the golden set: gate p50 is about 2 ms, retrieval plus rerank averages ~0.9 s with a p95 of ~1.4 s on CPU.

---

## Generation, five modes with one discipline

The system prompt (`prompts/system.txt`) classifies every topic before writing and enforces an exam-oriented answer structure:

- **Type A (theory):** no invented formulas, high keyword density and a mandatory diagram callout
- **Type B (math-driven):** leads with the *topic-defining* formula in LaTeX. Decision Trees get Gini and Entropy, never the Bayes formula. Quantum gates get their full matrices
- **Type C (balanced):** formula and diagram, both mandatory

Answers are **marks-aware** (2, 5 or 10-mark depth), keywords are bold-italicised throughout, and trailing "Keywords" or "References" sections are forbidden. Because PDF extraction mangles equations, the prompt explicitly authorises internal knowledge for mathematics, but only for the formula the topic is actually named after.

Each mode restyles the same grounded context:

| Mode | Behaviour |
|---|---|
| 🎓 Academic | Full textbook treatment: definition, characteristics, pros and cons |
| 💡 Simplified | Real-world analogy, zero-background friendly |
| 📝 Exam Prep | Answer shaped to the marks asked, 2-mark crisp to 10-mark full |
| ⚡ Revision | Cheat-sheet bullets, ends with "Key Points to Remember" |
| 🎭 Analogy | Complex concepts bridged to everyday objects |

---

## Follow-up memory

Follow-ups like *explain it in detail* or *what about its limitations* are resolved by rules, not another LLM call:

- The last **valid** academic answer supplies the referent, appended as *(referring to: ...)*
- Warning messages, rate-limit notes and error bubbles are filtered out of memory, so a blocked reply can never become the "topic" a follow-up points at
- If a pronoun appears with no valid topic behind it, the backend asks the user to name the topic instead of guessing

---

## Capacity engineering

**Groq key pool** (`app/key_pool.py`): up to five API keys, each budgeted at 25 requests/min and 6,400 tokens/min (80% of Groq's 8k tier). The pool always picks the key with the most token headroom, and a 429 marks that key exhausted until its window resets. The request switches to the next key instead of sleeping.

**Adaptive rate limiting** (`app/ratelimit.py`): one counter, two behaviours. A lone user gets 10 questions a minute. The moment two or more users are active in a 60-second window, everyone drops to a fair 3 per minute. Limits are keyed by the user's Supabase id. This is fair share, not security. Blocked users get a friendly in-stream message instead of an HTTP error.

---

## Evals and tests

`eval/golden.jsonl` is the contract: Tier 1, 2 and 3 questions across all six subjects plus multi-turn follow-ups, each with the expected source pages and must-contain keywords.

| Command | What it checks | Cost |
|---|---|---|
| `python -m eval.run_thin` | Gate verdicts, retrieval hits against syllabus page ranges, latency percentiles | Free |
| `python -m eval.judge` | Gate accuracy, chunk recall, answer-material proxy, latency | Free |
| `python -m eval.judge --llm` | Adds real answers: citation subset check and LLM-judged faithfulness | Groq credits |

Latest full strict run: **gate accuracy 100%, chunk recall 100%, answer-material proxy 94%** over all cases.

The tests (`pytest` from `backend/`) pin the behaviours that regressed before. Tier-2 queries that share one word with the syllabus must not pass as Tier-1. Typos must clear the bounce. The pool must pick by tokens and burn 429'd keys. The limiter must switch from solo to shared at exactly two users.

---

## Ingestion (one-time)

```
PDF textbooks → PyMuPDF page extraction (ranges from syllabus.yaml)
             → RecursiveCharacterTextSplitter (1000 / 200)
             → all-MiniLM-L6-v2 embeddings (numpy-cached, CUDA-aware)
             → ChromaDB (cosine HNSW, subject and page metadata)
```

`vector_store/` is git-ignored, so a fresh clone needs one indexing run. From `backend/`:

```python
import yaml
from app.document_index.extractor import extract_text_for_unit
from app.document_index.chunker import chunk_text
from app.document_index.indexer import index_chunks

syllabus = yaml.safe_load(open("data/syllabus.yaml", encoding="utf-8"))
chunks = []
for s in syllabus["subjects"]:
    for unit in s["units"]:
        for src in unit["sources"]:
            lo, hi = map(int, src["pages"].split("-"))
            pages = extract_text_for_unit(s["folder"], unit["number"], f"{src['book']}.pdf", lo, hi)
            chunks += chunk_text(pages)
index_chunks(chunks)
```

Re-runs skip encoding entirely when the chunk list has not changed (exact-match numpy cache). Otherwise the store is rebuilt from scratch.

---

## Project structure

```
Unitwise/
├── backend/
│   ├── main.py                    # FastAPI app: CORS, slowapi, router
│   ├── requirements.txt           # Pinned backend dependencies
│   ├── Dockerfile                 # HF Spaces deploy (port 7860)
│   ├── prompts/system.txt         # System prompt: rules, modes, math policy
│   ├── data/
│   │   ├── syllabus.yaml          # 6 subjects: units, topics, books, page ranges
│   │   └── raw/                   # Textbook PDFs, one folder per subject (add your own)
│   ├── app/
│   │   ├── api/                   # routes.py (SSE endpoint), schemas.py (validation)
│   │   ├── config/                # settings.py (all knobs), modes.py (5 mode prompts)
│   │   ├── document_index/        # extractor.py, chunker.py, indexer.py
│   │   ├── llm/                   # answerer.py (pipeline), checkquestion.py (gate)
│   │   ├── search/searcher.py     # Cosine recall + cross-encoder rerank
│   │   ├── key_pool.py            # Groq key rotation
│   │   └── ratelimit.py           # Adaptive per-user limiter
│   ├── eval/                      # golden.jsonl, run_thin.py, judge.py
│   ├── tests/                     # pytest: gate, key pool, rate limiter
│   └── vector_store/              # ChromaDB (built by ingestion, git-ignored)
│
├── frontend/
│   ├── public/                    # Logo, favicon, manifest
│   └── src/
│       ├── pages/                 # landingpage.js, Login.js, ChatDashboard.js
│       ├── components/            # sidebar, chatinput, modedropdown, chat groups
│       ├── config/                # supabaseClient.js
│       └── utils/                 # dateFormatter.js
│
├── prototype/                     # Original Streamlit prototype (kept for history)
├── .env.example
└── requirements.txt               # Includes backend deps + Streamlit for the prototype
```

---

## Run it locally

### Backend

```bash
git clone https://github.com/ayushmanlohani/Unitwise.git
cd Unitwise/backend

python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/macOS: source .venv/bin/activate)

pip install -r requirements.txt

cp ../.env.example .env           # fill in GROQ_API_KEY_1 (free key: console.groq.com)
                                  # and HUGGINGFACE_API_KEY for model downloads
```

Add textbook PDFs under `backend/data/raw/<SUBJECT>/`, point `backend/data/syllabus.yaml` at them, then run the ingestion snippet above once.

```bash
uvicorn main:app --reload         # API at http://localhost:8000
```

### Frontend

```bash
cd ../frontend
npm install

# frontend/.env
#   REACT_APP_SUPABASE_URL=...
#   REACT_APP_SUPABASE_ANON_KEY=...
#   REACT_APP_API_URL=http://localhost:8000

npm start                         # app at http://localhost:3000
```

<details>
<summary><strong>Supabase schema</strong> (tables the frontend expects)</summary>

```sql
create table chats (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  title text,
  subject text,
  is_starred boolean default false,
  created_at timestamptz default now()
);

create table messages (
  id uuid primary key default gen_random_uuid(),
  chat_id uuid references chats(id) on delete cascade,
  role text not null,
  content text not null,
  sources jsonb,
  mode text,
  created_at timestamptz default now()
);
```

</details>

---

## API reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/health` | Liveness check |
| POST | `/api/v1/ask` | Ask a question, returns an SSE stream |
| GET | `/api/v1/pool-status` | Debug: key pool usage |

**Request**

```json
{
  "query": "Explain sliding window protocols",
  "subject": "CN",
  "chat_history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}],
  "mode": "Exam Prep",
  "user_id": "supabase-uuid"
}
```

**SSE events** arrive as `data: {json}\n\n`:

| Type | Meaning |
|---|---|
| `content` | Streamed answer tokens, or gate and limit messages |
| `sources` | Final source list, one entry per chunk naming the book and page |
| `done` | Stream complete |
| `error` | Pipeline failure message |

---

## Tuning knobs

All in `backend/app/config/settings.py`:

| Knob | Default | Effect |
|---|---|---|
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 1000 / 200 | Chunking granularity |
| `CANDIDATE_TOP_K` | 15 | Cosine recall breadth |
| `FINAL_TOP_K` | 7 | Chunks sent to the LLM |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Generation model |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model |
| `MAX_TOKENS_PER_MINUTE` | 6400 | Per-key budget, 80% of tier |

---

## Deployment

| Service | Role |
|---|---|
| Vercel | Frontend hosting |
| Hugging Face Spaces | Backend, Docker on port 7860 |
| Supabase | Auth and Postgres |

Secrets are configured in each platform's environment settings, no keys live in the repo.

---

## Known limitations

- Ingestion is a full rebuild with no incremental indexing. The embedding cache keeps re-runs cheap
- The rate limiter and key pool are in-memory per process, counters reset on restart
- The gate is word and phrase matching, not a semantic classifier. It is tuned to this syllabus and English only
- `user_id` is self-reported by the frontend, fairness by design rather than security
- Sources reflect retrieval metadata, not LLM self-citation

---

## Credits

Built by **Ayushman Lohani** as a B.Tech mini-project at the University of Lucknow. For academic purposes.
