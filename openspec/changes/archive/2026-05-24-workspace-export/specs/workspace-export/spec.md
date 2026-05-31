# workspace-export

## ADDED Requirements

### Requirement: User can export diagnostic workspace to a selected directory

The system SHALL provide a workspace export capability that copies complete diagnostic context (log evidence, user context, similar cases, diagnosis instructions) into a user-specified directory, organized in a subdirectory structure that OpenCode can directly read.

#### Scenario: Export workspace from task ID
- **WHEN** user initiates workspace export with a valid task ID and user context
- **THEN** system SHALL create the following directory structure in the user-specified path:
  ```
  {workspace_dir}/
  ├── README.md
  ├── prompt.md
  ├── context/phenomenon.md
  ├── context/stack.md
  ├── context/params.md
  ├── logs/evidence-pack.md
  └── cases/case-001.md (and additional cases)
  ```

#### Scenario: Export workspace from search selections
- **WHEN** user initiates workspace export with selected search/cluster items
- **THEN** system SHALL compress the selected evidence and export to the workspace directory

#### Scenario: Export fails on invalid directory
- **WHEN** user specifies a directory that is not writable or does not exist
- **THEN** system SHALL return an error with clear message and NOT create any files

### Requirement: Workspace directory contents

The workspace directory SHALL contain the following files with exact content requirements:

#### Scenario: README.md content
- **WHEN** workspace is created
- **THEN** README.md SHALL contain:
  - Diagnostic task overview
  - Directory structure explanation
  - Instructions to save diagnosis results as `result.md`
  - Link to open the workspace in OpenCode

#### Scenario: prompt.md content
- **WHEN** workspace is created
- **THEN** prompt.md SHALL contain the diagnosis prompt with all placeholders replaced:
  - Role definition
  - Current Fault Evidence (from logs/evidence-pack.md)
  - Similar Historical Cases (from cases/)
  - Diagnosis Instructions
  - Constraints

#### Scenario: context files content
- **WHEN** workspace is created with user context (phenomenon, stack, params)
- **THEN** system SHALL create context/phenomenon.md, context/stack.md, context/params.md with the respective content
- **WHEN** user context is empty
- **THEN** system SHALL create the file with placeholder text indicating no content provided

#### Scenario: cases directory content
- **WHEN** similar cases are found
- **THEN** system SHALL copy up to 3 case markdown files to cases/ directory
- **WHEN** no similar cases are found
- **THEN** system SHALL create cases/README.md indicating no similar cases available

### Requirement: Workspace export API

The system SHALL provide a REST API endpoint `/api/diagnosis/export-workspace` that accepts workspace export requests.

#### Scenario: Successful export via API
- **WHEN** client calls POST /api/diagnosis/export-workspace with valid task_id, user_context, and workspace_dir
- **THEN** system SHALL return 200 with success=true and files_written list

#### Scenario: Export with session-based context
- **WHEN** client calls POST /api/diagnosis/export-workspace with session_id
- **THEN** system SHALL retrieve conversation context from session store and export

#### Scenario: Export from search cache
- **WHEN** client calls POST /api/diagnosis/export-workspace with cache_key and selections
- **THEN** system SHALL resolve selections to log entries, compress, and export

### Requirement: Files are written atomically

The workspace export SHALL write files atomically to prevent partial state.

#### Scenario: Write failure mid-export
- **WHEN** write fails after some files are created
- **THEN** system SHALL roll back any created files and return error
- **AND** user-specified directory SHALL remain unchanged

### Requirement: Detection hint in response

When workspace is successfully exported, the API response SHALL include a hint about result.md detection.

#### Scenario: Export response includes detection hint
- **WHEN** workspace export succeeds
- **THEN** response SHALL include detection_hint explaining how results will be detected
