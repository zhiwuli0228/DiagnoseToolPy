# Server Directory Scan Specification

## Purpose

Define secure server-side directory checking and metadata-only recursive scanning for log source directories.

## Requirements

### Requirement: Source Directory Check API
The system MUST provide an API that checks whether a requested server-side source directory is valid and allowed by configured whitelist roots.

#### Scenario: Allowed source directory check succeeds
- **WHEN** a client checks a directory that exists and resolves inside a configured allowed input root
- **THEN** the system returns a successful response indicating the directory is allowed

#### Scenario: Outside source directory check is rejected
- **WHEN** a client checks a directory that resolves outside all configured allowed input roots
- **THEN** the system returns a safe client error and does not expose arbitrary filesystem access

#### Scenario: Missing source path is rejected
- **WHEN** a client calls the check API without a source path
- **THEN** the system returns a safe client error indicating the request is invalid

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

### Requirement: Metadata-Only Recursive Scanner
The system MUST recursively scan filesystem metadata without opening or reading log file contents.

#### Scenario: Nested files are discovered
- **WHEN** an allowed source directory contains files in nested subdirectories
- **THEN** the scanner includes those files in the scan result metadata

#### Scenario: File contents are not read
- **WHEN** the scanner processes files during a source directory scan
- **THEN** it uses filesystem metadata such as path and size and MUST NOT read log contents into memory

### Requirement: Supported Log File Detection
The system MUST classify files with `.log`, `.txt`, `.out`, `.err`, and `.gz` extensions as supported log files using case-insensitive extension matching.

#### Scenario: Supported extensions are counted
- **WHEN** a scanned directory contains `.log`, `.txt`, `.out`, `.err`, and `.gz` files
- **THEN** the scan result counts those files as supported and reports each file type

#### Scenario: Unsupported extensions are counted separately
- **WHEN** a scanned directory contains files with unsupported extensions
- **THEN** the scan result counts those files as unsupported without reading their contents

### Requirement: Scan Result Shape
The system MUST return a structured scan result containing aggregate counts and per-file fields needed by future analysis task creation.

#### Scenario: Scan result includes required fields
- **WHEN** a source directory scan succeeds
- **THEN** the response includes `file_count`, `supported_file_count`, `unsupported_file_count`, `total_bytes`, and file entries with `path`, `name`, `size`, and `type`

### Requirement: Implementation State Is Documented
The system MUST update the project continuity snapshot after the server directory scan implementation is complete.

#### Scenario: Current state reflects scan completion
- **WHEN** the implementation tasks for this change are completed
- **THEN** `docs/00-project/current-state.md` records the server directory scan API as implemented while leaving out-of-scope analyzer, casebase, retrieval, and deployment work incomplete
