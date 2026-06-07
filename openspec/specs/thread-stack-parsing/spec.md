# Thread Stack Parsing

## Purpose

Parse JVM thread dump blocks into structured thread results so downstream consumers can reuse thread metadata, ordered stack frames, lock hints, and parse status without re-parsing raw text. The parser is conservative and returns RAW or PARTIAL output on malformed input rather than raising.

## Requirements

### Requirement: Thread Dump Block Recognition
The system SHALL recognize common JVM thread dump blocks and parse them as structured thread content instead of treating every line as unrelated text.

#### Scenario: Standard HotSpot thread dump block
- **WHEN** the parser receives a raw block containing a typical JVM thread header and stack frames
- **THEN** the system returns a structured thread dump result rather than RAW-only output

#### Scenario: Non-thread text is not misclassified
- **WHEN** the parser receives plain log text that does not match a thread dump block
- **THEN** the system returns a RAW result and preserves the original text

### Requirement: Thread Metadata Extraction
The system SHALL extract thread metadata from supported thread dump headers, including thread name and thread state when they are present in the input.

#### Scenario: Thread name and state are extracted
- **WHEN** a supported thread dump block contains a quoted thread name and a `java.lang.Thread.State` line
- **THEN** the result includes the thread name and the thread state

#### Scenario: Missing metadata is tolerated
- **WHEN** a supported thread dump block omits optional metadata fields such as daemon or priority indicators
- **THEN** the parser still returns a partial result with the available fields

### Requirement: Stack Frame Extraction
The system SHALL extract ordered stack frames from thread dump blocks and preserve the frame sequence from top to bottom.

#### Scenario: Stack frames are parsed in order
- **WHEN** a thread dump block contains multiple `at ...` frame lines
- **THEN** the result includes the frames in the same order they appeared in the input

#### Scenario: Native and unknown frames are preserved
- **WHEN** a thread dump block contains `Native Method` or `Unknown Source` frames
- **THEN** the parser preserves those frames instead of discarding them

### Requirement: Lock And Monitor Hint Extraction
The system SHALL extract common lock and monitor hints from supported thread dump formats when those hints are present.

#### Scenario: Waiting or blocked hints are captured
- **WHEN** the input contains common lock-related lines such as blocked or waiting indicators
- **THEN** the result includes the lock or wait hint information in a structured form

#### Scenario: Absent lock hints do not fail parsing
- **WHEN** a thread dump block has no lock or monitor lines
- **THEN** the parser still succeeds for the rest of the block

### Requirement: Raw Preservation And Parse Status
The system SHALL preserve the original raw thread dump text and return a parse status that reflects whether the block was fully parsed, partially parsed, or left raw.

#### Scenario: Fully parsed block preserves raw text
- **WHEN** the parser successfully recognizes all required fields in a thread dump block
- **THEN** the result is marked FULL and the raw input is still available in the output

#### Scenario: Partially parsed block is not dropped
- **WHEN** the parser recognizes a thread dump header but some fields are missing or malformed
- **THEN** the result is marked PARTIAL and the raw input remains available

### Requirement: Malformed Inputs Are Safe
The system MUST NOT raise an unhandled error when thread dump input is malformed or truncated.

#### Scenario: Truncated thread dump block
- **WHEN** the parser receives a thread dump block that ends before the stack frames are complete
- **THEN** the parser returns a partial or raw result without crashing

#### Scenario: Unsupported vendor format
- **WHEN** the parser receives a thread dump block in an unsupported vendor-specific format
- **THEN** the parser returns RAW or PARTIAL output and preserves the original text
