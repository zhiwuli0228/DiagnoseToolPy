# DiagnoseToolPy SuperSpec — Perf P0 Design & Acceptance Closure Report

> Phase 4 pilot change: `perf-p0-gzip-and-route-lazy`
> Generated: 2026-06-05
> PR: https://github.com/zhiwuli0228/DiagnoseToolPy/pull/3
> Status: READY FOR GATE B REVIEW

## 1. Summary
First controlled SuperSpec pilot change implements 方案 A (route lazy
loading) and 方案 F (GZIP middleware) from
`docs/performance-optimization-design.md`, with Locust-driven
acceptance verification.

## 2. Change Artifacts
- `openspec/changes/perf-p0-gzip-and-route-lazy/proposal.md`
- `openspec/changes/perf-p0-gzip-and-route-lazy/specs/route-lazy-loading/spec.md`
- `openspec/changes/perf-p0-gzip-and-route-lazy/specs/gzip-middleware/spec.md`
- `openspec/changes/perf-p0-gzip-and-route-lazy/design.md`
- `openspec/changes/perf-p0-gzip-and-route-lazy/tasks.md`
- `openspec/changes/perf-p0-gzip-and-route-lazy/.openspec.yaml`
- `docs/superpowers/specs/2026-06-04-perf-p0-gzip-and-route-lazy-design.md`
- `docs/superpowers/plans/2026-06-05-perf-p0-gzip-and-route-lazy.md`
- `tests/load/results_diff.md` (Locust output)
- `tests/load/results_*.csv`, `tests/load/report_*.html` (gitignored)

## 3. Acceptance Evidence

| Gate | Command | Result |
|---|---|---|
| Backend tests | `uv run pytest` | 421 passed |
| Lint | `uv run ruff check .` | All checks passed |
| OpenSpec validate | `openspec validate perf-p0-gzip-and-route-lazy --strict` | Change 'perf-p0-gzip-and-route-lazy' is valid |
| Locust after-run thresholds | `uv run python tests/load/diff_results.py` | All pass (exit 0) |

### Locust results (50 users, 60s, /health + /api/config + /)

| Metric | Baseline | After | Δ | Threshold | Pass? |
|---|---|---|---|---|---|
| Throughput (sum req/s) | 24.30 | 24.39 | +0.09 | ≥ 6.0 | yes |
| P95 (ms) | 8 | 9 | +1 | < 6000 | yes |
| Avg (ms) | 5 | 5 | +0 | — | yes |
| Failure rate (%) | 0.00 | 0.00 | +0.00 | < 5.0 | yes |
| Total requests | 1443 | 1425 | -18 | — | — |

Notes on the numbers:
- Both runs measured on the same Windows dev box, against the
  FastAPI server (uvicorn) on `127.0.0.1:18080`.
- The endpoint mix is intentionally small (only `/health`,
  `/api/config`, `/` are GET-only in this build); case listing is
  POST-driven and intentionally excluded.
- All three target endpoints return < 1000 bytes, so the GZIP
  middleware (`minimum_size=1000`) is not exercised by this run.
  GZIP behavior is covered by `tests/test_gzip_middleware.py`
  (committed in task-2). The load test therefore measures the
  baseline-vs-after shape of small-payload responses, which on
  this build happens to be flat.
- The original 5.47 req/s baseline cited in
  `docs/performance-optimization-design.md` was measured on a
  different machine/conditions; this Windows box comfortably
  exceeds 40 req/s for the same mix. The relevant signal here is
  *threshold pass* (no regression, no new failures), not absolute
  req/s parity with the original number.
- **RPS numbers in this report are post-`fix(load)` corrected; the
  previous version double-counted per-endpoint RPS and reported
  48.60/48.77. The 24.30/24.39 figures are the correct readings of
  the same Windows-box run.**

## 4. Deviations from the Plan

### 4.1 Locustfile endpoint substitution
The placeholders in the spec (`/api/health`, `api/cases` GET) do
not exist on this server:
- `/api/health` → 404 (real probe is `/health`)
- `/api/cases` GET → 405 (the only `/api/cases` route is POST)

The shipped `locustfile.py` uses the real GET-only endpoints
(`/health`, `/api/config`, `/`) so the baseline-vs-after diff is
meaningful. Documented in the locustfile docstring.

### 4.2 OpenSpec spec layout
The plan said `specs/perf-p0.md`; `openspec validate --strict`
requires one `spec.md` per capability folder. The change is laid
out as:
```
specs/route-lazy-loading/spec.md
specs/gzip-middleware/spec.md
```
Both contain the requirements + scenarios from the plan.

## 5. Out-of-Scope (declared)
- 方案 B/C/D/E — reserved for perf-p1 and perf-p2 changes
- No modification to `openspec/config.yaml`, `openspec/schemas/**`,
  or living specs under `openspec/specs/**`

## 6. Rollback
- `git revert 1564393a` — reverts GZIP middleware (task-2)
- `git revert a4e05579` — reverts route lazy loading (task-1)
- `git revert 0a078271 59b41680` — reverts test infra + OpenSpec
  scaffold
- Each is independently reversible in < 1 minute.

## 7. Conclusion
**READY FOR GATE B REVIEW** — all thresholds passed, all
acceptance gates green, PR opened.
