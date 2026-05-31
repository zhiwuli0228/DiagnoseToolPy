## 1. Backend: Workspace Exporter Module

- [x] 1.1 Create `diagnose_tool/exporter/workspace_exporter.py` module with `WorkspaceExporter` class
- [x] 1.2 Implement `_build_workspace_dir()` method to create directory structure
- [x] 1.3 Implement `export_from_task_id()` to export workspace from task ID and user context
- [x] 1.4 Implement `export_from_cache()` to export workspace from search/cluster cache and selections
- [x] 1.5 Implement `export_from_session()` to export workspace from conversation session
- [x] 1.6 Create README.md template with diagnostic instructions
- [x] 1.7 Create prompt.md template with diagnosis prompt placeholders filled
- [x] 1.8 Create context files (phenomenon.md, stack.md, params.md)
- [x] 1.9 Implement evidence-pack.md export (compressed version)
- [x] 1.10 Implement cases/ directory export with up to 3 similar cases
- [x] 1.11 Implement atomic write with rollback on failure
- [x] 1.12 Add validation for workspace_dir path (writable, exists)

## 2. Backend: Export Workspace API Endpoint

- [x] 2.1 Add `POST /api/diagnosis/export-workspace` endpoint in `routes_diagnosis.py`
- [x] 2.2 Define `ExportWorkspaceRequest` Pydantic model with task_id, session_id, workspace_dir, selections
- [x] 2.3 Define `ExportWorkspaceResponse` Pydantic model with success, workspace_dir, files_written, detection_hint
- [x] 2.4 Implement request validation (at least one of task_id or session_id or cache_key required)
- [x] 2.5 Integrate `WorkspaceExporter` into the endpoint handler
- [x] 2.6 Add error handling with proper HTTP status codes

## 3. Backend: Diagnosis Degraded Mode

- [x] 3.1 Update `DiagnosisOrchestrator` to extract `_build_prompt()` as public method
- [x] 3.2 Update `/api/diagnosis/conversation` to catch `LLMClientError` and return degraded response
- [x] 3.3 Update `/api/diagnosis/search` to catch `LLMClientError` and return degraded response
- [x] 3.4 Update `/api/diagnosis/cluster` to catch `LLMClientError` and return degraded response
- [x] 3.5 Update `/api/diagnosis` (standard diagnosis) to catch `LLMClientError` and return degraded response
- [x] 3.6 Define `DegradedResponse` model with degraded, error_type, message, workspace_export_url, workspace_export_options
- [x] 3.7 Ensure all degraded responses have consistent structure per spec

## 4. Frontend: Preview Prompt Button

- [x] 4.1 Add [Preview Prompt] button to `DiagnosisStudioPage.tsx` alongside [Start Diagnosis]
- [x] 4.2 Implement directory selector using system file picker (or Ant Design `Dragger`)
- [x] 4.3 Call `POST /api/diagnosis/export-workspace` after directory selection
- [x] 4.4 Show success dialog with [Open Directory] and [Copy Prompt Text] buttons
- [x] 4.5 Implement [Copy Prompt Text] to copy prompt.md content to clipboard
- [x] 4.6 Add same [Preview Prompt] button to other diagnosis entry points (search, cluster)

## 5. Frontend: Degraded Response Handling

- [x] 5.1 Update diagnosis API client to detect degraded response
- [x] 5.2 Show degraded dialog when response has `degraded: true`
- [x] 5.3 Display message explaining AI is unavailable
- [x] 5.4 Add [Export Workspace] button in degraded dialog
- [x] 5.5 Add [Retry] button in degraded dialog
- [x] 5.6 Persist degradation state for session continuity

## 6. Frontend: Result Auto-Recovery

- [x] 6.1 Add `useResultDetection` hook for polling result.md in workspace directory
- [x] 6.2 Implement 5-second polling interval
- [x] 6.3 Implement 30-minute polling timeout
- [x] 6.4 Add [Check for Result] button on workspace export success page
- [x] 6.5 Implement result.md validation before showing import notification
- [x] 6.6 Show import notification with [Import] and [Dismiss] buttons
- [x] 6.7 Implement import logic to save result.md content as diagnosis
- [x] 6.8 Persist polling state to localStorage for page reload recovery
- [x] 6.9 Handle polling timeout with user-friendly message

## 7. Testing

- [x] 7.1 Write unit tests for `WorkspaceExporter` class
- [x] 7.2 Write unit tests for degraded response handling
- [x] 7.3 Write unit tests for result.md validation
- [x] 7.4 Write integration tests for export-workspace API endpoint
- [x] 7.5 Test workspace directory structure matches spec
- [x] 7.6 Test atomic write rollback on failure
- [x] 7.7 Test frontend degraded dialog display
- [x] 7.8 Test result detection polling and import flow

## 8. Documentation

- [x] 8.1 Update CLAUDE.md if architecture changes
- [x] 8.2 Add user documentation for workspace export feature
- [x] 8.3 Document result.md format expectations
