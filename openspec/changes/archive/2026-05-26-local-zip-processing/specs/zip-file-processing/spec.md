# ZIP File Processing Specification

## Purpose

Define server-side ZIP file handling where the frontend passes only a file path string, and the backend performs extraction and log reading without any file content upload.

## ADDED Requirements

### Requirement: ZIP Path Check API
The system SHALL accept a `.zip` file path in the source check API and verify the ZIP file is valid and accessible.

#### Scenario: Valid ZIP path check succeeds
- **WHEN** a client checks a path pointing to a valid `.zip` file that exists and is readable
- **THEN** the system returns a successful response indicating the ZIP is valid

#### Scenario: Invalid or missing ZIP path is rejected
- **WHEN** a client checks a `.zip` path that does not exist or is not a valid ZIP file
- **THEN** the system returns a client error indicating the ZIP is invalid or inaccessible

### Requirement: ZIP Automatic Extraction
The system SHALL, when a `.zip` path is provided to the scan API, automatically extract the ZIP contents to a temporary directory before scanning.

#### Scenario: ZIP file is extracted to temp directory on scan
- **WHEN** a client scans a path with `.zip` extension
- **THEN** the system extracts the ZIP to `data/temp/zip-{uuid}/` and returns the extracted directory path in the response

#### Scenario: ZIP extraction failures are reported
- **WHEN** a client scans a path with `.zip` extension but the ZIP is corrupted or password-protected
- **THEN** the system returns an error indicating the ZIP could not be extracted

### Requirement: Extracted Path Tracking
The system SHALL track extracted ZIP directories and associate them with a task identifier for later cleanup.

#### Scenario: Extracted path is returned in scan response
- **WHEN** a scan operation extracts a ZIP file
- **THEN** the response includes `extracted_path` field containing the absolute path to the extracted directory

#### Scenario: Extraction creates unique temp directories
- **WHEN** the same ZIP file is scanned twice
- **THEN** each scan creates a separate temp directory with a unique identifier to avoid conflicts

### Requirement: Temp Directory Cleanup API
The system SHALL provide an API endpoint to delete a previously extracted temporary directory.

#### Scenario: Cleanup deletes extracted directory
- **WHEN** a client calls `DELETE /api/source/temp/{task_id}` with a valid task_id
- **THEN** the system removes the corresponding temp directory and all its contents

#### Scenario: Cleanup with invalid task_id returns error
- **WHEN** a client calls `DELETE /api/source/temp/{task_id}` with a non-existent task_id
- **THEN** the system returns a 404 error indicating the temp directory was not found

### Requirement: No File Upload Required
The system SHALL process ZIP files through path-based access only — no multipart file upload mechanism is used for ZIP handling.

#### Scenario: ZIP processing uses server filesystem access
- **WHEN** a client provides a ZIP file path to the API
- **THEN** the system reads the ZIP directly from the server filesystem using the provided path, not via HTTP upload
