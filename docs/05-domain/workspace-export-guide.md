# Workspace Export Guide

The workspace export feature allows you to export a diagnostic workspace to a local directory for manual diagnosis using OpenCode or another editor.

## When to Use

Use workspace export when:
- AI diagnosis is temporarily unavailable (degraded mode)
- You want to perform diagnosis manually with full context
- You want to use OpenCode's AI capabilities for deeper analysis

## How to Export

### From DiagnosisStudioPage

1. Navigate to the Diagnosis Studio page
2. Select log evidence or enter problem description
3. Click "Preview Prompt" button
4. Enter the workspace directory path when prompted
5. The system exports the workspace and shows success dialog

### Bugfix Prompt Export

When you have an existing analysis task output and want to hand a structured implementation brief to Claude Code or OpenCode:

1. Open the Analysis Tasks page and finish clustering or another task that produces `data/output/{task_id}`.
2. Click **Generate Bugfix Prompt**.
3. Review the generated `data/output/{task_id}/bugfix-prompt.md` content.
4. Copy the prompt into the implementation agent, or inspect the file directly in the data directory.

The bugfix prompt is generated from task artifacts such as `task.yaml`, `evidence-pack.md`, `case-draft.md`, and `retrieval-query.json`. It is deterministic and can be regenerated safely.

### From Degraded Dialog

When AI diagnosis returns a degraded response:
1. The degraded dialog appears automatically
2. Click "Export Workspace" button
3. Enter the workspace directory path
4. The system exports the workspace and starts result polling

## Workspace Directory Structure

```
{workspace_dir}/
├── README.md              # Instructions for manual diagnosis
├── prompt.md              # Pre-filled diagnosis prompt
├── context/
│   ├── phenomenon.md      # User-provided problem description
│   ├── stack.md           # Stack trace information
│   └── params.md          # Key parameters
├── logs/
│   └── evidence-pack.md  # Compressed log evidence
├── cases/
│   ├── case-001_xxx.md   # Similar historical case 1
│   ├── case-002_yyy.md   # Similar historical case 2
│   └── case-003_zzz.md   # Similar historical case 3
└── result.md             # YOUR diagnosis result (you create this)
```

## result.md Format

Your `result.md` should contain:

```markdown
# Diagnosis Result

## Root Cause
[Describe the root cause of the issue]

## Evidence
- [Evidence point 1]
- [Evidence point 2]
- [Evidence point 3]

## Solution
1. [Step 1]
2. [Step 2]
3. [Step 3]
```

### Format Requirements

- Minimum 100 characters
- Must NOT be empty
- Must NOT be the original prompt template
- Can be in any language (system will detect)

## Result Detection

After exporting:
1. System polls for `result.md` every 5 seconds
2. Polling continues for up to 30 minutes
3. When valid result is detected, import notification appears
4. Click "Import" to save the result as a diagnosis

### Manual Result Check

Click "Check Result" button in the export success dialog to immediately check for result.md.

## Using with OpenCode

1. Export workspace to a directory
2. Open the directory in OpenCode
3. Review the evidence and context
4. Complete your diagnosis in `result.md`
5. Save the file
6. Return to DiagnoseToolPy and import the result

## Using Bugfix Prompt Export

If you already have a completed analysis task and want a fix-oriented brief:

1. Use the Analysis Tasks page to generate the bugfix prompt.
2. Open `data/output/{task_id}/bugfix-prompt.md`.
3. Pass the prompt to Claude Code or OpenCode for implementation.
4. Keep the prompt and the analysis artifacts together so future reviews can trace the rationale.
