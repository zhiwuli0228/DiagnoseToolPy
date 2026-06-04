# Perf P0: GZIP Middleware + Route Lazy Loading — Design

- Date: 2026-06-04
- Status: Approved (pending user spec review)
- Change id: `perf-p0-gzip-and-route-lazy`
- Supersedes: `docs/performance-optimization-design.md` (P0 portion only)
- Governance: First controlled SuperSpec pilot change (per Phase 4 closure)

## 1. Goal & Non-Goals

### Goal
Land the P0 performance fixes in `docs/performance-optimization-design.md` (方案 A 路由懒加载 + 方案 F GZIP 中间件) so the throughput regression in the original stress test (5.47 req/s, target 10) is at least partially recovered, and first-screen JS bundle size drops by ~40%.

### In-Scope
- 方案 A: Convert 6 page components in `frontend/src/App.tsx` to `React.lazy` + `Suspense`
- 方案 F: Add `fastapi.middleware.gzip.GZIPMiddleware(minimum_size=1000)` to `diagnose_tool/main.py`
- Locust-based load test under `tests/load/` with baseline-vs-after comparison
- Unit tests for both changes
- OpenSpec change assets under `openspec/changes/perf-p0-gzip-and-route-lazy/`

### Out-of-Scope
- 方案 B (SWR/React Query client cache) — reserved for P1/P2
- 方案 C (Vite terser / gzip-static build) — reserved for P2
- 方案 D (backend LRU cache for case index) — reserved for P1
- 方案 E (BM25 index preload cache) — reserved for P1
- No modification to `openspec/config.yaml`, `openspec/schemas/**`, `openspec/specs/**`
- No new runtime dependencies (Locust is dev-only; React.lazy is built-in)

### Future Changes (declared, not implemented here)
- `perf-p1-bm25-and-case-cache` — implements 方案 D + E
- `perf-p2-swr-and-asset-compress` — implements 方案 B + C

## 2. Architecture & Files

### Files Touched
```
diagnose_tool/main.py                          # +GZIPMiddleware line
frontend/src/App.tsx                           # 6 pages → React.lazy; +<Suspense>
frontend/vite.config.ts                        # (optional) manualChunks for antd
pyproject.toml                                 # +locust (dev group)
tests/load/locustfile.py                       # NEW
tests/load/run_bench.sh                        # NEW
tests/load/diff_results.py                     # NEW
tests/load/README.md                           # NEW
tests/unit/test_gzip_middleware.py             # NEW
tests/unit/test_lazy_routes.py                 # NEW
openspec/changes/perf-p0-gzip-and-route-lazy/  # NEW (proposal/specs/design/tasks/plan)
docs/rectification/24-…-perf-p0-design-report.md  # NEW (Phase 4 style closure report)
```

### Module Boundaries
This change touches:
- `diagnose_tool/main.py` (API entry)
- `frontend/src/` (UI shell)
- `tests/` (verification)

This change does **not** touch:
- `diagnose_tool/analyzer/**`
- `diagnose_tool/casebase/**`
- `diagnose_tool/retrieval/**`
- `diagnose_tool/exporter/**`
- `diagnose_tool/core/**`

### Component Diagram
```
┌───────────────────────────── Browser ─────────────────────────────┐
│  Initial HTML                                                   │
│      ↓                                                          │
│  main.tsx  → App shell (Layout, Sider, Menu)  ←─ static import   │
│      ↓  <Suspense fallback={<Spin />}>                          │
│  React.lazy()  → current route chunk (dynamic import)           │
│      ↓  HTTP /api/*                                             │
└──────────────────────────────┬──────────────────────────────────┘
                               │  Content-Encoding: gzip (>1KB)
┌──────────────────────────────▼──────────────────────────────────┐
│  FastAPI                                                         │
│  ┌─ CORSMiddleware (existing) ─┐                                │
│  │  └─ GZIPMiddleware (NEW)    │                                │
│  │     └─ business routes      │                                │
│  └─────────────────────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

## 3. Implementation Details

### 3.1 方案 A — Route Lazy Loading

**`frontend/src/App.tsx` transformation:**

```tsx
import { lazy, Suspense } from 'react';
import { Spin } from 'antd';

// 静态 → 动态
const DashboardPage       = lazy(() => import('./pages/DashboardPage'));
const AnalysisTasksPage   = lazy(() => import('./pages/AnalysisTasksPage'));
const CasebasePage        = lazy(() => import('./pages/CasebasePage'));
const AIDiagnosisPage     = lazy(() => import('./pages/AIDiagnosisPage'));
const DiagnosisStudioPage = lazy(() => import('./pages/DiagnosisStudioPage'));
const SettingsPage        = lazy(() => import('./pages/SettingsPage'));

// 顶层包 Suspense
<Suspense fallback={<Spin size="large" style={{ display: 'block', margin: 120 }} />}>
  <Layout>...</Layout>
</Suspense>
```

**Chunk strategy:**
- Vite auto-splits by route by default
- Optional `vite.config.ts` `build.rollupOptions.output.manualChunks` to extract antd into a shared `vendor-antd` chunk

**Behavior preserved:**
- `TabContent` mount/unmount preservation logic untouched
- `PRESERVE_STATE_PATHS` array untouched
- i18n, AIDiagnosisButton, LanguageSwitcher remain static (shell-required)

### 3.2 方案 F — GZIP Middleware

**`diagnose_tool/main.py` transformation:**

```python
from fastapi.middleware.gzip import GZIPMiddleware

# Insert after CORSMiddleware
app.add_middleware(GZIPMiddleware, minimum_size=1000)
```

**Middleware order:** `GZIPMiddleware` must be **inside** `CORSMiddleware` so CORS can read `Content-Encoding` from the response and forward it to the browser.

**Threshold:** `minimum_size=1000` bytes (matches `docs/performance-optimization-design.md` §3.2 方案 F).

**Content-Type:** No custom whitelist — FastAPI's default covers HTML/JSON/CSS/JS.

### 3.3 Locust Load Test

**`tests/load/locustfile.py`:**
- `DiagnoseUser` class with mixed endpoints: `/`, `/api/health`, `/api/cases`, `/api/config`
- 80% read / 20% navigation
- Weight: `wait_time = between(1, 3)`

**`tests/load/run_bench.sh`:**
- `locust -f locustfile.py --headless -u 50 -r 10 -t 60s --csv=results_${TAG} --html=report_${TAG}.html`
- Default tag: `baseline` or `after`
- Calls `diff_results.py` to emit markdown table comparing the two

**`tests/load/diff_results.py`:**
- Reads two Locust CSV history files
- Emits a markdown table with: requests/s, p50/p95/p99, failure %, median, total RPS
- Non-zero exit if any acceptance threshold fails

**`tests/load/README.md`:**
- How to run baseline vs after
- Threshold table
- Notes on not committing CSV/HTML artifacts (gitignored)

## 4. Testing Strategy

### 4.1 Unit Tests

**`tests/unit/test_gzip_middleware.py` (pytest + httpx AsyncClient):**

| Case | Assertion |
|---|---|
| Response > 1000B | `Content-Encoding: gzip` header present; decompressed body matches original |
| Response < 1000B | `Content-Encoding` header absent |
| Streaming response | `StreamingResponse` not broken (chunked transfer preserved) |
| 4xx/5xx responses | Still get gzipped (FastAPI default behavior) |

**`tests/unit/test_lazy_routes.py` (Vitest + React Testing Library):**

| Case | Assertion |
|---|---|
| Suspense fallback renders | During route transition, `<Spin />` is visible |
| 6 pages are async | `App.tsx` source contains 6 `React.lazy` (or `lazy(`) calls; 0 static `import` of page files |
| Initial bundle excludes pages | `npm run build` output: `DashboardPage`, `CasebasePage`, etc. only in dynamic chunks, not in `index-*.js` |

> Prerequisite: project must have React Testing Library available. If not, task 1 includes "set up RTL if missing" as a sub-step.

### 4.2 Locust Acceptance Gate

Two runs with the same `run_bench.sh` parameters:

| Metric | Baseline | Target (after) | Fail Threshold |
|---|---|---|---|
| Error rate | 0% | <5% | ≥5% |
| Avg response | 881ms | <3000ms | ≥3000ms |
| P95 | 1495ms | <6000ms | ≥6000ms |
| Throughput | 5.47 req/s | **≥6.5 req/s** (conservative +20%) | <6.0 |
| First-screen JS bundle | TBD baseline | -40% vs baseline | no significant drop |

**Failure handling:**
- Any metric crosses fail threshold → `run_bench.sh` exits non-zero
- PR is blocked from merge
- Either re-tune or revert

### 4.3 Not Covered Here
- E2E (Playwright) for performance — overkill at P0
- CI integration of Locust — reserved for P1/P2 CI overhaul
- A/B traffic splitting

## 5. Acceptance Criteria & Rollback

### 5.1 Done Definition

**Code gates (all must pass):**
- [ ] `openspec validate perf-p0-gzip-and-route-lazy --strict` passes
- [ ] `uv run pytest` all green
- [ ] `npm test` all green
- [ ] `npm run build` succeeds, no new TS/Vite warnings
- [ ] `ruff check .` passes
- [ ] Locust after-run meets threshold table

**Functional gates (manual + Locust):**
- [ ] All 6 routes navigate correctly, Spin fallback visible during transition
- [ ] DevTools Network panel: large responses show `Content-Encoding: gzip`
- [ ] DevTools Network panel: first-screen chunk does not contain page-specific code
- [ ] PR description includes Locust diff table

**Documentation gates:**
- [ ] `docs/rectification/24-…-perf-p0-design-report.md` generated
- [ ] OpenSpec change dir complete with proposal/specs/design/tasks/plan

### 5.2 Rollback

| Change | Rollback command | Blast radius |
|---|---|---|
| GZIP middleware | `git revert <GZIP-sha>` or comment out the `add_middleware` line | Single line in main.py; sub-second |
| Lazy routes | `git revert <lazy-sha>` or change `lazy()` back to static `import` | Single file (App.tsx); sub-second |

**Rollback triggers:**
- Locust after-run crosses fail threshold on any metric
- Any route transition shows white screen > 1s
- Streaming API response (`/api/cluster/{id}/matched-lines`) shows content truncation

### 5.3 Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Suspense boundary causes route-flash | Med | Med | Spin fallback covers visually |
| antd loaded in first-screen chunk | Med | Med | manualChunks splits vendor-antd |
| Locust state coupling to data/output | Low | Low | Reset `data/output` between runs |
| GZIP raises CPU on small responses | Low | Low | minimum_size=1000 controls |
| GZIP breaks streaming response | Low | High | Unit test covers `StreamingResponse` |
| React Testing Library not installed | Med | Low | Task 1 includes setup sub-step |

## 6. Task Breakdown (3 tasks)

Per user choice, granular = 3 tasks:

1. **task-1-route-lazy-loading**: 方案 A — convert 6 page imports to `React.lazy`, add `Suspense`, optional `manualChunks`, unit tests. Independent commit.
2. **task-2-gzip-middleware**: 方案 F — add `GZIPMiddleware` in `main.py`, unit tests. Independent commit.
3. **task-3-load-test-and-acceptance**: Locust `locustfile.py` + `run_bench.sh` + `diff_results.py` + `README.md`; run baseline (on main) and after (on branch); emit `tests/load/results_diff.md`; **also scaffold `openspec/changes/perf-p0-gzip-and-route-lazy/`** with `proposal.md`, `specs/`, `design.md`, `tasks.md`, `plan.md`; generate `docs/rectification/24-…-perf-p0-design-report.md` (Phase 4 style closure report). Final commit.

Dependency: task-3 depends on task-1 and task-2 being merged (or at least committed) so the "after" Locust run exercises the post-change code.

Each task is independently committable and verifiable.

## 7. Compliance with Project Constraints

| Constraint | Compliance |
|---|---|
| File system is source of truth | ✅ No new database; Locust CSV is gitignored |
| No mandatory database | ✅ |
| Stream large logs | ✅ GZIP tested with streaming responses; no analyzer changes |
| Retrieval without embeddings | ✅ No retrieval changes |
| AI diagnosis is assistive | ✅ No diagnosis changes |
| Living specs unchanged | ✅ No `openspec/specs/**` edits in this change |
| Governance config untouched | ✅ No `openspec/config.yaml` or schema edits |
| SuperSpec pilot rules | ✅ Real business capability, small scope, no schema/infra |
