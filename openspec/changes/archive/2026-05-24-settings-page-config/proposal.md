## Why

The Settings page (`SettingsPage.tsx`) is an empty shell with hardcoded values and placeholder text. It serves no functional purpose — it cannot display real configuration, nor allow any configuration to be modified. Yet the backend already has rich configuration infrastructure (`config/app.yaml`, `load_config()`, `load_llm_config()`) that goes unused by the frontend. This is wasted potential and user confusion.

## What Changes

1. **Add `GET /api/config` endpoint** — exposes full application configuration (app, paths, llm) to the frontend
2. **Add `PATCH /api/config/paths` endpoint** — allows adding/removing `allowed_input_roots` entries with file locking for safe concurrent writes
3. **Wire up `SettingsPage`** — replace hardcoded cards with real data from `GET /api/config`
4. **Add Input Roots management UI** — users can add new allowed paths or remove existing ones from the Settings page
5. **LLM Configuration display** — show current LLM settings (enabled, model, base_url, timeout) as read-only information, since editing requires backend environment changes
6. **Invalidate `_llm_config` cache** — when `allowed_input_roots` changes via API, subsequent requests pick up the new config without server restart (load_config is already hot; only the global `_llm_config` cache in routes needs to be invalidated)

## Capabilities

### New Capabilities

- `settings-config-api`: Backend API for reading and updating application configuration. Provides `GET /api/config` for reading all config sections and `PATCH /api/config/paths` for managing `allowed_input_roots`.
- `settings-page-ui`: Frontend Settings page that displays real configuration and allows management of `allowed_input_roots`.

### Modified Capabilities

- (none — existing capabilities remain unchanged)

## Impact

- **Backend**: New API routes in `diagnose_tool/api/routes_config.py` (new file). Adds `filelock` pip dependency for cross-platform file locking.
- **Frontend**: `SettingsPage.tsx` rewritten to use API data. New `configApi.ts` in frontend API layer.
- **Config file**: `config/app.yaml` is mutated at runtime by the new PATCH endpoint (with file lock protection).
- **No impact** on existing diagnosis, casebase, search, or cluster workflows.
