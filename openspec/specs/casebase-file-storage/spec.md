# Casebase File Storage

## Purpose

File-based fault case storage with case creation from analysis artifacts, metadata management, and rebuildable index. Fault cases are stored as `case.md` + `metadata.yaml` documents under `data/cases/{case_id}_{slug}/`.

## Requirements

### Requirement: Case Models
The casebase module SHALL provide Pydantic/dataclass models for case metadata and case structures.

#### Scenario: FaultCaseMetadata has required fields
- **WHEN** a FaultCaseMetadata object is created
- **THEN** it contains case_id, title, slug, source_type, status, confidence, tags, components, fault_modes, exception_classes, key_phrases, and created_at

#### Scenario: CaseIndexEntry has required fields
- **WHEN** a CaseIndexEntry object is created
- **THEN** it contains case_id, title, slug, status, source_type, and created_at

### Requirement: Case Writer
The casebase module SHALL provide a case writer that creates fault case directories from analysis task artifacts.

#### Scenario: Case directory is created with correct structure
- **WHEN** archive_case_from_task is called with a valid task output path and case metadata
- **THEN** it creates a directory at data/cases/{case_id}_{slug}/ containing case.md, metadata.yaml, evidence-pack.md, and key-logs.txt

#### Scenario: Case metadata is written as YAML
- **WHEN** archive_case_from_task creates a case
- **THEN** metadata.yaml contains all required fields: case_id, title, slug, source_type, status, confidence, tags, components, fault_modes, exception_classes, key_phrases

#### Scenario: Evidence artifacts are copied from task output
- **WHEN** archive_case_from_task is called
- **THEN** evidence-pack.md and key-logs.txt are copied from the task output directory to the case directory

#### Scenario: Case directory naming uses case_id and slug
- **WHEN** a case is archived with case_id="CASE-001" and slug="redis-pool-exhausted"
- **THEN** the directory is named "CASE-001_redis-pool-exhausted"

### Requirement: Case Loader
The casebase module SHALL provide a case loader that reads case directories.

#### Scenario: Load case returns case.md and metadata
- **WHEN** load_case is called with a case directory path
- **THEN** it returns the case.md content and FaultCaseMetadata object

#### Scenario: Load metadata returns only metadata
- **WHEN** load_metadata is called with a case directory path
- **THEN** it returns only the FaultCaseMetadata object

#### Scenario: Missing case directory raises error
- **WHEN** load_case or load_metadata is called with a non-existent path
- **THEN** it raises FileNotFoundError

### Requirement: Case Indexer
The casebase module SHALL provide a case indexer that maintains data/cases/index.yaml.

#### Scenario: Rebuild index reads all case directories
- **WHEN** rebuild_index is called
- **THEN** it scans data/cases/ subdirectories and returns a list of CaseIndexEntry from each metadata.yaml

#### Scenario: Index file has correct YAML structure
- **WHEN** rebuild_index is called
- **THEN** the index.yaml contains a list of entries with case_id, title, slug, status, source_type, created_at

#### Scenario: Index is rebuildable from case directories
- **WHEN** index.yaml is deleted and rebuild_index is called
- **THEN** the same index is regenerated from case metadata files

#### Scenario: Malformed metadata is skipped during rebuild
- **WHEN** rebuild_index encounters a case directory with invalid metadata.yaml
- **THEN** it logs a warning and continues processing other cases

### Requirement: Case Service
The casebase module SHALL provide a case service that orchestrates case creation and retrieval.

#### Scenario: Create case from analysis orchestrates writer and indexer
- **WHEN** create_case_from_analysis is called with task output path and metadata
- **THEN** it calls archive_case_from_task and add_case_to_index

#### Scenario: Get all cases returns list of cases
- **WHEN** get_all_cases is called
- **THEN** it returns a list of FaultCase objects for all case directories

#### Scenario: Get case returns specific case
- **WHEN** get_case is called with a case_id
- **THEN** it returns the FaultCase with matching case_id or raises FileNotFoundError

### Requirement: Casebase Boundary Preservation
The casebase module MUST remain independent from FastAPI, analyzer, and retrieval modules.

#### Scenario: Casebase module does not import FastAPI
- **WHEN** the casebase module is implemented
- **THEN** it can be tested directly from diagnose_tool/casebase/ without importing FastAPI

#### Scenario: Casebase module does not import analyzer output generators
- **WHEN** the casebase module is implemented
- **THEN** it imports only from case_models, not from analyzer output modules
