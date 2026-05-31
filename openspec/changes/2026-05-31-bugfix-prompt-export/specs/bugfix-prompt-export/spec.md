# bugfix-prompt-export

## ADDED Requirements

### Requirement: Bugfix Prompt Artifact Generation

The system MUST generate a bugfix prompt markdown artifact at `data/output/{task_id}/bugfix-prompt.md` from existing analysis task output artifacts.

#### Scenario: Bugfix prompt is generated from task output
- **WHEN** a user requests bugfix prompt export for a valid `task_id`
- **THEN** the system SHALL generate `data/output/{task_id}/bugfix-prompt.md`
- **AND** the file SHALL contain a structured implementation brief derived from existing task output artifacts

#### Scenario: Bugfix prompt is regenerated
- **WHEN** the user requests the bugfix prompt again for the same task
- **THEN** the system SHALL overwrite the existing `bugfix-prompt.md` deterministically
- **AND** the regenerated content SHALL reflect the current task output artifacts

### Requirement: Bugfix Prompt Content

The system MUST include the following sections in the generated bugfix prompt:

- task metadata
- problem summary
- evidence summary
- diagnosis state or hypothesis
- implementation guardrails
- suggested fix plan
- regression tests
- human confirmation questions

#### Scenario: Prompt includes implementation guardrails
- **WHEN** the bugfix prompt is generated
- **THEN** it SHALL clearly state that AI diagnosis is preliminary unless human-confirmed root cause data is available
- **AND** it SHALL instruct the implementation agent to avoid unrelated refactoring

#### Scenario: Prompt uses references only
- **WHEN** historical cases or diagnosis output are included
- **THEN** the prompt SHALL mark them as references only and SHALL NOT present them as confirmed facts for the current issue

### Requirement: Bugfix Prompt Export API

The system MUST provide an API that generates the bugfix prompt for a task and returns a safe response containing the output path and prompt content.

#### Scenario: Export succeeds for a valid task
- **WHEN** the client requests bugfix prompt export with a valid `task_id`
- **THEN** the API SHALL return success and the generated prompt content
- **AND** it SHALL return the output file path

#### Scenario: Export fails for a missing task
- **WHEN** the client requests bugfix prompt export for a task that does not exist
- **THEN** the API SHALL return a not-found style error
- **AND** it SHALL NOT create any files

### Requirement: Frontend Access to Bugfix Prompt SHALL Be Provided

The system MUST provide a UI action that lets the user generate or preview the bugfix prompt from the diagnosis workflow.

#### Scenario: User opens bugfix prompt export from diagnosis page
- **WHEN** the user clicks the bugfix prompt action on the diagnosis page
- **THEN** the UI SHALL request the prompt from the API
- **AND** it SHALL allow the user to copy or preview the generated prompt

### Requirement: Exporter Boundary Preservation

The bugfix prompt exporter MUST remain independent of FastAPI and MUST NOT load full raw log files into memory.

#### Scenario: Exporter is testable in isolation
- **WHEN** the exporter is unit tested
- **THEN** it can be invoked directly from `diagnose_tool/exporter/` without importing FastAPI
