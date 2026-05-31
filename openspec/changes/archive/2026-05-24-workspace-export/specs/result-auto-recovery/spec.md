# result-auto-recovery

## ADDED Requirements

### Requirement: System detects result.md in workspace directory

After workspace export, the frontend SHALL periodically check if the user has saved a diagnosis result as `result.md` in the exported workspace directory.

#### Scenario: Detection polling mechanism
- **WHEN** workspace is exported and user is on result awaiting page
- **THEN** frontend SHALL poll the workspace directory every 5 seconds for result.md
- **AND** polling SHALL continue for up to 30 minutes after export

#### Scenario: result.md detected
- **WHEN** polling finds result.md in workspace directory
- **THEN** frontend SHALL show notification: "Diagnosis result detected. Import?"
- **AND** notification SHALL have [Import] and [Dismiss] buttons

#### Scenario: result.md not yet created
- **WHEN** user is awaiting diagnosis completion
- **THEN** no notification is shown
- **AND** system continues polling silently

### Requirement: result.md content is validated before import

Imported result.md SHALL be validated to ensure it contains meaningful diagnostic content.

#### Scenario: Valid result.md content
- **WHEN** result.md is detected and opened
- **THEN** system SHALL validate:
  - File is not empty
  - Content length > 100 characters
  - Content does not match the original prompt

#### Scenario: result.md content validation fails
- **WHEN** result.md exists but validation fails
- **THEN** system SHALL NOT show import notification
- **AND** polling continues normally

### Requirement: Manual detection trigger

User SHALL be able to manually trigger result.md detection at any time.

#### Scenario: Manual detection button
- **WHEN** user is on workspace export success page
- **THEN** there SHALL be a [Check for Result] button
- **AND** clicking it SHALL immediately check for result.md

#### Scenario: Manual detection when no workspace exported
- **WHEN** user clicks [Check for Result] without exporting workspace first
- **THEN** system SHALL show message: "Please export workspace first"

### Requirement: Import result.md as diagnosis

When user confirms import, the result.md content SHALL be saved as the diagnosis for the current session/task.

#### Scenario: Import confirmation
- **WHEN** user clicks [Import] on result notification
- **THEN** system SHALL:
  - Read content from result.md
  - Save to session/task's diagnosis record
  - Stop polling for this workspace
  - Show success message

#### Scenario: Import to existing session
- **WHEN** user imports result to an existing conversation session
- **THEN** system SHALL append the imported content as the final diagnosis turn

#### Scenario: Import creates new case draft
- **WHEN** user imports result for a task without existing case
- **THEN** system SHALL create a case draft with the imported diagnosis

### Requirement: result.md format detection

System SHALL attempt to detect the format of result.md content.

#### Scenario: Markdown format detected
- **WHEN** result.md contains markdown headers
- **THEN** system SHALL preserve markdown formatting when saving

#### Scenario: Plain text format
- **WHEN** result.md is plain text without markdown
- **THEN** system SHALL wrap content appropriately when saving

### Requirement: Detection state persistence

Detection polling state SHALL be persisted to allow resumption on page reload.

#### Scenario: Page reload during polling
- **WHEN** user reloads the page while polling is active
- **THEN** system SHALL restore polling state from localStorage
- **AND** resume polling from the last known workspace directory

#### Scenario: Polling timeout after 30 minutes
- **WHEN** 30 minutes pass without result detection
- **THEN** system SHALL stop polling
- **AND** show message: "Result detection timed out. You can manually import later."
