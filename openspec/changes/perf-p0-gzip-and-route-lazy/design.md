# Design: perf-p0

See `docs/superpowers/specs/2026-06-04-perf-p0-gzip-and-route-lazy-design.md`
for the full design rationale. This file summarizes the technical
shape for change review.

## Components

### 1. Frontend — App.tsx transformation
- 6 page imports become `React.lazy(() => import(...))`
- New top-level `<Suspense fallback={<Spin />}>` wraps the existing `<Layout>`
- No new runtime dependency

### 2. Backend — main.py middleware
- `app.add_middleware(GZIPMiddleware, minimum_size=1000)` inserted
  after `CORSMiddleware` (GZIP inside CORS so CORS headers see
  `Content-Encoding`)
- 1 line of code change + 1 import line

### 3. Load test — tests/load/
- Locust scenario: mixed `DiagnoseUser` with health/cases/config
  endpoints (80% read / 20% navigation)
- `run_bench.sh` with `--csv` output for diff
- `diff_results.py` enforces acceptance thresholds; non-zero exit on
  failure

## Why
Aligns with `docs/performance-optimization-design.md` P0 priorities.
First-screen chunking and HTTP-level compression are the two lowest-risk,
highest-ROI wins identified by the original stress test.
