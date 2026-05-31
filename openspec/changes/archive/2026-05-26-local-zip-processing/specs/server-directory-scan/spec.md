## MODIFIED Requirements

### Requirement: Source Directory Scan API

The system SHALL provide an API that recursively scans an allowed server-side source directory and returns metadata about discovered files. When the provided path is a `.zip` file, the system SHALL first extract it to a temporary directory, then scan the extracted contents.

#### Scenario: Allowed source directory scan succeeds
- **WHEN** a client scans a directory that exists and resolves inside a configured allowed input root
- **THEN** the system returns file count, supported file count, unsupported count, total bytes, and per-file metadata

#### Scenario: ZIP file path triggers automatic extraction before scan
- **WHEN** a client scans a path with `.zip` extension
- **THEN** the system extracts the ZIP to a temp directory, then scans the extracted contents and returns the `extracted_path` in the response for subsequent operations

#### Scenario: Outside source directory scan is rejected
- **WHEN** a client scans a directory that resolves outside all configured allowed input roots
- **THEN** the system rejects the request before directory traversal starts

### Requirement: Source Directory Check API

The system SHALL provide an API that checks whether a requested server-side source directory is valid and allowed by configured whitelist roots. The check API SHALL also accept `.zip` file paths and validate they are readable ZIP archives.

#### Scenario: Allowed source directory check succeeds
- **WHEN** a client checks a directory that exists and resolves inside a configured allowed input root
- **THEN** the system returns a successful response indicating the directory is allowed

#### Scenario: ZIP file path check validates ZIP accessibility
- **WHEN** a client checks a path with `.zip` extension
- **THEN** the system verifies the ZIP file exists and is readable, returning success or an appropriate error

#### Scenario: Outside source directory check is rejected
- **WHEN** a client checks a directory that resolves outside all configured allowed input roots
- **THEN** the system returns a safe client error and does not expose arbitrary filesystem access
