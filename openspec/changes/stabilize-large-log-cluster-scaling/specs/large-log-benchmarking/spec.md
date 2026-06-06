## ADDED Requirements

### Requirement: Prepared Large-Directory Benchmark Dataset
The benchmark workflow MUST support preparing a real large-directory dataset from a declared ZIP source before execution.

#### Scenario: Profile-scoped dataset preparation
- **WHEN** a benchmark is run for a specific profile
- **THEN** the dataset preparation step prepares or validates only the datasets referenced by that profile

#### Scenario: Prepared directory is size-checked
- **WHEN** a dataset declares an expected minimum size for a prepared directory
- **THEN** the preparation step validates the prepared directory size before benchmark execution proceeds

---

### Requirement: Benchmark Artifact Evidence
Large-log benchmark execution MUST produce machine-readable and human-readable artifacts in a per-run directory.

#### Scenario: Required artifacts are written
- **WHEN** a benchmark profile finishes
- **THEN** the run directory contains profile JSON, profile Markdown, `index.json`, `run-meta.json`, and `process-stats.csv`

#### Scenario: Non-zero benchmark exit is preserved
- **WHEN** a benchmark profile fails one or more acceptance checks
- **THEN** `run-meta.json` records the non-zero benchmark exit code for later review

---

### Requirement: Smoke Validation Gate
The benchmark standard MUST provide a small-scale smoke profile that validates the workflow before heavier profiles are used as evidence.

#### Scenario: Smoke profile validates wrapper path
- **WHEN** the smoke benchmark profile is executed
- **THEN** it validates preflight, dataset preparation selection, artifact directory creation, and benchmark runner invocation without requiring large-directory extraction

#### Scenario: Heavy benchmark follows smoke validation
- **WHEN** a heavier profile such as `directory_concurrency_baseline` is used as evidence
- **THEN** the smoke profile MUST be runnable as the minimal feasibility check for the same workflow

---

### Requirement: Large-Directory Cluster Acceptance Contract
The benchmark standard MUST define acceptance outcomes for real large-directory cluster execution.

#### Scenario: Baseline benchmark records cluster completion behavior
- **WHEN** `directory_concurrency_baseline` is executed against the prepared large directory
- **THEN** the resulting report records whether cluster tasks completed, timed out, or failed, including the last known progress state

#### Scenario: Same-source concurrency behavior is measurable
- **WHEN** concurrent benchmark workers submit cluster tasks for the same prepared large directory
- **THEN** the benchmark artifacts expose whether the system reused work, serialized work, or started redundant scans
