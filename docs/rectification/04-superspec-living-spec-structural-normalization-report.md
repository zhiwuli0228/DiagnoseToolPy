# DiagnoseToolPy SuperSpec Phase 1A 存量 Living Specs 结构兼容修复报告

> 执行阶段：Phase 1A  
> 执行工具：Codex  
> 执行日期：2026-05-31  
> 整改工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 整改分支：`chore/superspec-governance-migration`  
> Phase 1 起始 HEAD：`365c9a6e1c0f1df675a325a4127ade9c8aba4222`  
> 本阶段性质：仅修复已失败 living specs 的结构兼容性，不改业务语义

## 1. 执行摘要

- 执行结果：`PASS`
- 修复的 spec 数量：6
- `openspec validate --all --json`：`11 passed, 0 failed`
- `openspec validate --all`：`11 passed, 0 failed`
- 是否建议人工提交 Phase 1 + Phase 1A 统一变更：是
- 是否建议进入 Phase 2：是，前提是人工提交 Phase 1 / Phase 1A 统一基线后再开始下一阶段

本阶段只对 `openspec validate --all --json` 指出的 6 个失败 living specs 做了结构级修复，统一补齐或规范了 `## Purpose` 与 `## Requirements`，未新增能力、未删除要求、未改写行为语义。

## 2. 结构修复摘要

| Spec | 修复前问题 | 修复动作 | 语义影响 |
|---|---|---|---|
| `basic-case-retrieval` | 缺少 `## Purpose`，且仅有 `## ADDED Requirements` | 补充 `## Purpose`，将标题规范化为 `## Requirements` | 无，保留原检索行为合同 |
| `casebase-file-storage` | 仅有 `## Purpose`，缺少规范 `## Requirements` 标题 | 将 `## ADDED Requirements` 规范化为 `## Requirements` | 无，保留原 casebase 行为合同 |
| `docker-deployment` | 缺少 `## Purpose` | 补充 `## Purpose`，将标题规范化为 `## Requirements` | 无，保留原部署行为合同 |
| `evidence-report-generation` | 标题写作 `##ADDED Requirements`，缺少规范 `## Requirements` | 规范化标题为 `## Requirements` | 无，保留原证据产物行为合同 |
| `manual-case-creation` | 仅有 `## Purpose`，缺少规范 `## Requirements` 标题 | 将 `## ADDED Requirements` 规范化为 `## Requirements` | 无，保留原手工建案例行为合同 |
| `react-frontend-shell` | 缺少 `## Purpose` | 补充 `## Purpose`，将标题规范化为 `## Requirements` | 无，保留原前端壳行为合同 |

## 3. 修复后的验证结果

### `openspec validate --all --json`

```json
{
  "summary": {
    "totals": {
      "items": 11,
      "passed": 11,
      "failed": 0
    }
  }
}
```

### `openspec validate --all`

```text
✓ spec/basic-case-retrieval
✓ spec/casebase-file-storage
✓ spec/docker-deployment
✓ spec/evidence-report-generation
✓ spec/log-reader-and-multiline
✓ spec/manual-case-creation
✓ spec/project-skeleton
✓ spec/react-frontend-shell
✓ spec/server-directory-scan
✓ spec/settings-config-api
✓ spec/settings-page-ui
Totals: 11 passed, 0 failed (11 items)
```

## 4. 最终 Git 可见变更集合

### `git status --short --branch --untracked-files=all`

```text
## chore/superspec-governance-migration
 M openspec/config.yaml
 M openspec/specs/basic-case-retrieval/spec.md
 M openspec/specs/casebase-file-storage/spec.md
 M openspec/specs/docker-deployment/spec.md
 M openspec/specs/evidence-report-generation/spec.md
 M openspec/specs/manual-case-creation/spec.md
 M openspec/specs/react-frontend-shell/spec.md
?? docs/rectification/03-superspec-schema-installation-and-minimal-activation-report.md
?? docs/rectification/04-superspec-living-spec-structural-normalization-report.md
?? openspec/schemas/superspec/INTEGRATION.md
?? openspec/schemas/superspec/README.md
?? openspec/schemas/superspec/schema.yaml
?? openspec/schemas/superspec/templates/apply.md
?? openspec/schemas/superspec/templates/brainstorm.md
?? openspec/schemas/superspec/templates/design.md
?? openspec/schemas/superspec/templates/finalize.md
?? openspec/schemas/superspec/templates/plan.md
?? openspec/schemas/superspec/templates/proposal.md
?? openspec/schemas/superspec/templates/spec.md
?? openspec/schemas/superspec/templates/tasks.md
?? openspec/schemas/superspec/templates/verify.md
```

### `git diff --stat`

```text
 openspec/config.yaml                              | 2 +-
 openspec/specs/basic-case-retrieval/spec.md       | 6 +++++-
 openspec/specs/casebase-file-storage/spec.md      | 2 +-
 openspec/specs/docker-deployment/spec.md          | 6 +++++-
 openspec/specs/evidence-report-generation/spec.md | 2 +-
 openspec/specs/manual-case-creation/spec.md       | 2 +-
 openspec/specs/react-frontend-shell/spec.md       | 6 +++++-
 7 files changed, 19 insertions(+), 7 deletions(-)
```

### `git diff --name-only`

```text
openspec/config.yaml
openspec/specs/basic-case-retrieval/spec.md
openspec/specs/casebase-file-storage/spec.md
openspec/specs/docker-deployment/spec.md
openspec/specs/evidence-report-generation/spec.md
openspec/specs/manual-case-creation/spec.md
openspec/specs/react-frontend-shell/spec.md
```

## 5. 保护范围确认

- [x] 未修改 `diagnose_tool/`
- [x] 未修改 `frontend/`
- [x] 未修改 `tests/`
- [x] 未修改 `config/`
- [x] 未修改 `data/`
- [x] 未修改 `.claude/`
- [x] 未修改 `.opencode/`
- [x] 未修改 `AGENT.md` / `AGENTS.md` / `work-items/`
- [x] 未修改 `openspec/changes/`
- [x] 未修改 `openspec/schemas/superspec/**`
- [x] 未执行 OpenSpec lifecycle 命令
- [x] 未安装 Superpowers
- [x] 未执行 commit / push / merge / reset / clean / stash / git add

## 6. Phase 2 准入结论

### 结论

- `ALLOW`

### 理由

`openspec validate --all` 与 `openspec validate --all --json` 已均达到 `0 failed`，且本阶段只做了 living specs 的结构兼容修复，没有改动业务实现、schema 原始模板或工具专用资产。当前变更已经满足进入 Phase 2 的前置条件。

### Phase 2 预期内容

若进入 Phase 2，下一阶段只处理：

```text
- 为 openspec/config.yaml 注入精简 project context
- 为 SuperSpec artifacts 注入与 DiagnoseToolPy 对齐的 rules
- 建立文档路由与 config 注入之间的职责边界
- 不修改 schema 原始模板、不修改业务代码
```

