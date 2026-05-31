# diagnosis-degraded-mode

## ADDED Requirements

### Requirement: Diagnosis endpoints handle LLM unavailability gracefully

When the configured LLM API is unavailable (network error, timeout, 5xx response, 503 status), all diagnosis endpoints SHALL return a structured response that includes the workspace export prompt and clear user guidance, instead of propagating a generic error.

#### Scenario: Conversation endpoint LLM failure
- **WHEN** user calls POST /api/diagnosis/conversation and LLM API returns error
- **THEN** system SHALL return 503 with body containing:
  - error_type: "llm_unavailable"
  - workspace_export_url: URL to export workspace
  - message: "AI diagnosis temporarily unavailable. You can export the workspace and diagnose manually."

#### Scenario: Search diagnosis endpoint LLM failure
- **WHEN** user calls POST /api/diagnosis/search and LLM API returns error
- **THEN** system SHALL return 503 with degraded response including workspace export option

#### Scenario: Cluster diagnosis endpoint LLM failure
- **WHEN** user calls POST /api/diagnosis/cluster and LLM API returns error
- **THEN** system SHALL return 503 with degraded response including workspace export option

#### Scenario: Standard diagnosis endpoint LLM failure
- **WHEN** user calls POST /api/diagnosis with task_id and LLM API returns error
- **THEN** system SHALL return 503 with degraded response including workspace export option

### Requirement: Degraded response structure

The degraded response SHALL have a consistent structure across all diagnosis endpoints.

#### Scenario: Degraded response format
- **WHEN** LLM is unavailable and diagnosis is requested
- **THEN** response SHALL contain:
  ```json
  {
    "degraded": true,
    "error_type": "llm_unavailable",
    "message": "Human-readable message",
    "workspace_export_url": "/api/diagnosis/export-workspace?...",
    "workspace_export_options": {
      "task_id": "...",
      "session_id": "...",
      "user_context": {...},
      "selections": [...]
    }
  }
  ```

### Requirement: Frontend handles degraded response

The diagnosis frontend (DiagnosisStudioPage) SHALL detect degraded responses and guide users to export workspace.

#### Scenario: Degraded response triggers workspace export dialog
- **WHEN** diagnosis API returns degraded response
- **THEN** frontend SHALL show dialog with:
  - Message explaining AI is unavailable
  - [Export Workspace] button
  - [Retry] button
  - Clear indication that manual diagnosis via OpenCode is available

#### Scenario: Degraded response during conversation
- **WHEN** /api/diagnosis/conversation returns degraded response during multi-turn diagnosis
- **THEN** frontend SHALL offer to export current conversation context as workspace

### Requirement: Preview prompt button available before diagnosis

Users SHALL be able to preview and export the diagnostic prompt before attempting LLM diagnosis.

#### Scenario: Preview prompt button exists
- **WHEN** user is on DiagnosisStudioPage with evidence selected
- **THEN** there SHALL be a [Preview Prompt] button alongside [Start Diagnosis]

#### Scenario: Preview prompt opens directory selector
- **WHEN** user clicks [Preview Prompt]
- **THEN** frontend SHALL open directory selector
- **AND** after directory is selected, call export workspace API
- **AND** show success dialog with [Open Directory] and [Copy Prompt Text] options

### Requirement: LLM availability check is non-blocking

LLM availability SHALL NOT be checked proactively (before user initiates diagnosis) to avoid adding latency.

#### Scenario: LLM availability only checked on diagnosis request
- **WHEN** user loads DiagnosisStudioPage
- **THEN** system SHALL NOT call LLM API to check availability
- **AND** LLM failure is only detected when user initiates diagnosis

### Requirement: Retry with exponential backoff hint

The degraded response SHALL include guidance about retrying.

#### Scenario: Retry button shows on degraded response
- **WHEN** frontend shows degraded dialog
- **THEN** there SHALL be a [Retry] button that re-attempts diagnosis
- **AND** retry button SHALL include tooltip: "LLM may become available again later"
