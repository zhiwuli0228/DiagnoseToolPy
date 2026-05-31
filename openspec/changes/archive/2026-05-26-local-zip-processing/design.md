## Context

The tool is deployed locally (FastAPI server + browser on the same machine). Currently, ZIP files selected via the browser are decompressed in-browser using JSZip, then uploaded via multipart form data. This fails for large ZIPs because the browser loads the entire archive into memory before extraction. For local deployment, file upload is unnecessary — the backend can directly read from server paths.

The frontend provides a path input field and two辅助 buttons (ZIP, Browse). The goal is to eliminate browser-side ZIP extraction and file upload, letting the backend handle everything via path-based access.

## Goals / Non-Goals

**Goals:**
- Eliminate browser memory exhaustion when handling large ZIP files
- Remove frontend ZIP extraction dependency (JSZip)
- Backend transparently handles `.zip` paths — frontend only passes path strings
- Provide explicit temp directory cleanup via API and UI button
- Path input remains the primary user interface for specifying log sources

**Non-Goals:**
- Supporting remote/cloud deployment with separate frontend/backend hosts (this is a local-only workflow)
- Automatic temp directory garbage collection (explicit cleanup via user action)
- ZIP password protection support
- Nested ZIP handling (ZIP containing ZIP)

## Decisions

### Decision 1: Backend ZIP extraction using Python's `zipfile` module

**Choice**: Use Python standard library `zipfile.ZipFile.extractall()` in `routes_source.py`.

**Rationale**: Python's `zipfile` module is already present (no new dependencies), supports streaming extraction, and is well-tested. The existing `_extract_zip_archive()` in `cluster_analyzer.py` can be reused. This approach processes ZIPs on the server where memory is not constrained by a browser tab.

**Alternatives considered**:
- Use `shutil.unpack_archive()` — less control over extraction location
- Use `zipfile.is_zipfile()` check before extraction to validate

### Decision 2: Temp directory location and naming

**Choice**: Extract to `data/temp/zip-{uuid}/{filename}/` inside the project data directory.

**Rationale**:
- Centralized under `data/temp/` alongside other temp artifacts
- UUID ensures uniqueness and prevents collisions when same ZIP is scanned multiple times
- `data/` is already in `.gitignore` and not committed
- Retaining the original filename inside the UUID directory preserves structure for nested directories within the ZIP

**Example**: `data/temp/zip-a1b2c3d4/app-logs/` where `app-logs/` is the ZIP root contents

### Decision 3: Transparent ZIP handling in existing `check` and `scan` endpoints

**Choice**: Modify `routes_source.py` `check` and `scan` handlers to detect `.zip` suffix and trigger extraction inline, returning `extracted_path` in the response.

**Rationale**:
- Minimal API surface change — no new endpoint required for the happy path
- Frontend code changes are minimal: just pass the path string, backend handles the rest
- User experience is unchanged: they enter a path (which happens to be a `.zip`), and scanning works transparently

**Implementation**: In `scan_source()`, after path validation:
```python
path = Path(request.path)
if path.suffix.lower() == '.zip':
    temp_dir = extract_zip_to_temp(path)  # new helper
    scan_result = scan_directory(temp_dir)
    scan_result['extracted_path'] = str(temp_dir)
    return scan_result
```

### Decision 4: Temp directory cleanup via explicit API

**Choice**: Add `DELETE /api/source/temp/{task_id}` endpoint. Frontend provides a "Clean Temp Files" button that calls this.

**Rationale**:
- User has explicit control over when temp files are cleaned
- `task_id` maps to the UUID-based temp directory name
- Avoids background cleanup threads or cron-based solutions
- Simple: just `shutil.rmtree()` the temp directory

**Non-goal**: Automatic expiration-based cleanup (can be added later if needed)

### Decision 5: Frontend removes all upload logic

**Choice**: Remove `JSZip` import, `uploadFiles` API call, and `handleZipExtract` function. Keep the path input field as the primary interface.

**Rationale**:
- Browser no longer handles any file content — only path strings
- No more `multipart/form-data` upload for log sources
- "ZIP" and "Browse" buttons are removed or repurposed to only assist with path input (they cannot provide absolute paths in standard browsers)
- `sourceApi.ts` can remove the `uploadFiles` export entirely

**Alternative**: Keep buttons but change them to fill the path input with example paths — rejected as unnecessary complexity.

## Risks / Trade-offs

- [Risk] Path input requires user to know/guess the server path — Mitigation: Provide clear placeholder text and document common paths. The path validation error messages guide the user.

- [Risk] ZIP with nested directories may extract flat — Mitigation: ZIP archives preserve directory structure when extracted. The extracted path returned to frontend reflects the actual extracted location.

- [Risk] Multiple scans of same ZIP create multiple temp dirs — Mitigation: Acceptable trade-off for correctness. User can manually clean up via the cleanup button. UUID prevents collisions.

- [Risk] Frontend cannot browse server filesystem to discover paths — Mitigation: This is a known limitation of standard browsers. Path input with validation feedback is the UX pattern. Users who need discovery can use server tooling or documentation.

## Migration Plan

1. **Deploy backend changes first**: Add ZIP detection/extraction in `check` and `scan`, add cleanup endpoint
2. **Deploy frontend changes**: Remove JSZip, remove upload logic, add cleanup button
3. **No data migration needed**: Temp directories are disposable, existing scan workflows remain valid
4. **Rollback**: Revert frontend and backend independently — the old upload endpoint can remain unused but not removed (avoids breaking any edge-case callers)

## Open Questions

1. Should the scan response include a list of extracted files within the ZIP, or just the `extracted_path`? — Scan result already includes file listing from `scan_directory()`, so the extracted path is sufficient for subsequent operations.

2. Should the "Clean Temp Files" button clean all temp directories or require user to specify which one? — Clean all is simpler for the initial implementation. Per-task cleanup can be added later.
