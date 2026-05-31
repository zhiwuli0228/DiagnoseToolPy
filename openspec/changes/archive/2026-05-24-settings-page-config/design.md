## Context

The `SettingsPage.tsx` frontend currently renders hardcoded app name/version and placeholder Empty components. The backend has rich configuration infrastructure (`config/app.yaml`, `load_config()`, `load_llm_config()`) but no API endpoints expose it to the frontend.

The application serves a single user on a local machine (DiagnoseToolPy is a local tool), so multi-user concurrent writes to `config/app.yaml` are a low-probability edge case, but still needs protection.

## Goals / Non-Goals

**Goals:**
- Expose all relevant application configuration via a REST API endpoint
- Allow hot-updating `allowed_input_roots` (add/remove paths) without server restart
- Display LLM configuration status in the Settings page (read-only)
- Keep LLM configuration editing out of scope (requires backend environment changes)

**Non-Goals:**
- Editing LLM configuration via UI (API key, model, base_url should be set in config/app.yaml or via env vars)
- Editing server host/port via UI (requires uvicorn restart)
- Adding input roots via file browser (path text input is sufficient)
- Role-based access control or authentication

## Decisions

### 1. New file: `diagnose_tool/api/routes_config.py`

**Decision**: Create a dedicated router for configuration endpoints rather than adding to an existing router.

**Rationale**: Configuration is conceptually distinct from source scanning, diagnosis, cases, and clustering. A dedicated router keeps the codebase organized.

**Alternatives considered**:
- Adding config routes to `routes_source.py` — conflates path-validation concerns with config management
- Adding to `routes_diagnosis.py` — same problem

### 2. File locking: `filelock` pip package

**Decision**: Add `filelock` as a dependency rather than using `msvcrt.locking()` (Windows-only) or implementing our own lock.

**Rationale**:
- Cross-platform (Windows + Unix)
- Simple API: `with FileLock(path): ...`
- Battle-tested, no custom code needed
- Handles lock timeout and cleanup

**Alternatives considered**:
- `msvcrt.locking()` — Windows only, would break Linux deployments
- Custom spinlock with retry — reinventing the wheel, error-prone
- No locking — acceptable for single-user local tool, but defensive programming is better

### 3. `GET /api/config` response shape

**Decision**: Return a merged view of `AppConfig` + `AppLLMConfig` under a single endpoint.

```python
{
  "app": { "name": "...", "version": "..." },
  "server": { "host": "...", "port": ... },
  "paths": { "allowed_input_roots": [...], "data_dir": "..." },
  "llm": { "enabled": bool, "model": "...", "base_url": "...", "timeout": int }
}
```

**Rationale**: Single round-trip for the Settings page to get everything it needs.

### 4. `PATCH /api/config/paths` — atomic read-modify-write with lock

```python
lock = FileLock(CONFIG_PATH + ".lock")
with lock:
    raw = yaml.safe_load(CONFIG_PATH.open())
    # mutate raw["paths"]["allowed_input_roots"]
    CONFIG_PATH.write_text(yaml.safe_dump(raw))
```

**Rationale**: Atomic from the perspective of concurrent writers — lock held for full duration of read-modify-write cycle. `load_config()` called on every request naturally picks up changes.

**Cache invalidation**: The `allowed_input_roots` is read fresh via `load_config()` on every request in `_validate_source_path()`, so no cache invalidation is needed for path validation. The `_llm_config` global in `routes_diagnosis` and `routes_conversation` is not affected by path changes.

### 5. Remove `_llm_config` global cache in route modules

**Decision**: `load_llm_config()` is cheap (YAML parse). Remove the `global _llm_config` caching in `routes_diagnosis.py` and `routes_conversation.py` so that future LLM config changes (if ever added) take effect immediately.

**Rationale**: Simplicity. Caching adds no meaningful performance benefit for a config read that happens once per request. Future-proofs for potential UI-based LLM config editing.

**Risk**: Slightly higher per-request overhead (YAML parse on every diagnosis request). Negligible for the expected request volume.

### 6. Settings page — read-only LLM card

**Decision**: LLM configuration card shows current settings but does not offer edit controls.

**Rationale**: Changing LLM API key, model, or base URL in production should go through the YAML file / environment, not a UI that persists to YAML anyway. No security boundary is needed since this is a local single-user tool.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Concurrent PATCH to config/app.yaml (two users) | `filelock` ensures serialized access; second writer blocks until first releases |
| User removes all `allowed_input_roots` | Backend validates `allowed_input_roots` list is non-empty on PATCH; returns 400 |
| User adds a path that doesn't exist | Backend validates path exists and is a directory before adding |
| YAML write corrupts config/app.yaml | Lock held for full duration; `yaml.safe_load` round-trip validates structure before write |
| `filelock` package not installed | Add to `pyproject.toml` dependencies; `uv add filelock` |

## Migration Plan

1. Add `filelock` to `pyproject.toml` dependencies
2. Create `diagnose_tool/api/routes_config.py` with `GET /api/config` and `PATCH /api/config/paths`
3. Register router in `diagnose_tool/main.py`
4. Create `frontend/src/api/configApi.ts`
5. Rewrite `frontend/src/pages/SettingsPage.tsx` to use real API data
6. Run existing tests to ensure no regressions

**Rollback**: Revert the change files. The YAML config file format is unchanged — no migration needed.

## Open Questions

1. **Should adding a new path also create the directory if it doesn't exist?** — Currently the design validates the path exists. Should it auto-create?
2. **Should deleted paths be validated against active analysis tasks?** — If a user removes a root that has in-progress tasks, scanning stops working but existing outputs remain accessible. Do we warn?
