# Authority Notice

This file is the canonical project-level instruction entry for AI development agents.
Tool-specific instructions may exist in `CLAUDE.md`, `.claude/`, or `.opencode/`, but they must not override the non-negotiable project constraints and change-governance rules defined here.

# AGENT.md

This file defines the project-level rules for AI agents working on **DiagnoseToolPy**.

DiagnoseToolPy uses a project-level harness. Agents must follow this file, `openspec/config.yaml`, and the documentation under `docs/`.

---

## 1. Project Identity

DiagnoseToolPy is a lightweight Web-based diagnostic assistant for system stability work.

It helps users:

1. Select server-side log directories.
2. Stream and analyze large log files.
3. Merge multiline stack traces.
4. Parse complex log headers.
5. Classify exceptions using configurable rules.
6. Generate evidence packages for AI-assisted diagnosis.
7. Convert analysis results into reusable fault cases.
8. Maintain a local file-based case knowledge base.
9. Retrieve similar cases without requiring embeddings.
10. Optionally enable vector retrieval later.

DiagnoseToolPy is **not**:

- A generic ELK replacement.
- A real-time log collection platform.
- A distributed log search engine.
- A database-backed ticket system.
- A mandatory AI diagnosis platform.

---

## 2. Required Reading Order

Before implementing any non-trivial change, read:

1. `openspec/config.yaml`
2. `AGENT.md`
3. `docs/README.md`
4. `docs/00-project/project-brief.md`
5. `docs/00-project/current-state.md`
6. `docs/02-harness/harness-standard.md`

For OpenSpec work, also read:

1. `docs/03-openspec/proposal-rule.md`
2. `docs/03-openspec/design-rule.md`
3. `docs/03-openspec/spec-rule.md`
4. `docs/03-openspec/tasks-rule.md`

For log analyzer work, also read:

1. `docs/05-domain/log-format-guide.md`
2. `docs/05-domain/log-analysis-rules.md`
3. `docs/01-architecture/module-boundaries.md`

For casebase or retrieval work, also read:

1. `docs/01-architecture/casebase-design.md`
2. `docs/01-architecture/retrieval-design.md`
3. `docs/01-architecture/storage-contract.md`

For deployment or operations work, also read:

1. `docs/06-operations/deployment-guide.md`
2. `docs/06-operations/docker-compose-guide.md`
3. `docs/06-operations/server-directory-access.md`
4. `docs/06-operations/security-policy.md`

---

## 3. Hard Constraints

These constraints take precedence over generated OpenSpec artifacts.

### 3.1 No Mandatory Database

Do not introduce mandatory external databases.

Do not add mandatory dependencies on:

- MySQL
- PostgreSQL
- Elasticsearch
- ClickHouse
- Redis
- MongoDB
- Qdrant server
- mandatory SQLite
- any other required infrastructure service

Allowed storage formats:

- Markdown
- YAML
- JSON
- JSONL
- HTML
- plain text
- local rebuildable indexes

Optional local indexes are allowed only when disabled by default.

Examples:

- `rank-bm25` corpus files
- LanceDB local index
- FAISS local index

### 3.2 File System Is the Source of Truth

Durable knowledge must be stored as files.

Fault cases must be represented by:

```text
case.md
metadata.yaml
```

Analysis task state must be represented by:

```text
task.yaml
progress.json
```

Indexes are rebuildable caches, not durable truth.

### 3.3 Server Directory Scanning First

Large logs should not be uploaded through the browser.

Primary workflow:

```text
user uploads logs to server directory
→ user selects directory in Web UI
→ backend scans local files
→ analyzer streams logs
→ report and case draft are generated
```

Browser upload is optional and only for small files.

### 3.4 Large Logs Must Be Streamed

Never load a full log file into memory.

Forbidden:

```python
content = file.read()
lines = file.readlines()
```

Required:

```python
for line in file:
    process(line)
```

Samples must be bounded.

Do not store all matched logs in memory.

### 3.5 Retrieval Must Work Without Embeddings

Embedding models must not be required.

Default retrieval must work through:

- keywords
- exception classes
- key phrases
- stack symbols
- components
- tags
- fault modes
- BM25 when available

Vector search must be optional and disabled by default.

### 3.6 AI Diagnosis Is Assistive

AI diagnosis is not the final truth.

The system must preserve fields for:

- AI preliminary diagnosis
- human-confirmed root cause
- handling process
- lessons learned
- follow-up checklist

Do not design flows where AI output automatically becomes confirmed root cause.

---

## 4. Expected Technology Stack

Use:

- Python 3.11+
- uv
- FastAPI
- Jinja2 or simple HTML/JS for MVP UI
- Pydantic or dataclasses
- PyYAML
- Markdown/YAML/JSONL file storage
- pytest
- ruff

Optional:

- rank-bm25
- LanceDB
- FAISS

Avoid mandatory heavy infrastructure.

---

## 5. Recommended Project Structure

```text
DiagnoseToolPy/
├── AGENT.md
├── openspec/
│   └── config.yaml
├── docs/
│   ├── README.md
│   ├── 00-project/
│   ├── 01-architecture/
│   ├── 02-harness/
│   ├── 03-openspec/
│   ├── 04-development/
│   ├── 05-domain/
│   ├── 06-operations/
│   ├── 07-templates/
│   └── 99-archive/
├── config/
│   ├── app.yaml
│   ├── rules/
│   └── case_templates/
├── diagnose_tool/
│   ├── api/
│   ├── core/
│   ├── analyzer/
│   ├── casebase/
│   ├── retrieval/
│   ├── exporter/
│   ├── templates/
│   └── static/
├── data/
│   ├── input/
│   ├── output/
│   ├── cases/
│   ├── indexes/
│   └── runtime/
└── tests/
```

---

## 6. Module Boundaries

### 6.1 `api`

FastAPI route layer only.

Allowed:

- Request validation
- Response formatting
- Calling service functions

Forbidden:

- Log parsing logic
- Case writing logic
- Retrieval ranking logic
- Large file processing

### 6.2 `core`

Shared infrastructure.

Responsibilities:

- Config loading
- Path whitelist validation
- Shared models
- File state helpers
- Safe path utilities
- Atomic file write helpers where practical

### 6.3 `analyzer`

Log analysis module.

Responsibilities:

- Directory scanning
- File type filtering
- Streaming reads
- `.gz` reads
- Multiline stack trace merge
- Complex header parsing
- Rule-based classification
- Sample extraction
- Timeline generation
- Evidence package generation
- HTML report generation
- Case draft generation

Must not:

- Depend on FastAPI
- Write final archived cases directly
- Call AI providers

### 6.4 `casebase`

Fault case management module.

Responsibilities:

- Manual case creation
- Case creation from task artifacts
- Write `case.md`
- Write `metadata.yaml`
- Load cases
- Update cases
- Archive cases
- Maintain `data/cases/index.yaml`

### 6.5 `retrieval`

Local retrieval module.

Responsibilities:

- Build retrieval query from analysis result
- Keyword search
- Rule matching
- BM25 search
- Optional vector search
- Hybrid ranking
- Similar case prompt context generation

Must work when embedding is disabled.

### 6.6 `exporter`

Export module.

Responsibilities:

- Case Markdown export
- RAG JSONL dataset export
- ZIP export
- Bugfix prompt export

---

## 7. Log Parsing Rules

The project must support complex log headers such as:

```text
2026-05-16 10:01:01.123 ERROR [[order-core]worker-1] [com.demo.OrderService] query failed
```

Do not parse this format with naive bracket splitting.

Forbidden:

```python
parts = line.split("[")
```

Required strategy:

1. Parse timestamp and level with regex.
2. Parse bracket groups with a balanced bracket scanner.
3. Parse first bracket group as module/thread.
4. Parse second bracket group as logger.
5. Preserve remaining content as message.
6. Preserve raw content if parsing fails.

Expected fields:

- timestamp
- level
- module
- thread
- logger
- message
- raw
- file_path
- line_no
- parse_status

Allowed parse statuses:

```text
FULL
PARTIAL
RAW
```

Parsing failure must not discard logs.

---

## 8. Storage Contracts

### 8.1 Analysis Task Output

```text
data/output/{task_id}/
├── task.yaml
├── progress.json
├── summary.html
├── evidence-pack.md
├── key-logs.txt
├── case-draft.md
├── case-metadata-draft.yaml
├── retrieval-query.json
└── artifacts/
    ├── timeline.json
    └── raw-samples.jsonl
```

### 8.2 Fault Case

```text
data/cases/{case_id}_{slug}/
├── case.md
├── metadata.yaml
├── evidence-pack.md
├── key-logs.txt
├── ai-diagnosis.md
├── review.md
├── actions.md
└── artifacts/
```

### 8.3 Case Index

```text
data/cases/index.yaml
```

The case index must be rebuildable from case directories.

### 8.4 Retrieval Indexes

Allowed rebuildable indexes:

```text
data/indexes/fulltext/index.jsonl
data/indexes/bm25/corpus.jsonl
data/indexes/lancedb/
```

These indexes must not be treated as durable truth.

---

## 9. Casebase Rules

Every archived case must include:

```text
case.md
metadata.yaml
```

Supported case source types:

```text
auto
manual
imported
template
```

Supported case states:

```text
DRAFT
REVIEWING
ARCHIVED
DEPRECATED
```

Manual case creation is required.

Automatic case draft generation from analysis tasks is required.

Every archived case must update or be included in:

```text
data/cases/index.yaml
```

---

## 10. Retrieval Rules

Retrieval must work without embeddings.

Default retrieval channels:

- keyword matching
- exception class matching
- key phrase matching
- component matching
- tag matching
- fault mode matching
- BM25 when available

Optional retrieval channels:

- vector search
- LanceDB
- FAISS

Embedding must be disabled by default.

Historical cases included in AI prompts must be marked as references only.

Do not present historical case root cause as confirmed root cause for the current issue.

---

## 11. Coding Rules

Use Python 3.11+.

General rules:

- Use `pathlib.Path`.
- Avoid string path concatenation.
- Keep modules small.
- Prefer explicit models for structured data.
- Avoid global mutable state.
- Do not swallow exceptions silently.
- Return safe error messages to UI.
- Keep analyzer logic independent from FastAPI.
- Keep casebase logic independent from FastAPI.
- Keep retrieval logic independent from FastAPI.
- Handle uncertain log encodings safely.
- Do not make network calls unless explicitly required.

Recommended file reading:

```python
with path.open("r", encoding="utf-8", errors="replace") as f:
    for line in f:
        ...
```

---

## 12. Testing Rules

Use pytest.

Required tests for relevant changes:

### `core`

- Config loading
- Path whitelist validation
- Path traversal rejection
- Safe file state behavior

### `analyzer`

- Directory scanner
- Streaming reader
- Gzip reader
- Multiline stack trace merge
- Complex header parser
- Rule classifier
- Sample limiter
- Evidence package generation

### `casebase`

- Manual case writing
- Case from task
- Metadata writing
- Case index rebuild
- Invalid metadata handling

### `retrieval`

- Retrieval query builder
- Keyword search
- Rule matching
- BM25 search if enabled
- Embedding disabled behavior

### `api`

- Success response
- Invalid path response
- Missing input response
- Safe error response

Test fixtures should be small and stored under:

```text
tests/fixtures/
```

Do not commit large logs.

Generate temporary large files in tests if needed.

---

## 13. OpenSpec Rules

When using OpenSpec, treat:

```text
openspec/config.yaml
```

as the OpenSpec entry configuration.

For every OpenSpec change:

1. Read `openspec/config.yaml`.
2. Read `AGENT.md`.
3. Read `docs/README.md`.
4. Read `docs/00-project/project-brief.md`.
5. Read `docs/00-project/current-state.md`.
6. Read the relevant rule file under `docs/03-openspec/`.

Project-level constraints in these files take precedence over generated artifacts:

1. `AGENT.md`
2. `openspec/config.yaml`
3. `docs/02-harness/*`
4. `docs/01-architecture/*`

---

## 14. Recommended Development Flow

For non-trivial features:

```text
/opsx:explore
→ /opsx:propose
→ review proposal/design/spec/tasks
→ /opsx:apply
→ tests
→ update current-state.md
→ /opsx:archive
```

For small bug fixes:

1. Reproduce.
2. Identify root cause.
3. Fix minimally.
4. Add regression test.
5. Update current-state.md if needed.

Do not create oversized OpenSpec changes for trivial bugs.

---

## 15. Standard Commands

Install dependencies:

```bash
uv add fastapi uvicorn pydantic pydantic-settings pyyaml jinja2 python-multipart
uv add rank-bm25
uv add --dev pytest pytest-cov ruff
```

Run development server:

```bash
uv run uvicorn diagnose_tool.main:app --host 0.0.0.0 --port 18080 --reload
```

Run tests:

```bash
uv run pytest
```

Run lint:

```bash
uv run ruff check .
```

---

## 16. Required Finalization for Every Change

Before considering work complete:

- [ ] Code is implemented.
- [ ] Tests are added or updated.
- [ ] Storage contract changes are documented.
- [ ] Relevant docs are updated.
- [ ] `docs/00-project/current-state.md` is updated.
- [ ] No mandatory database was introduced.
- [ ] Large-file behavior remains streaming-based.
- [ ] File-system-as-source-of-truth remains preserved.
