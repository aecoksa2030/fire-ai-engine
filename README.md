# AECO Fire & Security AI Engine

An internal web application that uses AI to automate quantity takeoff for **fire protection** and **physical security** projects. Estimation engineers upload engineering drawings and project technical specifications (PTS), and the application returns structured, reviewable outputs such as a Bill of Quantities (BOQ) or a project scope table.

---

## Features

### 1. Projects — PTS scope extraction (stage 1 of the estimation workflow)
- Upload a project's technical specification (PTS) as a PDF.
- The AI reads the whole document and returns the fire-protection **scope** as a flat table: `SL #` | `Area` | `Type of system required as per PTS`, with one row per area/system pair.
- The table can be edited inline (edit cells, add or delete rows), saved, and downloaded as an **Excel** file in the estimation team's reference layout.
- Approved tables can be added to the **reference library (RAG)**. Every new extraction receives up to 3 approved tables as guidance for naming and level of detail.
- The saved table (JSON) will be the input to stage 2, together with the project's FEED package.

### 2. Drawing analysis (BOQ extraction)
- Upload a fire protection or security drawing (PDF) and choose the AI provider and report type (`fire` / `security`).
- Each page is analyzed, and the result is streamed back with live page-by-page progress.
- Output: a BOQ table (component, quantity, confidence, supplier type) with optional ERPNext item matching and pricing, plus a list of unclear areas flagged for manual review.
- CAD support: DWG→DXF / DWG→PDF conversion through ODA File Converter, and DXF analysis.

### 3. Drawing chat
- Ask follow-up questions about a saved drawing, for example to correct counts or query a specific floor. The full PDF is sent to Claude with prompt caching.
- Fixed prompt templates:
  - **Security:** HCIS requirements for Class 1 (380 kV) and Class 3 substations.
  - **Fire:** requirements per TES-P-119.21.
- Replies can be rendered as a table and merged into the main BOQ.

### 4. Archive
- Saved analyses keep the original PDF and the BOQ, and can be browsed, renamed, deleted and reopened for chat.

### 5. Reference library (RAG)
- Approved drawing analyses and approved PTS scope tables are stored as reference examples and used to guide future extractions of the same type.
- Retrieval is deliberately simple: a filter on report type plus string-similarity ranking, with no vector database.

### 6. Users & roles
- JWT authentication with the roles `admin`, `engineer` and `auditor`.
- Admins can create users, change roles, reset passwords and delete users.
- The UI is available in Arabic and English, with light and dark themes.

---

## Architecture

```
Browser ──► nginx (reverse proxy)
              ├── /        ──► frontend-next  (Next.js, port 3000)
              └── /api/*   ──► api            (FastAPI / uvicorn, port 8003)
                                   ├── PostgreSQL (db_fire_ai, port 5432)
                                   ├── Anthropic Claude / Google Gemini / Groq / OpenRouter
                                   └── ERPNext (item matching & pricing)
```

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, Tailwind CSS v4, TanStack Table, react-pdf, Zustand |
| Backend | FastAPI, SQLAlchemy 2, Pydantic 2, uvicorn |
| Database | PostgreSQL 16 (`pgvector/pgvector:pg16` image) |
| AI | Anthropic Claude (default for chat and PTS extraction), Google Gemini, Groq, OpenRouter |
| Documents | PyMuPDF, pypdf, ezdxf, ODA File Converter, openpyxl |
| Deployment | Docker Compose behind nginx |

> A legacy Streamlit frontend (`frontend/`, service `frontend`, port 8501) is still in the repository and in `docker-compose.yml`. It has been replaced by `frontend-next` and can be removed once it is no longer needed.

---

## Repository layout

```
fire-ai-engine/
├── app/                              # FastAPI backend
│   ├── main.py                       # App entry point, CORS, router registration, DB init
│   ├── database.py                   # SQLAlchemy models + DB helpers (single source of models)
│   ├── routers/
│   │   ├── auth.py                   # Login, users, saved sessions (archive)
│   │   ├── process.py                # Drawing BOQ extraction (PDF / CAD)
│   │   ├── chat.py                   # Drawing chat
│   │   ├── library.py                # Reference library (RAG) for drawings
│   │   └── projects.py               # PTS scope extraction, approval, Excel export
│   └── services/
│       ├── claude_service.py         # Claude drawing extraction
│       ├── ai_service.py             # Gemini drawing extraction
│       ├── groq_service.py           # Groq drawing extraction
│       ├── openrouter_service.py     # OpenRouter drawing extraction
│       ├── claude_chat_service.py    # Drawing chat (Claude + prompt caching)
│       ├── project_spec_service.py   # PTS scope extraction + Excel builder
│       ├── reference_library_service.py
│       ├── prompts.py                # Fire / security extraction prompts
│       ├── parser_service.py         # PDF page handling
│       ├── cad_service.py            # DXF analysis
│       ├── erpnext_service.py / item_matcher.py
│       ├── pricing.py                # Per-model token pricing (cost estimates)
│       └── json_utils.py             # Robust JSON parsing of model output
├── frontend-next/                    # Next.js frontend
│   └── src/
│       ├── app/(app)/                # projects, analyze, archive, users pages
│       ├── app/login/
│       ├── components/               # scope-table, boq-table, drawing-chat, pdf-viewer, ...
│       └── lib/                      # api.ts, i18n.ts, auth-store.ts, prompt templates
├── frontend/                         # Legacy Streamlit frontend
├── storage/drawings/                 # Uploaded drawings (mounted volume)
├── Dockerfile                        # API image
├── Dockerfile.frontend-next          # Next.js image (multi-stage)
├── Dockerfile.frontend               # Legacy Streamlit image
├── docker-compose.yml
├── requirements.txt
├── reset_db.py / migrate_add_columns.py
└── .env                              # Secrets (not committed)
```

---

## Configuration

Create a `.env` file in the project root:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | yes | PostgreSQL connection string (already set in `docker-compose.yml`) |
| `JWT_SECRET_KEY` | yes | Secret used to sign login tokens. **Must be changed from the default in production.** |
| `ANTHROPIC_API_KEY` | yes | Claude: drawing chat, PTS extraction, Claude drawing analysis |
| `CLAUDE_MODEL` | no | Claude model ID (default: `claude-fable-5`) |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | if using Gemini | Google Gemini provider |
| `GROQ_API_KEY` / `GROQ_MODEL` | if using Groq | Groq provider |
| `OPENROUTER_API_KEY` / `OPENROUTER_MODEL` / `OPENROUTER_SITE_URL` / `OPENROUTER_APP_NAME` | if using OpenRouter | OpenRouter provider |
| `ERPNEXT_URL` / `ERPNEXT_API_KEY` / `ERPNEXT_API_SECRET` | for ERP matching | ERPNext item matching and pricing |
| `UPLOAD_DIR` | no | Drawing storage path (default: `/app/storage/drawings`) |

The frontend takes a single build-time setting, `NEXT_PUBLIC_API_URL` (default `/api/v1`). It is passed as a Docker build argument because Next.js inlines it into the client bundle at build time.

---

## Running with Docker

```bash
# First time / after dependency changes
docker compose up -d --build

# Services
#   api            -> http://localhost:8003   (API docs: /docs)
#   frontend-next  -> http://localhost:3000
#   db_fire_ai     -> 127.0.0.1:5434
```

When to rebuild after a change:

| Change | Command |
|---|---|
| Python code only (`app/`) | `docker compose restart api` |
| `requirements.txt` or `Dockerfile` | `docker compose up -d --build api` |
| Anything in `frontend-next/` | `docker compose up -d --build frontend-next` |

When copying frontend changes to the server, always replace `frontend-next/src` **as a whole folder**. If an old file that is no longer used stays behind, it can break the TypeScript build.

### Creating the first admin user

Tables are created automatically on startup. To create the first admin account:

```bash
docker compose exec api python -c "from app.database import SessionLocal, create_user; create_user(SessionLocal(), 'admin', 'admin@example.com', 'CHANGE_ME', role='admin')"
```

---

## Local development (without Docker)

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://ai_user:<password>@localhost:5434/fire_engine_db
uvicorn app.main:app --port 8003 --reload

# Frontend
cd frontend-next
npm install
npm run dev          # http://localhost:3000
npm run build        # production build + type check
```

---

## API overview

All endpoints are under `/api/v1` and, except login, require `Authorization: Bearer <token>`. Interactive documentation is available at `/docs`.

| Area | Method & path | Purpose |
|---|---|---|
| Auth | `POST /auth/login` | Log in (form data), returns a JWT |
| | `GET /auth/me` | Validate the current token |
| | `GET/POST /auth/users`, `PATCH/DELETE /auth/users/{id}` | User management (admin only) |
| Archive | `POST /auth/sessions/save` | Save or update an analysis (upsert by `session_id`) |
| | `GET /auth/sessions/my-sessions` | List saved analyses |
| | `PATCH/DELETE /auth/sessions/{id}`, `GET /auth/sessions/{id}/pdf` | Rename, delete, get PDF |
| Extraction | `POST /extract/pdf-boq?provider=&report_type=` | Drawing BOQ extraction (NDJSON progress stream) |
| | `POST /extract/cad-boq`, `/convert-dwg-to-dxf`, `/convert-dwg-to-pdf` | CAD handling |
| Chat | `POST /chat/{session_id}/ask`, `GET /chat/{session_id}/history` | Drawing chat |
| Library | `POST /library/save`, `GET /library/examples`, `DELETE /library/examples/{id}` | Reference library (drawings) |
| Projects | `POST /projects/extract` | PTS → scope table (not saved) |
| | `POST /projects/save`, `PATCH /projects/{id}` | Save / update a scope table |
| | `POST /projects/{id}/approve` | Add an approved table to the reference library |
| | `GET /projects/my-specs`, `DELETE /projects/{id}`, `GET /projects/{id}/pdf` | List, delete, get PDF |
| | `POST /projects/export-xlsx` | Download a scope table as Excel |

---

## Operational notes

- **Single-process API.** uvicorn runs as a single process, so any long blocking call (AI requests, PDF rendering, ERPNext requests) must run in a `ThreadPoolExecutor`. Otherwise it freezes the server for every user. All existing AI endpoints already do this.
- **Long requests.** A PTS extraction or a large drawing analysis can take several minutes. nginx `proxy_read_timeout` and `proxy_send_timeout` for `/api/` must be long enough (for example 600s or more). PTS extraction uses Claude's streaming API because the SDK refuses non-streaming calls with very large `max_tokens`.
- **Database schema changes.** `Base.metadata.create_all()` creates missing **tables** only. It does not add columns to existing tables, so adding a column requires a manual `ALTER TABLE` (see `migrate_add_columns.py`).
- **Model output parsing.** All AI responses go through `json_utils.clean_and_parse_json()` (fence stripping + `json_repair`), and structured outputs are normalized before they reach the frontend, so a partial or malformed model reply cannot crash the UI.
- **Cost tracking.** Token usage and estimated cost are returned with each result and logged in `analysis_logs`. Per-model rates are in `app/services/pricing.py`.

---

## Roadmap

- **Stage 2 of the estimation workflow:** combine the approved PTS scope table with the project's FEED package (to be specified by the estimation team).
- Test PTS extraction across several projects and grow the approved reference library.
- Remove the legacy Streamlit frontend once it is no longer needed.
