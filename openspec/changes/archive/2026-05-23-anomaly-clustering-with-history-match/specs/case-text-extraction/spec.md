## ADDED Requirements

### Requirement: Case Text Extraction from case.md
The system SHALL extract structured information from case.md files, including root cause, solution, and summary for use in historical case matching.

#### Scenario: Extract root cause section
- **WHEN** parsing a case.md file
- **THEN** system SHALL extract content under "## Root Cause" or "## 根因" heading
- **THEN** extracted root cause is stored as a string field

#### Scenario: Extract solution section
- **WHEN** parsing a case.md file
- **THEN** system SHALL extract content under "## Solution" or "## 解决方案" heading
- **THEN** extracted solution is stored as a string field

#### Scenario: Extract summary
- **WHEN** parsing a case.md file
- **THEN** if no explicit summary section exists, system SHALL use the first paragraph as summary
- **THEN** extracted summary is stored as a string field

#### Scenario: Handle missing sections
- **WHEN** a case.md file does not contain a root cause or solution section
- **THEN** system SHALL return None for those fields
- **THEN** extraction continues for available sections without error

---

### Requirement: Dual-track Historical Case Matching
The system SHALL match current clusters against historical cases using both metadata.yaml fields and case.md extracted text, combining scores from both tracks.

#### Scenario: Metadata field matching
- **WHEN** matching a cluster with exception_class "JedisConnectionException"
- **THEN** system SHALL score case metadata by exception_classes field overlap
- **THEN** system SHALL score case metadata by components and fault_modes overlap

#### Scenario: Case body text matching
- **WHEN** metadata match score is low or metadata fields are sparse
- **THEN** system SHALL query case.md extracted text for exception class or error pattern
- **THEN** system SHALL use keyword overlap on root_cause and solution fields

#### Scenario: Combined scoring
- **WHEN** both metadata and case body matches are found
- **THEN** system SHALL combine scores with weights (metadata: 0.6, body: 0.4)
- **THEN** system SHALL return top matches sorted by combined score

#### Scenario: No historical matches
- **WHEN** no case matches a cluster above minimum threshold (0.3)
- **THEN** system SHALL return empty matched_cases array
- **THEN** system SHALL indicate "无匹配案例，建议 AI 诊断"

---

### Requirement: Matched Case Output Format
The system SHALL output matched historical cases with case_id, score, summary, root_cause, and solution fields.

#### Scenario: Successful match output
- **WHEN** a cluster matches case#42
- **THEN** response includes { case_id: "case#42", score: 0.85, summary: "...", root_cause: "...", solution: "..." }

#### Scenario: Partial extraction
- **WHEN** a case.md has root_cause but no solution section
- **THEN** matched case output has root_cause filled and solution as null