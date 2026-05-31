# DiagnoseToolPy SuperSpec Phase 2B 配置门禁语法修正与提交证据链复核报告

> 执行阶段：Phase 2B  
> 执行工具：Codex  
> 执行日期：2026-05-31  
> 整改工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 整改分支：`chore/superspec-governance-migration`  
> Phase 2 基线 HEAD：`d34c81ba6355309ebe577006c3b981fde8d08736`  
> 本阶段性质：仅修正 `openspec/config.yaml` 中的 YAML 门禁语法与语义，不修改 schema、living specs、业务代码、工具目录或既有报告

## 1. 执行摘要

- 执行结果：`PASS`
- 修改文件：`openspec/config.yaml`
- 新增报告：`docs/rectification/07-superspec-config-gate-syntax-fix-report.md`
- 是否修改 schema templates：否
- 是否修改 living specs：否
- 是否修改业务代码 / 测试 / 数据 / `.claude/` / `.opencode/`：否
- 是否建议进入 Phase 3：是

本阶段复核表明，`rules.apply` 与 `rules.finalize` 在 YAML 层面确实位于 `rules` 对象下，但之前未加引号，导致解析后最后一项被当成 mapping 而不是字符串列表项。现已以最小方式修正为严格的字符串列表项，并保留之前已经收窄的 durable docs / `current-state.md` 规则。

## 2. 提交证据链核验

### 2.1 变更集合核验

当前待修改集合核验结果：

```text
## chore/superspec-governance-migration...origin/chore/superspec-governance-migration
 M openspec/config.yaml
?? docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
?? docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
```

结论：

- 当前工作树除 `openspec/config.yaml` 外，还保留两份未跟踪整改报告。
- 本次修正未新增额外业务文件。
- `docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md` 并未进入 Git 历史。

### 2.2 Git 历史核验

对 `docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md` 的历史查询结果为空，说明该文件尚未随任何已提交 commit 进入当前分支历史。

```text
git log --oneline --decorate -- docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
<no output>
```

结论：

- `05` 报告未提交。
- 本阶段不能把它当成已经进入历史的证据。

## 3. YAML Parser 复核

### 3.1 修正前

使用 YAML parser 解析 `openspec/config.yaml`，门禁项虽然位于 `rules.apply` 与 `rules.finalize` 下，但最后一项因未加引号，被解析为映射而不是字符串：

```json
{
  "top_keys": ["schema", "context", "rules"],
  "has_top_apply": false,
  "has_top_finalize": false,
  "rules_keys": ["brainstorm", "proposal", "design", "specs", "tasks", "plan", "apply", "verify", "finalize"],
  "apply_type": "list",
  "finalize_type": "list",
  "apply_items": [
    "Implement only approved paths and record any deviation before proceeding.",
    "Keep work constrained to the active change and avoid unrelated refactors or scope expansion.",
    "Preserve evidence of tests and task completion in the apply receipt.",
    {
      "Treat apply as a temporary execution gate": "do not start high-risk implementation until the active change is authorized and the task scope is clear."
    }
  ],
  "finalize_items": [
    "Close out only after verify passes and repository-specific Git safety prerequisites are approved.",
    "Do not broaden merge, push, cleanup, or PR actions beyond the active change and approved workflow.",
    "Record the final outcome and evidence for archive and human review.",
    {
      "Treat finalize as a temporary closeout gate": "do not perform Git/PR closeout until verification is green and the repository-specific safety review has approved the action."
    }
  ]
}
```

### 3.2 修正后

修正后 parser 结果：

```json
{
  "top_keys": ["schema", "context", "rules"],
  "has_top_apply": false,
  "has_top_finalize": false,
  "rules_keys": ["brainstorm", "proposal", "design", "specs", "tasks", "plan", "apply", "verify", "finalize"],
  "apply_type": "list",
  "finalize_type": "list",
  "apply_items": [
    "Implement only approved paths and record any deviation before proceeding.",
    "Keep work constrained to the active change and avoid unrelated refactors or scope expansion.",
    "Preserve evidence of tests and task completion in the apply receipt.",
    "Do not start real business implementation for the active change until the active change is authorized and the task scope is clear."
  ],
  "finalize_items": [
    "Close out only after verify passes and repository-specific Git safety prerequisites are approved.",
    "Do not broaden merge, push, cleanup, or PR actions beyond the active change and approved workflow.",
    "Record the final outcome and evidence for archive and human review.",
    "Do not perform Git/PR closeout, merge, or push until verification is green and the repository-specific safety review has approved the action."
  ]
}
```

## 4. 配置精确 diff

### `openspec/config.yaml`

```diff
diff --git a/openspec/config.yaml b/openspec/config.yaml
index 737587aa..b14c0f8e 100644
--- a/openspec/config.yaml
+++ b/openspec/config.yaml
@@ -38,7 +38,7 @@ rules:
     - Implement only approved paths and record any deviation before proceeding.
     - Keep work constrained to the active change and avoid unrelated refactors or scope expansion.
     - Preserve evidence of tests and task completion in the apply receipt.
-    - Do not start real business implementation for the active change until the active change is authorized and the task scope is clear.
+    - "Do not start real business implementation for the active change until the active change is authorized and the task scope is clear."
@@ -46,7 +46,7 @@ rules:
     - Close out only after verify passes and repository-specific Git safety prerequisites are approved.
     - Do not broaden merge, push, cleanup, or PR actions beyond the active change and approved workflow.
     - Record the final outcome and evidence for archive and human review.
-    - Do not perform Git/PR closeout, merge, or push until verification is green and the repository-specific safety review has approved the action.
+    - "Do not perform Git/PR closeout, merge, or push until verification is green and the repository-specific safety review has approved the action."
```

## 5. OpenSpec 验证结果

### `openspec schemas`

```text
Available schemas:

  spec-driven
  superspec (project)
```

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
11 passed, 0 failed
```

## 6. 最终 Git 可见变更集合

### `git status --short --branch --untracked-files=all`

```text
## chore/superspec-governance-migration...origin/chore/superspec-governance-migration
 M openspec/config.yaml
?? docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
?? docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
?? docs/rectification/07-superspec-config-gate-syntax-fix-report.md
```

### `git diff --stat`

```text
 openspec/config.yaml | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

### `git diff --name-only`

```text
openspec/config.yaml
```

## 7. 保护范围确认

- [x] 未修改 schema
- [x] 未修改 living specs
- [x] 未修改历史整改报告
- [x] 未修改业务代码
- [x] 未修改测试代码
- [x] 未修改工具目录
- [x] 未修改数据
- [x] 未修改 `.claude/`
- [x] 未修改 `.opencode/`
- [x] 未修改 `AGENTS.md`
- [x] 未执行 `/opsx:*` lifecycle 命令
- [x] 未执行 commit / push / merge / reset / clean / stash / git add

## 8. 结论

- 允许提交修正后的 Phase 2 + Phase 2A + Phase 2B 变更：`是`
- 允许进入 Phase 3：`是`

前提仍然是仅提交授权范围内的 `openspec/config.yaml` 变更与本次新增报告，不纳入未跟踪但未获授权的其他文件。
