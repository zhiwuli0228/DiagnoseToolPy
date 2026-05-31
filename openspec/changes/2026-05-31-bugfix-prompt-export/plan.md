# Bugfix Prompt Export Plan

## Step 1: Define the prompt contract

- Freeze the `bugfix-prompt.md` structure and content rules.
- Confirm the output path and overwrite behavior.
- Ensure the prompt marks AI diagnosis as preliminary unless human-confirmed data exists.

## Step 2: Implement backend generation

- Add a dedicated exporter that reads existing task output artifacts.
- Generate `data/output/{task_id}/bugfix-prompt.md` atomically.
- Add tests for success, missing artifacts, and overwrite behavior.

## Step 3: Wire the API

- Add a diagnosis-related API endpoint for bugfix prompt export.
- Return the generated prompt content and file path with safe errors.
- Add integration tests for valid and invalid requests.

## Step 4: Add frontend access

- Add a UI action on the diagnosis workflow to generate or preview the prompt.
- Provide copy/preview behavior without exposing raw internals.
- Add frontend tests for the action and error states.

## Step 5: Update docs and continuity state

- Document the new artifact and endpoint.
- Update `docs/00-project/current-state.md` after implementation.
- Run the relevant tests and verify the file-based output contract.

