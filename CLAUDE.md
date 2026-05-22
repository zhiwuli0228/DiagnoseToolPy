# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DiagnoseToolPy is a lightweight Web-based diagnostic assistant for system stability work. It scans server-side log directories, streams and analyzes large log files, generates evidence packages, and maintains a file-based case knowledge base with retrieval that works without embeddings.

## Tech Stack

- **Backend**: Python 3.12+, FastAPI, Pydantic, Jinja2, PyYAML
- **Frontend**: React 18, Vite 6, TypeScript 5, Ant Design 5, React Router 7
- **Package Manager**: uv (backend), npm (frontend)
- **Testing**: pytest + pytest-cov (backend), Vitest (frontend)
- **Linting**: ruff (backend)

## Common Commands

### Backend (from project root)
```bash
# Install dependencies
uv add fastapi uvicorn pydantic pydantic-settings pyyaml jinja2 python-multipart
uv add rank-bm25
uv add --dev pytest pytest-cov ruff

# Run development server on port 18080
uv run uvicorn diagnose_tool.main:app --host 0.0.0.0 --port 18080 --reload

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=diagnose_tool

# Run lint
uv run ruff check .
```

### Frontend (from `frontend/` directory)
```bash
# Install dependencies
npm install

# Start dev server (proxies /api to localhost:18080)
npm run dev

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Build for production
npm run build
```

## Architecture

```
Web UI (React) → FastAPI API → Service Modules → File-based Storage
```

### Backend Modules (`diagnose_tool/`)

| Module | Purpose | Notes |
|--------|---------|-------|
| `api/` | FastAPI route handlers | Thin layer - validation, formatting, calling services |
| `core/` | Config loading, path security, shared models | No business logic |
| `analyzer/` | Log analysis: scanning, parsing, classification, sampling | **Must be independent from FastAPI** |
| `casebase/` | Case lifecycle: write `case.md`/`metadata.yaml`, maintain index | File-based |
| `retrieval/` | Similar case search via keywords, rules, BM25 | Works without embeddings by default |
| `exporter/` | Export formats: Markdown, JSONL, ZIP, bugfix prompts | |

### Frontend Structure (`frontend/src/`)

- `api/` - Axios client and API call functions
- `pages/` - Route components: Dashboard, AnalysisTasks, TaskDetail, Casebase, CaseDetail, Settings
- `components/layout/` - AppLayout with sidebar navigation

## Key Constraints

1. **File system is source of truth** - Durable knowledge stored as `.md` and `.yaml` files, not a database
2. **No mandatory database** - Only file-based storage (Markdown, YAML, JSON, JSONL); optional local indexes (BM25, LanceDB) are disabled by default
3. **Stream large logs** - Never `file.read()` full content; use `for line in file:` iteration with bounded samples
4. **Retrieval without embeddings** - Default retrieval uses keywords, exception classes, rules, BM25; vector search is optional/disabled
5. **AI diagnosis is assistive** - System preserves fields for human-confirmed root cause; AI output is not automatically confirmed

## Storage Contracts

### Analysis Task Output
```
data/output/{task_id}/
├── task.yaml
├── progress.json
├── summary.html
├── evidence-pack.md
├── case-draft.md
└── artifacts/
```

### Fault Case
```
data/cases/{case_id}_{slug}/
├── case.md
├── metadata.yaml
└── ...
```

### Case Index (rebuildable)
```
data/cases/index.yaml
```

## Log Parsing

Complex log headers must be parsed with regex + balanced bracket scanner:
```
2026-05-16 10:01:01.123 ERROR [[order-core]worker-1] [com.demo.OrderService] query failed
```
- Parse timestamp/level with regex
- Parse bracket groups with balanced bracket scanner
- Never use naive `line.split("[")`

## Frontend-Backend Communication

- Vite dev server proxies `/api` → `http://localhost:18080` (avoids CORS)
- Frontend calls `/api/source/check`, `/api/source/scan`, `/api/diagnosis/*`, `/api/cases/*`
- API routes in `diagnose_tool/api/routes_*.py`