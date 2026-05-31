# DiagnoseToolPy Docs Entry

This directory is the **project-level Harness Context Hub**.

It is used by humans and AI agents to understand project state, architecture, constraints, OpenSpec artifact rules, development standards, and domain-specific diagnostic behavior.

## Reading Policy

Do not read every document blindly. Read documents based on task type.

### Required for Every Non-trivial Change

1. `AGENTS.md`
2. `docs/00-project/project-brief.md`
3. `docs/00-project/current-state.md`
4. `docs/02-harness/harness-standard.md`
5. `docs/04-development/development-guide.md`

### Architecture Changes

Also read:

1. `docs/01-architecture/design.md`
2. `docs/01-architecture/module-boundaries.md`
3. `docs/01-architecture/storage-contract.md`

### OpenSpec Work

Also read:

1. `docs/03-openspec/proposal-rule.md`
2. `docs/03-openspec/design-rule.md`
3. `docs/03-openspec/spec-rule.md`
4. `docs/03-openspec/tasks-rule.md`
5. `docs/03-openspec/superspec-validation-project-workflow.md`

### Log Analyzer Work

Also read:

1. `docs/05-domain/log-format-guide.md`
2. `docs/05-domain/log-analysis-rules.md`
3. `docs/01-architecture/module-boundaries.md`

### Casebase / Retrieval Work

Also read:

1. `docs/01-architecture/casebase-design.md`
2. `docs/01-architecture/retrieval-design.md`
3. `docs/05-domain/fault-case-template.md`
4. `docs/05-domain/retrieval-query-template.md`

### Deployment / Operations Work

Also read:

1. `docs/06-operations/deployment-guide.md`
2. `docs/06-operations/docker-compose-guide.md`
3. `docs/06-operations/server-directory-access.md`
4. `docs/06-operations/security-policy.md`

## Hard Rules

- Do not introduce mandatory external databases.
- Do not make browser upload the primary large-log input path.
- Do not load full log files into memory.
- Durable knowledge must be stored as Markdown/YAML/JSONL files.
- Every implementation must include tests for core logic.
- Every completed change must update `docs/00-project/current-state.md`.

## Directory Map

```text
docs/
├── 00-project/       # project brief, state, glossary, roadmap
├── 01-architecture/  # design, module boundaries, storage contracts, ADRs
├── 02-harness/       # AI-assisted development harness standards
├── 03-openspec/      # OpenSpec proposal/design/spec/tasks rules
├── 04-development/   # coding, testing, local run, dependency rules
├── 05-domain/        # log diagnosis domain rules and templates
├── 06-operations/    # deployment and operational guides
├── 07-templates/     # reusable artifact templates
└── 99-archive/       # obsolete or historical docs
```
