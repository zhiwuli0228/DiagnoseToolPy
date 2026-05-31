# DiagnoseToolPy

A lightweight Web-based diagnostic assistant for system stability work. DiagnoseToolPy scans server-side log directories, analyzes log content with streaming processing, generates evidence packages, and maintains a file-based case knowledge base with retrieval that works without embeddings.

## Architecture

```
Web UI (React) → FastAPI API → Service Modules → File-based Storage
```

| Module | Responsibility |
|--------|----------------|
| `diagnose_tool/api/` | FastAPI route handlers — thin layer, only validation and formatting |
| `diagnose_tool/core/` | Config loading, path security, shared models |
| `diagnose_tool/analyzer/` | Log analysis: scanning, streaming reads, parsing, classification, sampling — **no FastAPI dependency** |
| `diagnose_tool/casebase/` | Fault case lifecycle: `case.md` + `metadata.yaml`, `index.yaml` |
| `diagnose_tool/retrieval/` | Similar case search: keywords, rules, BM25 (works without embeddings) |
| `diagnose_tool/exporter/` | Export: Markdown, JSONL, ZIP, bugfix prompts |

**Key constraints:**
- File system is source of truth — no mandatory database
- Large logs are streamed line-by-line, never loaded into memory
- Retrieval works without embeddings; vector search is optional and disabled by default
- AI diagnosis is assistive only — preserves fields for human-confirmed root cause

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+ (frontend)
- uv (backend package manager)

### 1. Prepare directories

```bash
mkdir -p data/input data/output data/cases data/indexes data/runtime
```

### 2. Start backend

```bash
uv run uvicorn diagnose_tool.main:app --host 0.0.0.0 --port 18080 --reload
```

API available at `http://127.0.0.1:18080`

### 3. Start frontend (optional)

```bash
cd frontend
npm install
npm run dev
```

Frontend at `http://localhost:3000` (proxies `/api` to backend on 18080).

## Configuration

Edit `config/app.yaml`:

```yaml
app:
  name: DiagnoseToolPy
  version: 0.1.0
server:
  host: 0.0.0.0
  port: 18080
paths:
  allowed_input_roots:
    - /path/to/your/logs    # Directories the tool can read
    - data/input
  data_dir: data
llm:
  enabled: false            # Set true to enable AI diagnosis
  model: "gpt-4o-mini"
  base_url: "https://api.openai.com/v1"
  api_key: "your-key-here"
  timeout: 60
```

`allowed_input_roots` limits which server directories the tool can scan — path traversal outside these roots is rejected.

## Usage Workflow

1. **Place logs** on the server at a path listed in `allowed_input_roots`
2. **Scan** — enter the directory path in the Web UI; the backend scans file metadata (not content) and returns file counts and sizes
3. **Search** — apply time range, thread, keyword (AND), and exclude-keyword filters to search log content
4. **Aggregate** — enable aggregation to group similar exceptions/log messages with counts; toggle thread/time grouping
5. **Diagnose** — send search results and similar historical cases to the LLM for AI-assisted diagnosis
6. **Archive** — save analysis results as a fault case (`case.md` + `metadata.yaml`) for future retrieval

## Development Commands

### Backend

```bash
# Install dependencies
uv add fastapi uvicorn pydantic pydantic-settings pyyaml jinja2 python-multipart
uv add rank-bm25
uv add --dev pytest pytest-cov ruff

# Run development server
uv run uvicorn diagnose_tool.main:app --host 0.0.0.0 --port 18080 --reload

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=diagnose_tool

# Lint
uv run ruff check .
```

### Frontend

```bash
cd frontend
npm install

# Dev server (proxies /api to localhost:18080)
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

## Production Deployment

### Docker

```bash
# Build image
docker build -t diagnose-tool .

# Start (uses docker-compose.yml volume mounts)
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

### Required host directories

```bash
mkdir -p /data/diagnose/input      # Read-only: put log files here
mkdir -p /data/diagnose/output      # Analysis task output
mkdir -p /data/diagnose/cases        # Fault case library
mkdir -p /data/diagnose/indexes      # BM25/search indexes
mkdir -p /data/diagnose/runtime      # Temporary runtime files
```

### nginx configuration (optional)

```nginx
server {
    listen 80;
    root /var/www/diagnosetoolpy/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:18080/api/;
    }
}
```

## Log Format Support

DiagnoseToolPy handles complex log header formats:

```
2026-05-15 12:00:00,218 ERROR [[module]thread] [logger] message
```

Features:
- Timestamp with dot or comma milliseconds: `12:00:00.218` or `12:00:00,218`
- Nested brackets in module/thread: `[[order-core]worker-1]`
- Empty placeholder brackets: `[]`
- Nested brackets in message body: JSON, SQL, URLs, maps
- Balanced bracket scanner — never loses log content on parse failure

## Storage Structure

```
data/
├── input/              # Server log files (read-only in config)
├── output/             # Analysis task outputs
│   └── {task_id}/
│       ├── task.yaml
│       ├── evidence-pack.md
│       ├── case-draft.md
│       └── artifacts/
├── cases/              # Archived fault cases
│   └── {case_id}_{slug}/
│       ├── case.md
│       ├── metadata.yaml
│       └── evidence-pack.md
└── indexes/
    └── bm25/
        └── corpus.jsonl   # Persisted BM25 corpus (rebuildable)
```