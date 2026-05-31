# Evidence Builder

## Purpose

允许用户从搜索结果和聚类结果中选择和组织日志证据，传给大模型进行诊断。提供后端缓存机制、智能压缩能力和前端证据篮 UI。

## ADDED Requirements

### Requirement: Search Result Cache Storage

When search is executed, the system SHALL store matched log lines with context to a server-side cache file at `data/output/search-{timestamp}-{uuid}/matched-lines.jsonl`.

#### Scenario: Search stores matched lines with context
- **WHEN** user executes a log search via `POST /api/source/search`
- **THEN** the system creates `data/output/search-{timestamp}-{uuid}/` directory and writes `matched-lines.jsonl` containing each matched log event with its logical context (5 events before and after)

#### Scenario: Search returns cache key
- **WHEN** search completes successfully
- **THEN** the response includes `cache_key` in format `search-{timestamp}-{uuid}` for subsequent diagnosis calls

#### Scenario: Cache is overwritten by new search on same path
- **WHEN** user performs a new search on the same source path
- **THEN** the new search overwrites the previous cache file for that path pattern

### Requirement: Cluster Result Cache Storage

When cluster analysis completes, the system SHALL store matched log lines for each cluster group to `data/output/{cluster-task-id}/matched-lines.jsonl`.

#### Scenario: Cluster stores matched lines per group
- **WHEN** cluster analysis completes via `POST /api/cluster`
- **THEN** the system writes `matched-lines.jsonl` containing all matched log lines grouped by their cluster assignment

#### Scenario: Cluster uses task_id as cache key
- **WHEN** cluster analysis creates a task
- **THEN** the returned `task_id` serves as the `cache_key` for subsequent diagnosis calls

### Requirement: Matched Lines JSONL Structure

Each line in `matched-lines.jsonl` SHALL be a valid JSON object with the following structure:

```json
{
  "id": "<sha256-hash-of-file-path-line-no-timestamp>",
  "group_key": "<aggregation-group-key>",
  "event": {
    "timestamp": "<ISO-ish timestamp>",
    "level": "<ERROR|WARN|INFO|...>",
    "thread": "<thread-name>",
    "message": "<log-message>",
    "raw": "<full-raw-log-line>",
    "file_path": "<source-file-path>",
    "line_no": "<line-number>"
  },
  "context_before": [<previous-5-logical-events>],
  "context_after": [<next-5-logical-events>]
}
```

#### Scenario: ID is stable across expansions
- **WHEN** user expands a group to view matched lines and selects a log entry
- **THEN** the log entry ID remains the same if user collapses and re-expands the group

#### Scenario: Context is computed per logical event
- **WHEN** computing context for a multi-line stack trace log event
- **THEN** the entire stack trace is treated as one logical event for context boundary calculation

### Requirement: Custom Diagnosis from Search Cache

The system SHALL provide `POST /api/diagnosis/search` endpoint that accepts user selections from search results and returns LLM diagnosis.

#### Scenario: Diagnosis with group selection
- **WHEN** user selects an aggregation group and calls `POST /api/diagnosis/search`
- **THEN** the system retrieves all matched lines for that group from cache, compresses them, generates evidence pack, and returns diagnosis

#### Scenario: Diagnosis with single log selection
- **WHEN** user selects a single log entry and calls `POST /api/diagnosis/search`
- **THEN** the system retrieves that specific log entry with its context from cache, compresses, and returns diagnosis

#### Scenario: Diagnosis with group_all selection
- **WHEN** user selects "select all in group" and calls `POST /api/diagnosis/search`
- **THEN** the system retrieves all matched lines in that group from cache, compresses, and returns diagnosis

#### Scenario: Cache not found returns error
- **WHEN** user calls `POST /api/diagnosis/search` with an invalid or expired `cache_key`
- **THEN** the system returns HTTP 404 with detail "Cache not found"

### Requirement: Custom Diagnosis from Cluster Cache

The system SHALL provide `POST /api/diagnosis/cluster` endpoint that accepts user selections from cluster results and returns LLM diagnosis.

#### Scenario: Diagnosis with cluster group selection
- **WHEN** user selects a cluster group and calls `POST /api/diagnosis/cluster`
- **THEN** the system retrieves matched lines for that cluster from cache, compresses them, and returns diagnosis

### Requirement: Intelligent Evidence Compression

The compression module SHALL reduce selected log entries before sending to LLM while preserving diagnostic value.

#### Scenario: Compression groups by stack trace pattern
- **WHEN** compressing multiple log entries with identical stack traces
- **THEN** the system outputs one representative entry per unique stack pattern with count and time range

#### Scenario: Compression respects max_tokens budget
- **WHEN** compressed evidence would exceed `max_tokens` limit
- **THEN** the system further reduces by sampling across stack pattern groups proportionally

#### Scenario: Compression includes statistics
- **WHEN** compressing a group of similar entries
- **THEN** the output includes: total count, first occurrence, last occurrence, peak time window

#### Scenario: Compression options control output
- **WHEN** `options.include_stack` is `false`
- **THEN** stack traces are excluded from compressed output
- **WHEN** `options.include_timeline` is `true`
- **THEN** time distribution statistics are included

### Requirement: Diagnosis Response Format

The diagnosis endpoint SHALL return a JSON object with diagnosis text.

#### Scenario: Successful diagnosis response
- **WHEN** user calls diagnosis endpoint with valid selections
- **THEN** the response is `{"diagnosis": "<LLM-generated-diagnosis-text>"}`

### Requirement: Frontend Evidence Basket State

The frontend SHALL maintain an in-memory evidence basket that stores user selections.

#### Scenario: Evidence basket shows selection count
- **WHEN** user selects items
- **THEN** the basket badge displays the total number of selected items

#### Scenario: Evidence basket persists selections within session
- **WHEN** user selects items and collapses/expands groups
- **THEN** the selections are preserved

#### Scenario: Evidence basket clears on page refresh
- **WHEN** user refreshes the page
- **THEN** the evidence basket is cleared and selections are lost

### Requirement: Frontend Group Expansion

Aggregation groups in search/cluster results SHALL be collapsed by default.

#### Scenario: Group is collapsed by default
- **WHEN** search or cluster results are displayed
- **THEN** aggregation groups are shown in collapsed state with count and summary

#### Scenario: User can expand group to see individual entries
- **WHEN** user clicks to expand a group
- **THEN** the matched lines for that group are displayed in a table with checkboxes

#### Scenario: User can select individual entries within expanded group
- **WHEN** user expands a group
- **THEN** each matched line has a checkbox that can be selected independently

#### Scenario: User can select all entries in a group
- **WHEN** user expands a group
- **THEN** there is a "Select All" option to select all entries in that group

### Requirement: Diagnosis Options

User SHALL be able to specify options when requesting diagnosis.

#### Scenario: Default options
- **WHEN** user calls diagnosis without specifying options
- **THEN** default options are used: `include_stack: true`, `include_timeline: true`, `max_tokens: 2000`

#### Scenario: Custom max_tokens
- **WHEN** user specifies `max_tokens: 1000`
- **THEN** the compression module ensures output fits within 1000 tokens

## REMOVED Requirements

None.
