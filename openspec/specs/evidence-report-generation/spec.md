# Evidence Report Generation

## Purpose

Generate structured output files from in-memory analysis results for evidence preservation, reporting, case drafting, and retrieval querying. This capability produces HTML reports, evidence packages, case drafts, and retrieval context without AI involvement or full-file loading.

## Requirements

### Requirement: Evidence Pack Generator
The system SHALL generate `evidence-pack.md` containing classification statistics, exception timeline, key log features, and bounded top exception samples from in-memory parsed log records and classification results.

#### Scenario: Evidence pack contains required sections
- **WHEN** the evidence generator is called with classification results and parsed log records
- **THEN** the generated `evidence-pack.md` contains sections for basic info, exception classification stats, exception timeline, key log features, and top exception samples

#### Scenario: Evidence pack samples are bounded
- **WHEN** a category has more than 20 samples
- **THEN** only the first 20 samples are included in the evidence pack

### Requirement: Key Logs Generator
The system SHALL generate `key-logs.txt` containing bounded excerpt lines per classification category with category labels.

#### Scenario: Key logs file contains labeled excerpts
- **WHEN** the key logs generator is called with parsed log records and classification results
- **THEN** each line in `key-logs.txt` includes the category label and raw log excerpt

#### Scenario: Key logs samples are bounded
- **WHEN** a category exceeds the sample limit
- **THEN** only the first 20 excerpts per category are written

### Requirement: HTML Summary Report Generator
The system SHALL generate `summary.html` from in-memory analysis data using a Jinja2 template, containing classification summary, error counts, and key features.

#### Scenario: HTML report renders with required data
- **WHEN** the report generator is called with OutputContext and analysis data
- **THEN** the generated `summary.html` contains task metadata, error/warn counts, classification summary, and top exceptions

#### Scenario: HTML template uses provided context
- **WHEN** the report generator renders the summary
- **THEN** the Jinja2 template receives task_id, source_path, error_count, warn_count, classification_stats, and top_exceptions

### Requirement: Case Draft Generator
The system SHALL generate `case-draft.md` and `case-metadata-draft.yaml` from analysis results for later casebase archiving.

#### Scenario: Case draft contains required markdown sections
- **WHEN** the case draft generator is called with top classification result and parsed records
- **THEN** `case-draft.md` contains basic info, fault description placeholder, and key evidence references

#### Scenario: Case metadata contains required YAML fields
- **WHEN** the case draft generator is called
- **THEN** `case-metadata-draft.yaml` contains case_id, title, slug, source_type=auto, status=draft, confidence=unconfirmed, tags, components, fault_modes, exception_classes, key_phrases

### Requirement: Retrieval Query Generator
The system SHALL generate `retrieval-query.json` containing keywords, exception classes, components, fault modes, and stack symbols from analysis results.

#### Scenario: Retrieval query contains required fields
- **WHEN** the retrieval query generator is called with classification results and parsed records
- **THEN** `retrieval-query.json` contains task_id, summary, components, fault_modes, exception_classes, keywords, stack_symbols, and log_templates

#### Scenario: Retrieval query excludes raw logs
- **WHEN** the retrieval query generator creates the query
- **THEN** no full raw log content is included in the JSON output

### Requirement: Timeline Generator
The system SHALL generate `artifacts/timeline.json` containing time-windowed error and warn counts from pre-aggregated buckets.

#### Scenario: Timeline JSON has correct structure
- **WHEN** the timeline generator is called with time buckets
- **THEN** `artifacts/timeline.json` is a JSON array of objects with timestamp, error_count, and warn_count fields

### Requirement: Raw Samples Generator
The system SHALL generate `artifacts/raw-samples.jsonl` containing bounded samples per classification category.

#### Scenario: Raw samples JSONL format is correct
- **WHEN** the raw samples generator is called with parsed log records and classification results
- **THEN** `artifacts/raw-samples.jsonl` contains one JSON object per line with category, raw, timestamp, and level fields

#### Scenario: Raw samples are bounded
- **WHEN** a category exceeds the sample limit
- **THEN** only the first 20 samples per category are written to the JSONL file

### Requirement: Output Directory Creation
The system SHALL create the output directory `data/output/{task_id}/` and `data/output/{task_id}/artifacts/` before writing files.

#### Scenario: Directory is created before writing
- **WHEN** the output system is called with a task_id
- **THEN** it creates the output directory and artifacts subdirectory if they do not exist

### Requirement: Evidence Generation Without AI
The system SHALL produce evidence that is useful for AI-assisted diagnosis but SHALL NOT invent conclusions or fabricate evidence content.

#### Scenario: Evidence contains only observed data
- **WHEN** the evidence generator creates output files
- **THEN** all content is derived from observed parsed log records and classification results without fabricating details

### Requirement: Analyzer Boundary Preservation
The output generator modules MUST remain independent from FastAPI, casebase archiving, retrieval ranking, and AI providers.

#### Scenario: Output modules do not import FastAPI
- **WHEN** the output generator modules are implemented
- **THEN** they can be tested directly from `diagnose_tool/analyzer/` without importing FastAPI or writing final archived cases

### Requirement: Implementation State Is Documented
The system MUST update the project continuity snapshot after evidence and report generation are implemented.

#### Scenario: Current state reflects evidence and report completion
- **WHEN** implementation tasks for this change are completed
- **THEN** `docs/00-project/current-state.md` marks evidence package generator and report generator as implemented while leaving casebase archiving, retrieval, and deployment work incomplete
