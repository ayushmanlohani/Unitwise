# Unitwise Workflow

## Setup
- `backend/` = working copy, mirrors HF Space (`ayushmanlohani/unitwise-b`).
- Old GitHub backend replaced by the HF backend. GitHub now aligns with HF.
- Nested git: `backend/.git` pushes to HF only. Outer repo pushes to GitHub.

## Local dev
- Backend: `uvicorn main:app --reload` in `backend/` → `localhost:8000`
- Frontend: `npm start` in `frontend/` → `localhost:3000`
- Frontend API target is env-driven: `REACT_APP_API_URL` (`frontend/.env` = localhost). Never hardcode.
- Login from `localhost:3000` only. Supabase Redirect URLs must include `http://localhost:3000/**`.

## Pushing changes
- Whole repo (front + back) → GitHub: commit/push from repo root.
- NEVER commit or push inside `backend/` (its git points to HF). HF Space is updated by MANUAL paste only: paste full files, never snippets, then check HF build logs + `/health`.
- The backend tab showing "1 ahead" is expected. Ignore it.
- Secrets (`backend/.env`, `frontend/.env`, `backend/.venv`) are git-ignored. Never commit.

## Prod
- Frontend: `unitwise-weld.vercel.app` (uses Vercel `REACT_APP_API_URL`).
- Backend: HF Space. CORS allows localhost:3000 + Vercel.
