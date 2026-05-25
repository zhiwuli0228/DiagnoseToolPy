## 1. Backend Setup

- [x] 1.1 Add `filelock` to `pyproject.toml` dependencies (`uv add filelock`)
- [x] 1.2 Add `filelock` to `uv.lock` by running `uv sync`

## 2. Backend API: routes_config.py

- [x] 2.1 Create `diagnose_tool/api/routes_config.py` with `GET /api/config` endpoint
- [x] 2.2 Add `PATCH /api/config/paths` endpoint with add/remove actions
- [x] 2.3 Implement file locking around YAML read-modify-write using `filelock`
- [x] 2.4 Register router in `diagnose_tool/main.py`
- [x] 2.5 Validate path exists and is directory before adding
- [x] 2.6 Validate at least one root remains after removal
- [x] 2.7 Reject duplicate paths on add
- [x] 2.8 Reject non-existent paths on remove

## 3. Backend: Remove _llm_config Global Cache

- [x] 3.1 Remove `global _llm_config` caching in `diagnose_tool/api/routes_diagnosis.py`
- [x] 3.2 Remove `global _llm_config` caching in `diagnose_tool/api/routes_conversation.py`

## 4. Frontend: configApi.ts

- [x] 4.1 Create `frontend/src/api/configApi.ts`
- [x] 4.2 Add `GET /api/config` function returning full config
- [x] 4.3 Add `PATCH /api/config/paths` function for add/remove actions

## 5. Frontend: SettingsPage.tsx

- [x] 5.1 Replace hardcoded app name/version with API data
- [x] 5.2 Add LLM Configuration card (read-only display)
- [x] 5.3 Replace Empty component with real `allowed_input_roots` list
- [x] 5.4 Add delete button per root that calls `PATCH /api/config/paths` with remove
- [x] 5.5 Add input + Add button for new root path
- [x] 5.6 Add client-side validation: empty path, duplicate path, single-root removal
- [x] 5.7 Add loading state while fetching config
- [x] 5.8 Add error handling with error message display

## 6. Tests

- [x] 6.1 Add backend tests for `GET /api/config`
- [x] 6.2 Add backend tests for `PATCH /api/config/paths` add (success, duplicate, non-existent)
- [x] 6.3 Add backend tests for `PATCH /api/config/paths` remove (success, last-root rejection, non-existent)
- [x] 6.4 Add backend tests for concurrent PATCH requests (file locking)
- [x] 6.5 Update `SettingsPage.test.tsx` to test real API integration

## 7. Verification

- [x] 7.1 Run `uv run pytest` — all backend tests pass
- [x] 7.2 Run `npm test` — all frontend tests pass
- [x] 7.3 Start backend (`uv run uvicorn`) and frontend (`npm run dev`)
- [x] 7.4 Navigate to Settings page — verify config loads correctly
- [x] 7.5 Add a new input root via UI — verify it appears and persists after page reload
- [x] 7.6 Remove an input root via UI — verify it disappears and persists after page reload
