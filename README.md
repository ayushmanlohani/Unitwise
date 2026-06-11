# Unitwise — AI-Powered Academic Chatbot

> **Exam in 2 days? No notes?** Unitwise lets B.Tech students ask questions directly from their syllabus and get cited, textbook-accurate answers — no notes collecting, no friend calls, no guessing.

<img width="600" alt="image" src="https://github.com/user-attachments/assets/205304c6-bd19-4119-b679-59655f8b726a" />
<img width="600" alt="image" src="https://github.com/user-attachments/assets/cc8a0ca5-649b-43ed-ac5e-1fa999a81e7a" />

<img width="600" alt="image" src="https://github.com/user-attachments/assets/adf2ed33-7728-4746-a19b-678817801e0f" />



---

## What It Does

Unitwise is a **Retrieval-Augmented Generation (RAG)** chatbot built specifically for University of Lucknow B.Tech students. It answers questions strictly from the indexed syllabus and cites the exact textbook and page number for every answer.

- Ask anything from your syllabus — get a sourced answer in under 5 seconds
- Responses cite specific textbook pages (e.g., *Computer Networks — Page 45*)
- Syllabus gate blocks off-topic questions so the LLM stays focused
- Multiple answer modes: Academic, Simplified, and more
- Real-time streaming responses via Server-Sent Events

---

## Architecture

```
User Query
    │
    ▼
React Frontend (Auth via Supabase)
    │
    ▼
FastAPI Backend  →  Syllabus Gate (LLM filter via Groq)
    │                        │ off-topic → blocked
    ▼
ChromaDB Vector Store
(all-MiniLM-L6-v2 embeddings, top-15 similarity search)
    │
    ▼
LLaMA 3.1 8B via Groq API  →  SSE Stream  →  Frontend renders answer + sources
```

**Ingestion Pipeline (one-time setup):**
PDF textbooks → PyMuPDF extraction → RecursiveCharacterTextSplitter (1000 chars / 200 overlap) → Embed with all-MiniLM-L6-v2 → Store in ChromaDB (SQLite)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Tailwind CSS, Framer Motion |
| Backend | FastAPI, Uvicorn |
| LLM | LLaMA 3.1 8B Instant via Groq API |
| RAG Framework | LangChain Core, LangChain Groq |
| Vector Store | ChromaDB (SQLite-backed, persistent) |
| Embeddings | all-MiniLM-L6-v2 (Sentence Transformers, 384-dim) |
| Document Parsing | PyMuPDF |
| Auth | Supabase (PostgreSQL + Auth) |

---

## Project Structure

```
Unitwise/
├── backend/
│   ├── main.py                   # FastAPI entry point
│   ├── app/
│   │   ├── api/routes.py         # Endpoints: /health, /ask
│   │   ├── llm/answerer.py       # RAG pipeline + streaming
│   │   ├── llm/checkquestion.py  # Syllabus gate (LLM filter)
│   │   ├── search/searcher.py    # ChromaDB query interface
│   │   └── document_index/       # Extractor, chunker, indexer
│   ├── data/
│   │   ├── syllabus.yaml         # Subject/unit/topic/book config
│   │   └── raw/                  # PDF textbooks (by subject)
│   └── vector_store/             # ChromaDB SQLite (auto-created)
│
├── frontend/
│   └── src/
│       ├── pages/                # Login, ChatDashboard, Landing
│       └── components/           # ChatDashboard, CustomCursor
│
└── .env.example                  # Environment variable template
```

---

## Setup & Run

### 1. Clone the repo

```bash
git clone https://github.com/ayushmanlohani/Unitwise.git
cd Unitwise
```

### 2. Configure environment

```bash
cp .env.example .env
# Add your Groq API key inside .env
# GROQ_API_KEY=gsk_your_key_here
```

Get your free Groq API key at [console.groq.com](https://console.groq.com)

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your PDFs

Place textbook PDFs under `backend/data/raw/<subject>/` and configure `backend/data/syllabus.yaml` with subject, unit, and page range mappings.

### 5. Run ingestion (builds the vector store)

```bash
python -m backend.scripts.run_ingestion
```

### 6. Start the backend

```bash
uvicorn backend.main:app --reload
```

### 7. Start the frontend

```bash
cd frontend
npm install
npm start
```

App runs at `http://localhost:3000`

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/health` | Liveness check |
| POST | `/api/v1/ask` | Ask a question (returns SSE stream) |

**POST `/api/v1/ask` request body:**

```json
{
  "query": "What is encapsulation?",
  "subject": "CN",
  "chat_history": [],
  "mode": "Academic"
}
```

**Response (Server-Sent Events):**
- `type: "content"` — streamed tokens from LLM
- `type: "sources"` — final event with cited textbook pages
- `type: "error"` — error message if pipeline fails

---

## Known Limitations

- Metadata filtering (subject/unit) is currently disabled for testing — searches the full vector store
- No reranking; uses pure cosine similarity (top-15 chunks)
- No incremental ingestion — full re-index required on PDF updates
- Backend auth relies on frontend Supabase session only

---

## Team

Built as a B.Tech penultimate year mini-project at the University of Lucknow.

---

## License

This project is for academic purposes. Contact the team before reuse or distribution.
