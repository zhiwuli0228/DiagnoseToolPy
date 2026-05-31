# API Documentation

## Overview

This document describes the API endpoints for the DiagnoseToolPy diagnostic assistant.

## Base URL

All API endpoints are prefixed with `/api`.

## Authentication

Currently no authentication is required.

---

## Diagnosis Endpoints

### POST /api/diagnosis

Run AI preliminary diagnosis for a completed analysis task.

**Request:**
```json
{
  "task_id": "string"
}
```

**Response (200):**
```json
{
  "case_id": "string",
  "diagnosis": "string (markdown)"
}
```

**Errors:**
- `404`: Task not found
- `503`: AI diagnosis not enabled

---

### POST /api/diagnosis/search

Run AI diagnosis from search cache with user-selected evidence.

**Request:**
```json
{
  "cache_key": "string",
  "selections": [
    {
      "type": "group" | "group_all" | "log" | "cluster",
      "group_key": "string (optional)",
      "id": "string (optional)",
      "cluster_index": "integer (optional)"
    }
  ],
  "options": {
    "include_stack": true,
    "include_timeline": true,
    "max_tokens": 2000
  }
}
```

**Response (200):**
```json
{
  "diagnosis": "string (markdown)"
}
```

**Selection Types:**
- `group`: All logs in a specific group (identified by `group_key`)
- `group_all`: All logs in all groups
- `log`: A specific log entry (identified by `id`)
- `cluster`: All logs in a cluster group (identified by `cluster_index`)

**Errors:**
- `400`: No entries selected
- `404`: Cache not found
- `503`: AI diagnosis not enabled

---

### POST /api/diagnosis/cluster

Run AI diagnosis from cluster analysis cache.

**Request:** Same as `/api/diagnosis/search`

**Response (200):**
```json
{
  "diagnosis": "string (markdown)"
}
```

**Errors:** Same as `/api/diagnosis/search`

---

## Cluster Endpoints

### POST /api/cluster

Create a new cluster analysis task.

**Request:**
```json
{
  "source_path": "string"
}
```

**Response (200):**
```json
{
  "task_id": "string"
}
```

**Errors:**
- `400`: Source path does not exist

---

### GET /api/cluster/{task_id}

Get cluster analysis progress or results.

**Response (200):**
```json
{
  "status": "scanning" | "aggregating" | "matching" | "done",
  "progress": 0-100,
  "current_step": "string",
  "clusters": [
    {
      "exception_class": "string",
      "count": "integer",
      "sample_messages": ["string"],
      "time_distribution": {
        "peak_hour": "string",
        "range": "string"
      },
      "matched_cases": [
        {
          "case_id": "string",
          "score": "float (0-1)",
          "summary": "string",
          "root_cause": "string",
          "solution": "string"
        }
      ]
    }
  ]
}
```

---

### GET /api/cluster/{task_id}/matched-lines/{cluster_index}

Get matched lines for a specific cluster group.

**Response (200):**
```json
{
  "cluster_index": "integer",
  "group_key": "string",
  "matched_lines": [
    {
      "id": "string",
      "group_key": "string",
      "event": {
        "timestamp": "string",
        "level": "string",
        "thread": "string",
        "message": "string",
        "raw": "string",
        "file_path": "string",
        "line_no": "integer"
      },
      "context_before": [LogEvent],
      "context_after": [LogEvent]
    }
  ],
  "total": "integer"
}
```

---

## Source Endpoints

### POST /api/source/check

Check if a directory path is valid and accessible.

**Request:**
```json
{
  "path": "string"
}
```

**Response (200):**
```json
{
  "valid": true,
  "path": "string"
}
```

---

### POST /api/source/scan

Scan a directory for log files.

**Request:**
```json
{
  "path": "string"
}
```

**Response (200):**
```json
{
  "files": [
    {
      "path": "string",
      "size": "integer",
      "modified": "string (ISO timestamp)"
    }
  ]
}
```

---

### POST /api/source/search

Search log content for matching lines.

**Request:**
```json
{
  "source_path": "string",
  "query": {
    "keywords": ["string"],
    "levels": ["ERROR", "WARN"],
    "time_range": {
      "start": "string (ISO timestamp)",
      "end": "string (ISO timestamp)"
    }
  },
  "aggregated": true
}
```

**Response (200):**
```json
{
  "task_id": "string",
  "cache_key": "string",
  "total": "integer",
  "groups": [
    {
      "key": "string",
      "count": "integer",
      "sample_message": "string"
    }
  ]
}
```

---

## Case Endpoints

### GET /api/cases

List all cases in the casebase.

**Response (200):**
```json
{
  "cases": [
    {
      "case_id": "string",
      "summary": "string",
      "severity": "string",
      "created_at": "string"
    }
  ]
}
```

---

### GET /api/cases/{case_id}

Get case details.

**Response (200):**
```json
{
  "case_id": "string",
  "summary": "string",
  "root_cause": "string",
  "solution": "string",
  "severity": "string",
  "created_at": "string",
  "metadata": {}
}
```

---

## Evidence Cache

Evidence basket selections are cached server-side for compression before sending to LLM.

### Cache Structure

```
data/output/{cache_key}/
├── meta.json
└── matched-lines.jsonl
```

### Meta.json
```json
{
  "cache_key": "string",
  "source_path": "string",
  "created_at": "string (ISO)",
  "type": "search" | "cluster"
}
```

### matched-lines.jsonl

One JSON entry per line:
```json
{
  "id": "string (hash)",
  "group_key": "string",
  "event": {
    "timestamp": "string",
    "level": "string",
    "thread": "string",
    "message": "string",
    "raw": "string",
    "file_path": "string",
    "line_no": "integer"
  },
  "context_before": [LogEvent],
  "context_after": [LogEvent]
}
```

---

## Error Responses

All endpoints return error responses in this format:

```json
{
  "detail": "string (error message)"
}
```

Common status codes:
- `400`: Bad request (invalid input)
- `404`: Resource not found
- `500`: Internal server error
- `503`: Service unavailable (e.g., LLM not configured)

---

## Workspace Export Endpoints

### POST /api/diagnosis/export-workspace

Export complete diagnostic workspace to a user-specified directory for manual diagnosis via OpenCode.

**Request:**
```json
{
  "task_id": "string (optional)",
  "session_id": "string (optional)",
  "cache_key": "string (optional)",
  "workspace_dir": "string (required)",
  "user_context": {
    "phenomenon": "string",
    "stack": "string",
    "params": "string"
  },
  "selections": [
    {
      "type": "group" | "group_all" | "log" | "cluster",
      "group_key": "string (optional)",
      "id": "string (optional)",
      "cluster_index": "integer (optional)"
    }
  ]
}
```

**Note:** At least one of `task_id`, `session_id`, or `cache_key` must be provided.

**Response (200):**
```json
{
  "success": true,
  "workspace_dir": "string",
  "files_written": ["README.md", "prompt.md", "context/phenomenon.md", ...],
  "detection_hint": "Save your diagnosis as result.md in the workspace directory."
}
```

**Workspace Directory Structure:**
```
{workspace_dir}/
├── README.md           # Instructions for manual diagnosis
├── prompt.md           # Pre-filled diagnosis prompt
├── context/
│   ├── phenomenon.md   # User-provided problem description
│   ├── stack.md        # Stack trace information
│   └── params.md       # Key parameters
├── logs/
│   └── evidence-pack.md  # Compressed log evidence
└── cases/              # Similar historical cases (up to 3)
```

**Errors:**
- `400`: No source provided (task_id, session_id, or cache_key required)
- `400`: Directory does not exist

---

### GET /api/diagnosis/check-result

Check if `result.md` exists in workspace directory and validate content.

**Query Parameters:**
- `workspace_dir`: Path to the exported workspace directory

**Response (200):**
```json
{
  "exists": true,
  "content": "string (valid result content)" | null,
  "validation": {
    "is_empty": false,
    "is_too_short": false,
    "is_prompt_template": false
  }
}
```

**Validation Rules:**
- `is_empty`: Content must not be blank
- `is_too_short`: Content must be at least 100 characters
- `is_prompt_template`: Content must not look like the original prompt template (must not contain 3+ of: `# Role`, `You are an experienced`, `{evidence_pack}`, `{similar_cases}`, `Diagnosis Instructions`)

---

## Degraded Response

When AI diagnosis is unavailable (LLM service error, timeout, etc.), endpoints may return a degraded response:

```json
{
  "degraded": true,
  "error_type": "llm_unavailable" | "llm_error",
  "message": "AI diagnosis temporarily unavailable. You can export the workspace and diagnose manually.",
  "workspace_export_url": "/api/diagnosis/export-workspace",
  "workspace_export_options": {
    "task_id": "string (if applicable)",
    "session_id": "string (if applicable)",
    "cache_key": "string (if applicable)",
    "selections": [...]
  }
}
```

The frontend displays a dialog offering to export the workspace for manual diagnosis.

---

## result.md Format

For successful import, `result.md` must contain a valid diagnosis in markdown format:

**Minimum Requirements:**
- At least 100 characters of content
- Not empty or whitespace-only
- Not the original prompt template

**Recommended Structure:**
```markdown
# Diagnosis Result

## Root Cause
[Description of the root cause]

## Evidence
[Supporting evidence from logs]

## Solution
[Recommended fix or next steps]
```

**Invalid Examples:**
- Empty file or just whitespace
- Original prompt template unchanged
- Content shorter than 100 characters
