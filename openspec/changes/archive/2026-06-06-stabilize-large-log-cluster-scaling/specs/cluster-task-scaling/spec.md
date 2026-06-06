## ADDED Requirements

### Requirement: Same-Source Cluster Admission
The cluster API MUST prevent redundant concurrent full scans for the same normalized source path.

#### Scenario: Duplicate same-source request reuses active task
- **WHEN** a client submits `POST /api/cluster` for a source path that already has an active cluster task in `scanning` or `matching`
- **THEN** the system returns the active task identity instead of starting a second full scan for the same source

#### Scenario: New source request starts new task
- **WHEN** a client submits `POST /api/cluster` for a source path that has no active cluster task
- **THEN** the system creates a new cluster task and persists initial runtime state for that source

#### Scenario: Failed task does not block resubmission forever
- **WHEN** the most recent cluster task for a source path has entered a terminal failed or timed-out state
- **THEN** a later request for the same source path MUST be allowed to create a new task

---

### Requirement: Byte-Based Cluster Progress
Cluster task progress MUST reflect processed bytes and current file context for large-directory scans.

#### Scenario: Progress file contains byte fields during scan
- **WHEN** a cluster task is scanning a source directory
- **THEN** `data/output/{task_id}/progress.json` includes `processed_bytes`, `total_bytes`, and a message or field identifying the current file being scanned

#### Scenario: Progress advances within a very large file
- **WHEN** a cluster task is scanning a source that contains a small number of very large files
- **THEN** progress updates MUST continue to advance before the current file finishes instead of waiting for the next file boundary

#### Scenario: Terminal progress is explicit
- **WHEN** a cluster task completes, fails, or times out
- **THEN** `progress.json` records a terminal status and MUST NOT remain indefinitely in `scanning`

---

### Requirement: Bounded Large-Source Scan Behavior
Cluster scanning MUST preserve streaming reads and bounded memory behavior while processing large directories.

#### Scenario: Cluster scan remains streaming
- **WHEN** a cluster task processes a multi-gigabyte log file
- **THEN** the implementation reads the file incrementally and MUST NOT load the full file into memory

#### Scenario: Non-matching lines avoid unnecessary clustering work
- **WHEN** a scanned line does not match the severity gate for clustering
- **THEN** the system skips expensive clustering-specific parsing and grouping for that line

#### Scenario: Sample retention stays bounded
- **WHEN** a cluster group has more matching events than the configured sample bound
- **THEN** the system retains only bounded representative samples for cluster output and diagnosis cache artifacts

---

### Requirement: Large-Source Failure Semantics
Cluster tasks MUST fail with observable bounded semantics when configured limits are exceeded.

#### Scenario: Timeout is observable
- **WHEN** a cluster task exceeds the configured cluster timeout
- **THEN** the task records a failed terminal state with the last known progress and reason instead of remaining silently active

#### Scenario: Partial output does not masquerade as success
- **WHEN** a cluster task terminates before clustering completes
- **THEN** the system MUST NOT write a success result that implies the task finished normally
