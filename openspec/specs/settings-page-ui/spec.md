# settings-page-ui Specification

## Purpose
TBD - created by archiving change settings-page-config. Update Purpose after archive.
## Requirements
### Requirement: Settings page displays application configuration

The Settings page SHALL fetch and display the current application configuration from `GET /api/config`. The displayed information SHALL include: app name, app version, server port, data directory path, allowed input roots list, and LLM configuration (enabled status, model, base URL, timeout).

#### Scenario: Settings page loads configuration on mount
- **WHEN** the user navigates to the Settings page
- **THEN** the page fetches `GET /api/config`
- **AND** displays app name and version in the Application Configuration card
- **AND** displays data directory in the Application Configuration card

#### Scenario: Settings page shows loading state
- **WHEN** the user navigates to the Settings page while the API request is in flight
- **THEN** the page shows a loading indicator (e.g., skeleton or spinner)
- **AND** the configuration cards are not shown until data arrives

#### Scenario: API returns error
- **WHEN** the user navigates to the Settings page and `GET /api/config` fails
- **THEN** the page shows an error message with retry option
- **AND** the configuration cards are not shown

### Requirement: Settings page displays LLM configuration as read-only

The Settings page SHALL display the LLM configuration (enabled, model, base URL, timeout) in a read-only card. The user SHALL NOT be able to edit LLM settings from the UI.

#### Scenario: LLM is enabled
- **WHEN** the user is on the Settings page and LLM is enabled in the config
- **THEN** the LLM card shows `Enabled: true`
- **AND** shows model name, base URL, and timeout
- **AND** there are no input fields or edit buttons

#### Scenario: LLM is disabled
- **WHEN** the user is on the Settings page and LLM is disabled in the config
- **THEN** the LLM card shows `Enabled: false`
- **AND** shows model, base URL, and timeout as informational values
- **AND** there are no input fields or edit buttons

### Requirement: Settings page displays and manages allowed input roots

The Settings page SHALL display the `allowed_input_roots` list and provide controls to add new roots or remove existing ones. The UI SHALL use the `PATCH /api/config/paths` endpoint for modifications.

#### Scenario: Displays list of input roots
- **WHEN** the user is on the Settings page
- **THEN** the Allowed Input Roots card shows each root as a list item
- **AND** each item has a delete button

#### Scenario: User removes an input root
- **WHEN** the user clicks the delete button on an input root
- **THEN** the UI sends `PATCH /api/config/paths` with `action: "remove"`
- **AND** on success, the root disappears from the list
- **AND** on failure, the UI shows an error message (toast or inline)

#### Scenario: User adds a new input root
- **WHEN** the user enters a directory path in the input field and clicks Add
- **THEN** the UI validates the path is not empty
- **AND** sends `PATCH /api/config/paths` with `action: "add"` and the path
- **AND** on success, the new root appears in the list
- **AND** on failure, the UI shows an error message

#### Scenario: User tries to add duplicate root
- **WHEN** the user enters a path already in the list and clicks Add
- **THEN** the UI shows an error message (e.g., "Path already configured")
- **AND** no API call is made

#### Scenario: User tries to remove last root
- **WHEN** there is only one root in the list and the user tries to remove it
- **THEN** the UI shows an error message (e.g., "At least one root must remain")
- **AND** no API call is made

#### Scenario: User submits empty path
- **WHEN** the user clicks Add with an empty input field
- **THEN** the UI shows a validation error
- **AND** no API call is made

### Requirement: Settings page shows "configure in YAML" hint for input roots

The Allowed Input Roots card SHALL include a hint that these directories can also be configured directly in `config/app.yaml`.

#### Scenario: Hint text is visible
- **WHEN** the user is on the Settings page
- **THEN** the Allowed Input Roots card contains a hint: "Paths can also be configured directly in config/app.yaml"

