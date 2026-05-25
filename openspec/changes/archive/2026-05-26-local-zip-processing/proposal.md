# Proposal: Local ZIP Processing

## Why

The current implementation uses JSZip in the browser to decompress ZIP files before uploading, which causes browser memory exhaustion and crashes when handling large ZIP archives. Since this tool is designed for local deployment (FastAPI server + browser on the same machine), file upload is unnecessary overhead. The solution is to pass only the file path to the backend and let Python handle ZIP extraction and log reading.

## What Changes

- **Remove** frontend JSZip dependency and all ZIP extraction logic from the browser
- **Remove** the `uploadFiles` API and related frontend upload handling
- **Enhance** `/api/source/check` and `/api/source/scan` to auto-detect `.zip` paths and extract them server-side
- **Add** new `DELETE /api/source/temp/{task_id}` endpoint to clean up extracted temporary directories
- **Add** frontend "Clean Temp Files" button to trigger cleanup
- **Modify** the path input workflow: ZIP/folder all handled via path string input to backend

## Capabilities

### New Capabilities

- `zip-file-processing`: Backend handles ZIP file detection, extraction to temp directory, and subsequent log reading. Frontend passes only path string, no file content upload. Includes temp file lifecycle management (create, track, cleanup).

### Modified Capabilities

- `server-directory-scan`: Extend the existing scan capability to handle `.zip` file paths transparently — when a `.zip` path is provided, the backend extracts it first, then scans the extracted contents as if it were a regular directory. The scan result returns the extracted path for subsequent operations.

## Impact

**Frontend:**
- `frontend/src/pages/AnalysisTasksPage.tsx` — Remove `JSZip` import, `uploadFiles` call, and file upload `onChange` handlers; retain path input; add "Clean Temp Files" button

**Backend:**
- `diagnose_tool/api/routes_source.py` — Enhance `check` and `scan` to detect `.zip` suffix and trigger extraction; add cleanup endpoint
- `diagnose_tool/analyzer/cluster_analyzer.py` — Already has `_extract_zip_archive()`; can be reused
- `diagnose_tool/analyzer/reader.py` — Already has `_read_zip_contents()` for streaming ZIP log reading

**Dependencies:**
- No new dependencies required — Python standard library `zipfile` handles extraction
