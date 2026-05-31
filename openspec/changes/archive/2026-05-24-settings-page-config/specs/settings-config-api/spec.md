## ADDED Requirements

### Requirement: GET /api/config returns full application configuration

The system SHALL expose a `GET /api/config` endpoint that returns the current application configuration including app metadata, server settings, paths configuration, and LLM provider settings. The response SHALL include the full `allowed_input_roots` list so the Settings page can display and manage input paths.

#### Scenario: Returns complete configuration
- **WHEN** a client sends `GET /api/config`
- **THEN** the response contains `app` (name, version), `server` (host, port), `paths` (allowed_input_roots, data_dir), and `llm` (enabled, model, base_url, timeout)
- **AND** all values reflect the current contents of `config/app.yaml`

#### Scenario: Config file does not exist
- **WHEN** a client sends `GET /api/config` and `config/app.yaml` is missing
- **THEN** the response returns HTTP 500 with an error message

### Requirement: PATCH /api/config/paths can add an allowed input root

The system SHALL expose a `PATCH /api/config/paths` endpoint that accepts `{ "action": "add", "path": "<directory_path>" }` and adds the specified directory to `paths.allowed_input_roots` in `config/app.yaml`. The path MUST be validated to exist and be a directory before being added. Duplicate paths SHALL be rejected.

#### Scenario: Successfully adds a new root
- **WHEN** a client sends `PATCH /api/config/paths` with `action: "add"` and a valid existing directory path
- **THEN** the directory is appended to `paths.allowed_input_roots` in `config/app.yaml`
- **AND** subsequent `GET /api/config` includes the new path in `paths.allowed_input_roots`

#### Scenario: Rejects duplicate path
- **WHEN** a client sends `PATCH /api/config/paths` with `action: "add"` and a path already in `allowed_input_roots`
- **THEN** the response returns HTTP 400 with `"detail": "Path already in allowed_input_roots"`

#### Scenario: Rejects non-existent path
- **WHEN** a client sends `PATCH /api/config/paths` with `action: "add"` and a path that does not exist
- **THEN** the response returns HTTP 400 with `"detail": "Requested path does not exist"`

#### Scenario: Rejects a file instead of directory
- **WHEN** a client sends `PATCH /api/config/paths` with `action: "add"` and a path that exists but is a file
- **THEN** the response returns HTTP 400 with `"detail": "Requested path is not a directory"`

### Requirement: PATCH /api/config/paths can remove an allowed input root

The system SHALL expose a `PATCH /api/config/paths` endpoint that accepts `{ "action": "remove", "path": "<directory_path>" }` and removes the specified directory from `paths.allowed_input_roots` in `config/app.yaml`. At least one root MUST remain after removal.

#### Scenario: Successfully removes an existing root
- **WHEN** a client sends `PATCH /api/config/paths` with `action: "remove"` and a path in `allowed_input_roots`
- **THEN** the directory is removed from `paths.allowed_input_roots` in `config/app.yaml`
- **AND** subsequent `GET /api/config` does not include the removed path

#### Scenario: Rejects removal that would leave empty list
- **WHEN** a client sends `PATCH /api/config/paths` with `action: "remove"` and there is only one root in `allowed_input_roots`
- **THEN** the response returns HTTP 400 with `"detail": "allowed_input_roots must have at least one entry"`

#### Scenario: Rejects removal of non-existent path
- **WHEN** a client sends `PATCH /api/config/paths` with `action: "remove"` and a path not in `allowed_input_roots`
- **THEN** the response returns HTTP 400 with `"detail": "Path not found in allowed_input_roots"`

### Requirement: PATCH /api/config/paths is protected by file locking

The system SHALL use a file lock when reading or writing `config/app.yaml` to prevent concurrent modification. The lock file SHALL be named `config/app.yaml.lock` and use the `filelock` library for cross-platform compatibility.

#### Scenario: Serializes concurrent write requests
- **WHEN** two clients send `PATCH /api/config/paths` simultaneously
- **THEN** requests are serialized via file lock
- **AND** one request completes before the other begins its read-modify-write cycle
- **AND** the final state of `config/app.yaml` is correct (no data loss)
