## ADDED Requirements

### Requirement: Progress Polling Endpoint
The system SHALL provide a GET /api/cluster/{task_id} endpoint that returns current task status, progress percentage, and current step description.

#### Scenario: Poll running task
- **WHEN** client calls GET /api/cluster/abc123 while task is running
- **THEN** system returns { status: "scanning|aggregating|matching", progress: 0-80, current_step: "..." }

#### Scenario: Poll completed task
- **WHEN** client calls GET /api/cluster/abc123 after task completes
- **THEN** system returns { status: "done", progress: 100, clusters: [...] }

#### Scenario: Poll non-existent task
- **WHEN** client calls GET /api/cluster/nonexistent
- **THEN** system returns HTTP 404

---

### Requirement: Progress Persistence
The system SHALL persist task progress to data/output/{task_id}/progress.json, updating at each phase transition.

#### Scenario: Write initial progress
- **WHEN** cluster task is created
- **THEN** system writes progress.json with { status: "scanning", progress: 0, current_step: "扫描日志中..." }

#### Scenario: Update progress at aggregation start
- **WHEN** scanning phase completes and aggregation begins
- **THEN** system updates progress.json to { status: "aggregating", progress: 50, current_step: "异常聚类中..." }

#### Scenario: Update progress at completion
- **WHEN** all phases complete
- **THEN** system updates progress.json to { status: "done", progress: 100, current_step: "分析完成" }

---

### Requirement: Session-level Task Cleanup
The system SHALL not persist clustering results beyond the user session. Task directories are temporary and can be cleaned up when the session ends.

#### Scenario: Session cleanup (implementation detail)
- **WHEN** a user closes the browser/tab
- **THEN** task directories in data/output/ remain but are eligible for cleanup
- **THEN** historical cases saved to data/cases/ are NOT affected by session end

---

### Requirement: Minimum Polling Interval
The system SHALL not require clients to poll more frequently than every 2 seconds to avoid excessive load.

#### Scenario: Frontend polling
- **WHEN** frontend polls GET /api/cluster/{task_id}
- **THEN** frontend SHOULD wait at least 2 seconds between polls
- **THEN** system handles rapid polling gracefully without errors