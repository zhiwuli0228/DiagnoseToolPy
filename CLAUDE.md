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

# Frontend E2E Verification Rule

## Goal

When fixing frontend bugs, Claude Code must not rely only on static code analysis. It must verify the issue in a real browser whenever the frontend can be started locally.

## Required workflow

For every frontend UI bug fix:

1. Understand the reported user path.
2. Start the frontend dev server if it is not running.
3. Use Playwright MCP to open the target page.
4. Reproduce the issue through real browser interaction.
5. Inspect:
   - visible UI state
   - DOM / accessibility snapshot
   - browser console errors
   - network failures if relevant
6. Apply the minimal code fix.
7. Re-run the same browser path.
8. Capture evidence:
   - final page state
   - screenshot when useful
   - console status
   - test result
9. If the bug is reproducible, add or update a Playwright E2E test.
10. Do not mark the task complete until browser verification passes or the reason verification is impossible is explicitly stated.

## Verification output format

At the end of the task, report:

- Reproduction path
- Root cause
- Code changes
- Browser verification result
- Screenshot / trace / test evidence if available
- Remaining risk

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

| Module       | Purpose                                                         | Notes                                                 |
| ------------ | --------------------------------------------------------------- | ----------------------------------------------------- |
| `api/`       | FastAPI route handlers                                          | Thin layer - validation, formatting, calling services |
| `core/`      | Config loading, path security, shared models                    | No business logic                                     |
| `analyzer/`  | Log analysis: scanning, parsing, classification, sampling       | **Must be independent from FastAPI**                  |
| `casebase/`  | Case lifecycle: write `case.md`/`metadata.yaml`, maintain index | File-based                                            |
| `retrieval/` | Similar case search via keywords, rules, BM25                   | Works without embeddings by default                   |
| `exporter/`  | Export formats: Markdown, JSONL, ZIP, bugfix prompts            |                                                       |

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
- Frontend calls `/api/source/check`, `/api/source/scan`, `/api/diagnosis/*`, `/api/cases/*`, `/api/cluster`
- API routes in `diagnose_tool/api/routes_*.py`

### Cluster Analysis API

| Endpoint                 | Method | Purpose                                               |
| ------------------------ | ------ | ----------------------------------------------------- |
| `/api/cluster`           | POST   | Create async clustering task, returns `task_id`       |
| `/api/cluster/{task_id}` | GET    | Poll task progress/status, returns clusters when done |

### Conversational Diagnosis API

| Endpoint                                            | Method | Purpose                                   |
| --------------------------------------------------- | ------ | ----------------------------------------- |
| `/api/diagnosis/conversation`                       | POST   | Create/continue diagnosis conversation    |
| `/api/diagnosis/conversation/{session_id}`          | GET    | Get conversation state and history        |
| `/api/diagnosis/conversation/{session_id}/continue` | POST   | Continue with user's reply                |
| `/api/diagnosis/conversation/{session_id}/skip`     | POST   | Skip follow-up, force diagnosis           |
| `/api/diagnosis/conversation/{session_id}/end`      | POST   | End conversation, trigger quality scoring |

**Request/Response Models:**
- `UserContextModel`: `phenomenon`, `stack`, `params` (user-provided context)
- `ConversationStartRequest`: `session_id`, `user_context`, `evidence_refs`, `mode`, `max_follow_up_rounds`
- `ConversationStartResponse`: `session_id`, `is_new_session`, `turn_id`, `state`, `ai_question`, `ai_diagnosis`
- `EndConversationResponse`: `session_id`, `quality_score`, `case_id`, `is_draft`, `diagnosis`

**Session Storage**: Sessions stored in `data/sessions/{session_id}/` with `metadata.yaml` and `conversation/turn-*.json` files.

### Workspace Export API

| Endpoint                          | Method | Purpose                                                 |
| --------------------------------- | ------ | ------------------------------------------------------- |
| `/api/diagnosis/export-workspace` | POST   | Export workspace to user directory for manual diagnosis |
| `/api/diagnosis/check-result`     | GET    | Poll for result.md in exported workspace                |

**Workspace Export Flow:**
1. User clicks "Preview Prompt" button in DiagnosisStudio, Search, or Cluster views
2. System prompts for workspace directory path
3. `POST /api/diagnosis/export-workspace` creates directory structure with:
   - `README.md` - Instructions for manual diagnosis
   - `prompt.md` - Pre-filled diagnosis prompt with evidence
   - `context/phenomenon.md`, `stack.md`, `params.md` - User context
   - `logs/evidence-pack.md` - Compressed log evidence
   - `cases/` - Up to 3 similar historical cases
4. User opens workspace in OpenCode, completes diagnosis, saves as `result.md`
5. System polls `GET /api/diagnosis/check-result` for result
6. Valid result is imported as diagnosis

**ExportWorkspaceRequest:**
```json
{
  "task_id": "optional - export from analysis task",
  "session_id": "optional - export from conversation session",
  "cache_key": "optional - export from search/cluster cache",
  "workspace_dir": "required - user-selected directory",
  "user_context": {"phenomenon": "", "stack": "", "params": ""},
  "selections": [{"type": "log|group|cluster", "id": "", "group_key": "", "cluster_index": 0}]
}
```

**Degraded Response (503):** When LLM is unavailable, API returns degraded response with `workspace_export_url` and `workspace_export_options` to guide user to workspace export flow.

### Result Detection

The `useResultDetection` hook handles polling for `result.md` in exported workspace:
- 5-second polling interval
- 30-minute timeout
- localStorage persistence for page reload recovery
- Validates result.md content (not empty, >100 chars, not prompt template)