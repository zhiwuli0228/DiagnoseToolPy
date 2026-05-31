## Purpose

Provide local retrieval over existing fault cases without embeddings, using keywords, rules, and optional BM25 while keeping historical cases reference-only.

## Requirements

### Requirement: Retrieval Query Builder
The retrieval module SHALL provide a query builder that creates a retrieval query from analyzer output or retrieval-query.json.

#### Scenario: Build query from retrieval-query.json file
- **WHEN** build_retrieval_query is called with a path to retrieval-query.json
- **THEN** it returns a query object with keywords, components, fault_modes, exception_classes, and key_phrases

#### Scenario: Build query from analyzer output path
- **WHEN** build_retrieval_query is called with a task output directory path
- **THEN** it reads retrieval-query.json from that directory

### Requirement: Keyword Search
The retrieval module SHALL provide keyword-based case search without requiring embeddings.

#### Scenario: Keyword search returns scored case IDs
- **WHEN** search_by_keywords is called with a query
- **THEN** it returns a list of (case_id, score) tuples for cases with matching keywords
- **AND** scores are based on keyword overlap with case content and metadata

#### Scenario: Keyword search works when embedding is disabled
- **WHEN** search_by_keywords is called
- **THEN** no embedding model is required
- **AND** search uses text matching only

### Requirement: Rule Matching
The retrieval module SHALL provide rule-based matching using tags, components, fault_modes, exception_classes, and key_phrases.

#### Scenario: Rule matching returns scored case IDs
- **WHEN** match_by_rules is called with a query
- **THEN** it returns a list of (case_id, score) tuples for cases with matching metadata fields
- **AND** scores are based on overlap with tags, components, fault_modes, exception_classes, and key_phrases

#### Scenario: Rule matching works when embedding is disabled
- **WHEN** match_by_rules is called
- **THEN** no embedding model is required
- **AND** matching uses field comparison only

### Requirement: BM25 Search
The retrieval module SHALL provide optional BM25 full-text search when rank-bm25 is available.

#### Scenario: BM25 search returns scored case IDs when available
- **WHEN** search_bm25 is called and rank-bm25 is installed
- **THEN** it returns a list of (case_id, score) tuples from full-text search

#### Scenario: BM25 search returns empty when not available
- **WHEN** search_bm25 is called and rank-bm25 is not installed
- **THEN** it returns an empty list
- **AND** no error is raised

### Requirement: Prompt Context Generation
The retrieval module SHALL generate prompt context for AI diagnosis with reference-only markers.

#### Scenario: Prompt context includes reference markers
- **WHEN** generate_prompt_context is called with query and cases
- **THEN** the output includes explicit markers stating cases are "references only"
- **AND** the output includes a statement that historical root cause may not match current issue

#### Scenario: Prompt context is bounded
- **WHEN** generate_prompt_context is called with more than max_cases
- **THEN** only the top max_cases are included in the context

### Requirement: Retrieval Boundary Preservation
The retrieval module MUST remain independent from AI providers and mandatory embedding models.

#### Scenario: Retrieval does not call AI
- **WHEN** retrieval functions are called
- **THEN** no AI API is called
- **AND** no embedding model is invoked for scoring

#### Scenario: Retrieval works with embedding disabled
- **WHEN** retrieval functions are called with embedding disabled
- **THEN** keyword search and rule matching still return results
- **AND** BM25 search is skipped if not available
