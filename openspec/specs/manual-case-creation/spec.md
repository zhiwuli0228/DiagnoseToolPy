# Manual Case Creation

## Purpose

API endpoint and service for creating fault cases manually without requiring log analysis. Supports cold-start environments, legacy system migration, and known fault pattern initialization. All data stored as files with no database required.

## Requirements

### Requirement: Manual Case Creation Service
The casebase module SHALL provide a service function for creating fault cases manually without analysis task artifacts.

#### Scenario: Create manual case with required fields
- **WHEN** create_manual_case is called with title, case content, and required metadata
- **THEN** it creates a case directory with case.md and metadata.yaml
- **AND** metadata.yaml contains source_type=manual
- **AND** status is set to provided status (DRAFT or ARCHIVED)

#### Scenario: Create manual case auto-generates slug from title
- **WHEN** create_manual_case is called without a slug
- **THEN** a slug is auto-generated from the title (lowercase, spaces to hyphens, non-alphanumeric removed)

#### Scenario: Create manual case generates unique case_id
- **WHEN** create_manual_case is called
- **THEN** a case_id is generated following pattern CASE-{timestamp}
- **AND** if collision occurs, a random suffix is appended

### Requirement: Manual Case API Route
The API module SHALL provide a POST route for manual case creation.

#### Scenario: POST /api/cases creates manual case
- **WHEN** POST /api/cases is called with title and content
- **THEN** a new manual case is created with source_type=manual
- **AND** case.md contains the provided content
- **AND** metadata.yaml contains the provided title and metadata

#### Scenario: POST /api/cases with minimal input
- **WHEN** POST /api/cases is called with only title
- **THEN** a case is created with auto-generated slug and default metadata
- **AND** case content is empty or minimal

#### Scenario: POST /api/cases updates index
- **WHEN** POST /api/cases creates a case with status ARCHIVED
- **THEN** the case index at data/cases/index.yaml is updated with the new case entry

#### Scenario: POST /api/cases validation error
- **WHEN** POST /api/cases is called with missing title
- **THEN** HTTP 422 is returned with validation error details

### Requirement: Manual Case Boundary Preservation
The manual case creation feature MUST remain independent from AI providers and embedding models.

#### Scenario: Manual case creation does not call AI
- **WHEN** create_manual_case is called
- **THEN** no AI API is called
- **AND** no embedding model is invoked

#### Scenario: Manual case creation does not use database
- **WHEN** create_manual_case is called
- **THEN** all data is stored as files
- **AND** no database connection is made
