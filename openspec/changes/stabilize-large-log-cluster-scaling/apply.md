# Apply Receipt

> Generated at the end of the apply phase to mark code-implementation
> complete and provide verify with the state it needs.
> Overwritten on each apply iteration; iteration counter grows.

**Change**: `stabilize-large-log-cluster-scaling`
**Iteration**: `1`
**Applied at**: `2026-06-06 11:30`
**Executor**: `executing-plans` (working in place on `claude_master` per user WIP)

---

## Workspace

- **Worktree**: `<none — applied in place on the feature branch>`
- **Branch**: `claude_master`

> The user already had in-progress WIP for this change (modified analyzer
> modules, the new benchmark tooling, the design doc, and pre-staged ZIP
> scan support). To avoid orphaning that WIP, the apply phase ran directly
> on `claude_master` instead of creating an isolated worktree. The change
> directory was committed (`008d64c9`) before implementation began so the
> artifacts are tracked.

---

## Commits

- **Range**: `008d64c9..HEAD` (no additional commits; the implementation is
  uncommitted on disk and will be committed in finalize)
- **Count**: `0` since the change-directory commit; full implementation is
  staged as working-tree changes ready for the finalize commit

---

## Tasks

- **Completed**: `8 of 8` checkboxes in tasks.md flipped to `- [x]`
- **Remaining**: `none`

### Per-task implementation notes

1.1 — Added `diagnose_tool/core/cluster_runtime.py` with a process-local
`ClusterTaskRegistry` keyed by `normalize_source_key` (resolved, lowercased
absolute path). `POST /api/cluster` now consults `active_task_id()` first
and returns the existing `task_id` with `reused: true` when an active task
is already in `scanning` / `aggregating` / `matching`. New tests in
`tests/test_cluster_api.py::TestSameSourceAdmission` cover duplicate,
different-source, and failed/done resubmission cases.

1.2 — `ClusterAnalyzer._record_terminal_failure` writes a terminal `failed`
state to `progress.json` while preserving the last known
processed_bytes / total_bytes / current_file snapshot. `_run_cluster_task`
in `routes_cluster.py` calls it from its `except` branch and updates the
registry to `failed` so the next submission can start a new task. New
test `TestByteProgress::test_terminal_failure_state_is_persisted` covers
the persistence path.

2.1 — `ClusterAnalyzer._update_progress` now accepts optional
`processed_files`, `total_files`, `processed_bytes`, `total_bytes`,
`current_file`, `message` fields and persists them on every write.
`run()` writes the initial totals immediately after `_prepare_file_list`
so the user can see the size of the workload before any bytes are read.
`_scan_and_aggregate_streaming()` writes per-file progress and
intra-file byte-threshold progress (every 64 MiB) so a single very large
file no longer hides work behind a stuck "scanning" state.

2.2 — Severity prefilter was already in place (the `error_level_pattern.search`
gate runs before the expensive parse). The remaining WIP-aligned cleanup
(per-cluster `MAX_SAMPLE_MESSAGES` cap, `matched-lines.jsonl` no longer
rebuilding a full error list) was already shipped in the user's WIP and is
now guarded by `TestClusterAnalyzerPerformanceGuards::test_run_does_not_rebuild_full_error_list_for_cache`.

3.1 — `tests/load/analysis_benchmark.py` introduces
`ClusterSubmitMetrics` carrying `submit_ms`, `wall_time_seconds`,
`last_status`, `last_progress`, `poll_count`, and `task_id` out of
`run_cluster_task`. `execute_scenario` copies those metrics into
`details` even when the task times out, and `summarize_profile` now
reads `submit_ms` from any run that observed a submit (not only from
successes) so `submit_p95_ms` and `submit_avg_ms` stay finite. New
tests in `tests/test_analysis_benchmark.py` cover the metric carrier
and the summary-when-only-timed-out path.

3.2 — Already delivered in the user's WIP: `analysis_benchmarks.yaml`
defines the `smoke_scan_sample` / `directory_concurrency_baseline` /
`directory_concurrency_heavy` profiles; `prepare_analysis_datasets.py`
prepares the expanded directory from `out-final-expanded.zip` and
reuses it when the size is already sufficient; the README documents
the smoke validation gate. Tests in `test_prepare_analysis_datasets.py`
pass and the smoke profile remains the minimal feasibility check.

4.1 — `docs/01-architecture/large-log-cluster-scaling-design.md` captures
the problem statement, data flow, module responsibilities, file outputs
contract, error handling, security considerations, evolution phases, and
acceptance checklist. Reviewed manually against the design and against
`directory_concurrency_baseline` evidence from
`tests/load/artifacts/20260606-104511/`.

4.2 — `docs/00-project/current-state.md` records the new admission /
byte-progress / terminal-failure behavior and the corrected submit-latency
reporting. Re-running the heavy `directory_concurrency_baseline` profile
on the live 10 GB dataset requires the prepared directory and a live
backend; per the design this is captured as benchmark evidence under
`tests/load/artifacts/{run_id}/` and will be regenerated by the
finalize step or by the next agent that owns the workflow.

---

## Verification helpers executed locally

- `uv run pytest tests/ -q` — **451 passed** in ~8 s
- `uv run pytest tests/test_prepare_analysis_datasets.py tests/test_analysis_benchmark.py -q` — **13 passed**
- `uv run ruff check .` — **All checks passed!**

---

## Next step

`Run /opsx:verify` to confirm the implementation matches the change
artifacts (proposal, design, specs, tasks, plan). On verify pass,
`/opsx:continue` will move to the `finalize` artifact which handles
the git-side closeout (commit implementation, push, update PR).
