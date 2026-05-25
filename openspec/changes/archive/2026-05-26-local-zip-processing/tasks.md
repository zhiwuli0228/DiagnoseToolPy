## 1. Backend — ZIP Handling Infrastructure

- [x] 1.1 Add `extract_zip_to_temp()` helper function in `routes_source.py` using Python `zipfile` module; extract to `data/temp/zip-{uuid}/` and return the Path
- [x] 1.2 Modify `check_source_directory()` to detect `.zip` suffix and validate ZIP file accessibility using `zipfile.is_zipfile()`
- [x] 1.3 Modify `scan_source_directory()` to detect `.zip` suffix, call `extract_zip_to_temp()`, then call `scan_directory()` on the extracted path; return `extracted_path` in response
- [x] 1.4 Add `DELETE /api/source/temp/{task_id}` endpoint that removes the corresponding temp directory via `shutil.rmtree()`

## 2. Backend — Expose Extracted Path in Responses

- [x] 2.1 Ensure `ScanResult` (or response dict) returned from `scan_source_directory()` includes `extracted_path` field when ZIP extraction occurred
- [x] 2.2 Ensure `SourcePathRequest` check response includes `is_zip: bool` field so frontend can know if the path is a ZIP archive

## 3. Frontend — Remove Upload Logic

- [x] 3.1 Remove `JSZip` import from `AnalysisTasksPage.tsx`
- [x] 3.2 Remove `uploadFiles` import from `AnalysisTasksPage.tsx`
- [x] 3.3 Remove `handleZipExtract()` function entirely (no longer needed)
- [x] 3.4 Remove `zipInputRef` and its click trigger button ("ZIP" button) from the input addon
- [x] 3.5 Remove `fileInputRef` and the "Browse..." button's `onChange` handler that called `uploadFiles()`
- [x] 3.6 Remove `extracting` state variable (used only by `handleZipExtract`)
- [x] 3.7 Update `sourceApi.ts` to remove the `uploadFiles()` export

## 4. Frontend — Add Cleanup Button

- [x] 4.1 Add `DELETE /api/source/temp/{task_id}` call to `sourceApi.ts`
- [x] 4.2 Add "Clean Temp Files" button to `AnalysisTasksPage.tsx` near the path input area
- [x] 4.3 Wire the cleanup button to call the delete temp API; show success/error message

## 5. Frontend — Path Input UX

- [x] 5.1 Update path input placeholder text to clarify it accepts both directory and `.zip` file paths (e.g., `/data/logs` or `/data/logs/app.zip`)
- [x] 5.2 Verify that after a ZIP scan, the `path` state is updated to the `extracted_path` returned by the backend, so subsequent operations use the extracted directory

## 6. Verification

- [x] 6.1 Start the backend server and verify ZIP path input works: enter a `.zip` path in the input, click "Check Directory" — should succeed
- [x] 6.2 Click "Scan Directory" on a ZIP path — should extract and return scan results
- [x] 6.3 Verify browser console has no errors during ZIP processing
- [x] 6.4 Click "Clean Temp Files" — verify temp directory is deleted from `data/temp/`
- [x] 6.5 Verify existing directory (non-ZIP) scanning still works as before
