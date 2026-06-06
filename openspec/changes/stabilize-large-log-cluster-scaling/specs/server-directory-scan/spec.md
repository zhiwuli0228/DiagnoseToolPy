## MODIFIED Requirements

### Requirement: Source Directory Scan API
The system MUST provide an API that recursively scans an allowed server-side source directory and returns metadata about discovered files.

#### Scenario: Allowed source directory scan succeeds
- **WHEN** a client scans a directory that exists and resolves inside a configured allowed input root
- **THEN** the system returns file count, supported file count, unsupported count, total bytes, and per-file metadata

#### Scenario: Outside source directory scan is rejected
- **WHEN** a client scans a directory that resolves outside all configured allowed input roots
- **THEN** the system rejects the request before directory traversal starts

#### Scenario: Scan metadata feeds large-task byte accounting
- **WHEN** a large-directory scan result is later used to create a long-running analysis or cluster task
- **THEN** the reported `total_bytes` and per-file sizes are sufficient to drive byte-based progress accounting without reopening files for metadata-only totals
