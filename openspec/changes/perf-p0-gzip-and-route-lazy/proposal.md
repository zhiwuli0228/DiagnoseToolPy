# Proposal: perf-p0-gzip-and-route-lazy

## Problem
Initial stress test in `docs/performance-optimization-design.md` showed
throughput at 5.47 req/s against a 10 req/s target. The first-screen
JS bundle ships all 6 route components in a single chunk, and the
backend does not compress responses larger than 1 KB. Both issues
inflate time-to-first-byte and reduce concurrent throughput.

## Goal
Recover at least 20% of the throughput gap (target >= 6.0 req/s; original goal was 6.5 req/s ≈ +20% over 5.47 baseline from `docs/performance-optimization-design.md`) and
shrink the first-screen JS bundle by ~40% by introducing GZIP
compression and route-level code splitting.

## Scope
- 方案 A: React.lazy + Suspense for 6 page components in App.tsx
- 方案 F: FastAPI GZIPMiddleware (minimum_size=1000) in main.py
- Locust load test with baseline/after comparison

## Out of Scope
- 方案 B (SWR/React Query client cache) — perf-p2
- 方案 C (Vite terser/gzip-static) — perf-p2
- 方案 D (backend LRU case cache) — perf-p1
- 方案 E (BM25 index preload) — perf-p1
- No modification to openspec/config.yaml, openspec/schemas/**, or
  living specs under openspec/specs/**

## Affected Modules
- diagnose_tool/main.py (1 line: add_middleware)
- frontend/src/App.tsx (lazy imports + Suspense wrapper)
- frontend/vite.config.ts (optional manualChunks)
- tests/load/* (new)
- tests/test_gzip_middleware.py (new)
- pyproject.toml (dev: +locust)

## Storage Impact
None. No data files or durable specs are modified.

## Risks
- Suspense boundary may flash a spinner on slow networks — mitigated
  by Spin fallback (antd native, well-styled)
- GZIP may raise CPU on small responses — mitigated by
  minimum_size=1000
- Streaming responses may be affected — covered by unit test

## Verification
- `uv run pytest` all green
- `npm test` all green
- `npm run build` succeeds; chunk count > 1
- Locust after-run meets P0 threshold table
- `openspec validate perf-p0-gzip-and-route-lazy --strict` passes
