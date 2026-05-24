## ADDED Requirements

### Requirement: Cluster Task Creation
The system SHALL accept a log source path and create an asynchronous clustering task, returning a task_id immediately for progress tracking.

#### Scenario: Successful task creation
- **WHEN** user submits a log path via POST /api/cluster
- **THEN** system creates a task directory at data/output/{task_id}/
- **THEN** system writes initial progress.json with status "scanning" and progress 0
- **THEN** system returns task_id to the caller

#### Scenario: Invalid source path
- **WHEN** user submits a non-existent or inaccessible path
- **THEN** system returns HTTP 400 with error detail

---

### Requirement: Asynchronous Clustering Execution
The system SHALL perform clustering asynchronously without blocking the API response, updating progress as analysis proceeds.

#### Scenario: Progress tracking during scanning
- **WHEN** clustering task is in "scanning" phase
- **THEN** GET /api/cluster/{task_id} returns status "scanning" and progress 20

#### Scenario: Progress tracking during aggregation
- **WHEN** clustering task is in "aggregating" phase
- **THEN** GET /api/cluster/{task_id} returns status "aggregating" and progress 50

#### Scenario: Progress tracking during matching
- **WHEN** clustering task is in "matching" phase
- **THEN** GET /api/cluster/{task_id} returns status "matching" and progress 80

#### Scenario: Progress tracking on completion
- **WHEN** clustering task has completed all phases
- **THEN** GET /api/cluster/{task_id} returns status "done" and progress 100
- **THEN** response includes the full clustering results

---

### Requirement: Error Log Extraction
The system SHALL scan the log source and extract all ERROR, WARN, and WARNING level log lines as input for clustering.

#### Scenario: Extract ERROR/WARN/WARNING from single file
- **WHEN** scanning a .log file
- **THEN** system extracts all lines matching ERROR, WARN, or WARNING patterns
- **THEN** extracted lines are stored with timestamp, thread, level, raw content

#### Scenario: Extract from multiple files
- **WHEN** scanning a directory containing multiple .log files
- **THEN** system processes all supported file types (.log, .txt, .out, .err, .gz)
- **THEN** results are aggregated across all files

#### Scenario: Extract from ZIP archive
- **WHEN** user selects a .zip file as log source
- **THEN** system streams and decompresses .gz files inside the ZIP without full extraction
- **THEN** system also reads plain log files (.log, .txt, .out, .err) inside the ZIP
- **THEN** ERROR/WARN/WARNING lines are extracted from all decompressed content

---

### Requirement: Exception-based Clustering
The system SHALL group extracted log lines by exception class name, using the most recent exception class as the group key.

#### Scenario: Group by exception class
- **WHEN** log lines contain "JedisConnectionException"
- **THEN** all such lines are grouped under key "JedisConnectionException"

#### Scenario: Fallback to message template when no exception
- **WHEN** a log line has no exception class but has a message
- **THEN** system normalizes the message (replacing numbers/strings with placeholders)
- **THEN** lines with similar normalized templates are grouped together

---

### Requirement: Cluster Result Output
The system SHALL output clustering results including exception class, count, sample messages, and time distribution for each group.

#### Scenario: Successful clustering output
- **WHEN** clustering completes
- **THEN** system writes cluster-result.json containing all groups
- **THEN** each group includes exception_class, count, sample_messages (max 10), time_distribution

#### Scenario: Empty result when no errors found
- **WHEN** scanning completes but no ERROR/WARN lines found
- **THEN** system returns empty clusters array with status "done"

---

### Requirement: Time Distribution Calculation
The system SHALL calculate time distribution for each cluster, identifying peak hour and time range.

#### Scenario: Calculate time distribution
- **WHEN** aggregating log lines into a cluster
- **THEN** system extracts timestamps from all lines in the cluster
- **THEN** system identifies the hour with most events (peak_hour)
- **THEN** system calculates the range from first to last event (range)

---

### Requirement: Encoding Auto-Detection
The system SHALL auto-detect file encoding to correctly parse Chinese character logs.

#### Scenario: Detect GB18030 for Chinese logs
- **WHEN** reading a log file with high byte density (>15% bytes > 0x7F)
- **THEN** system uses GB18030 encoding to decode the file
- **THEN** Chinese characters are displayed correctly without garbling

#### Scenario: Detect UTF-8 for standard logs
- **WHEN** reading a log file with low byte density
- **THEN** system uses UTF-8 encoding by default
- **THEN** ASCII and UTF-8 content is decoded correctly

#### Scenario: Fallback for gzipped content in ZIP
- **WHEN** reading a .gz file inside a ZIP archive
- **THEN** system tries UTF-8 first, then GB18030 for Chinese logs
- **THEN** system falls back to latin-1 if both fail