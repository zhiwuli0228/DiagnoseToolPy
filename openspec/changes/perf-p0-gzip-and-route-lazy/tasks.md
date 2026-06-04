# Tasks: perf-p0-gzip-and-route-lazy

- [ ] **task-1-route-lazy-loading**: 方案 A — convert 6 page imports to React.lazy, add Suspense, optional manualChunks, unit tests. Independent commit.
- [ ] **task-2-gzip-middleware**: 方案 F — add GZIPMiddleware in main.py, unit tests. Independent commit.
- [ ] **task-3-load-test-and-acceptance**: Locust locustfile.py + run_bench.sh + diff_results.py + README.md; baseline on main, after on branch; emit results_diff.md; scaffold openspec change dir + Phase 4 closure report. Final commit.

Dependency: task-3 depends on task-1 and task-2 being committed.
