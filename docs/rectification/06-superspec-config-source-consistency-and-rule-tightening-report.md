# DiagnoseToolPy SuperSpec Phase 2A 配置来源一致性复核与规则收口报告

> 执行阶段：Phase 2A  
> 执行工具：Codex  
> 执行日期：2026-05-31  
> 整改工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 整改分支：`chore/superspec-governance-migration`  
> Phase 2 基线 HEAD：`d34c81ba6355309ebe577006c3b981fde8d08736`  
> 本阶段性质：仅复核配置来源一致性并收窄规则义务，不修改 schema、living specs、业务代码或工具目录

## 1. 执行摘要

- 执行结果：`PASS`
- 修改文件：`openspec/config.yaml`
- 新增报告：`docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md`
- 是否修改 schema templates：否
- 是否修改 living specs：否
- 是否修改业务代码 / 测试 / 数据 / `.claude/` / `.opencode/`：否
- 是否建议进入 Phase 3：是

本阶段先以整改 worktree 内的 `AGENTS.md`、`docs/` 与 `work-items/README.md` 作为唯一配置依据，重新核验了 `openspec/config.yaml` 的规则来源；随后对 `rules.tasks` 做了最小收窄，并补强 `apply` / `finalize` 的临时安全门禁语义。原工作区文件仅用于 SHA256 对比，不作为最终配置依据。

## 2. 复核结论

### 2.1 依据边界

- `AGENTS.md`：作为本阶段唯一权威项目入口，已在整改 worktree 内重新读取。
- `docs/README.md`：确认 OpenSpec 与文档读取顺序要求。
- `work-items/README.md`：确认历史任务记录冻结，不再作为活跃治理路径。
- 原工作区 `E:/009workspace/claudecode/DiagnoseToolPy/...`：仅用于 SHA256 / diff 比对，不参与配置定稿。

### 2.2 规则收口结果

- `rules.tasks` 由“更新 docs 和 current-state”收窄为“仅当获批变更改变长期能力、架构边界、运维合同或已记录限制时，才更新 durable docs，包括 current-state”。
- `rules.apply` 显式保留临时执行门禁：在 active change 被授权且任务范围清晰前，不进入高风险实现。
- `rules.finalize` 显式保留临时收尾门禁：在验证通过且仓库级 Git/PR 安全审查批准前，不执行 closeout。

## 3. 来源文件 SHA256 比对表

以下比对以整改 worktree 文件为准，原工作区文件仅用于 hash 对照：

| 文件 | Worktree SHA256 | Original SHA256 | 结论 |
|---|---|---|---|
| `AGENTS.md` | `CF855703C2610F06928DE028ACA30ED27112DAB47216FF7C761A6F801B471FE4` | `D01BA1DF652502BCFC8865666BBCB4FCEC5806D2406FC733305486C632D5CA9E` | 不同，worktree 为 Phase 0A 后版本 |
| `docs/README.md` | `F5013412C2835004119E39EBED6EB10FD95224D0C16A524337D132D51BF5E3B6` | `F5013412C2835004119E39EBED6EB10FD95224D0C16A524337D132D51BF5E3B6` | 相同 |
| `work-items/README.md` | `FDC77AB89897C2668EA16FE5D97236BA0CA670675DD158E08D3E9E6FC196B90D` | `02E67CE18EA9A4529A140C4BFEABB3A952ADF8AE39C64CF93B0471A11FA4CB3A` | 不同，worktree 为冻结声明版本 |
| `docs/02-harness/harness-standard.md` | `2F6985501D0F55D25DA4D65C72077A94EEEBAA8BA662BAC874E8F2151882AC63` | `2F6985501D0F55D25DA4D65C72077A94EEEBAA8BA662BAC874E8F2151882AC63` | 相同 |
| `docs/01-architecture/storage-contract.md` | `CA60FD0E04FD45101A54D4F9EE5D49134A1CA131F7850D5364FBE05BC3C2FA1D` | `CA60FD0E04FD45101A54D4F9EE5D49134A1CA131F7850D5364FBE05BC3C2FA1D` | 相同 |
| `docs/01-architecture/module-boundaries.md` | `AEFB5542C76FC6ADF42D73869FAF19F9756954AE866652B6CAF032C4229D0136` | `AEFB5542C76FC6ADF42D73869FAF19F9756954AE866652B6CAF032C4229D0136` | 相同 |
| `docs/06-operations/server-directory-access.md` | `73F6265726FCBDBB585B46826AA8EE1FB5C33990EB1028A9241B870839A8071F` | `73F6265726FCBDBB585B46826AA8EE1FB5C33990EB1028A9241B870839A8071F` | 相同 |
| `docs/06-operations/security-policy.md` | `058FF58D782833CC66E992A189187E44CC5FDA76DEFE72D31E108BB09387A611` | `058FF58D782833CC66E992A189187E44CC5FDA76DEFE72D31E108BB09387A611` | 相同 |
| `docs/03-openspec/proposal-rule.md` | `60807098E7CAC52E7ABA315E178BC99DB61B86A516CC959312ABE363E9FA251D` | `60807098E7CAC52E7ABA315E178BC99DB61B86A516CC959312ABE363E9FA251D` | 相同 |
| `docs/03-openspec/design-rule.md` | `7C73C0BEAD8FCE1304FDFBEC9E24F6BBC4208396BD3ED548F0C9BEB39CB53B1F` | `7C73C0BEAD8FCE1304FDFBEC9E24F6BBC4208396BD3ED548F0C9BEB39CB53B1F` | 相同 |
| `docs/03-openspec/spec-rule.md` | `EBD6016DA87411285726D133CF7D98D5B7264F2874FB3ED83C0BF9CFF6A9CA12` | `EBD6016DA87411285726D133CF7D98D5B7264F2874FB3ED83C0BF9CFF6A9CA12` | 相同 |
| `docs/03-openspec/tasks-rule.md` | `3DF7461EC7810BDDC967BEC4882F1E026607D3F2CFE0932E0DB3FFF2791D9CD4` | `3DF7461EC7810BDDC967BEC4882F1E026607D3F2CFE0932E0DB3FFF2791D9CD4` | 相同 |

## 4. 配置全文核验结果

### `openspec/config.yaml`

核验结论：

- `schema: superspec` 保持不变
- `context` 保持精简且仅引用 DiagnoseToolPy 的长期项目约束
- `rules.tasks` 已收窄到“长期能力 / 架构边界 / 运维合同 / 已记录限制”四类触发条件
- `rules.apply` 和 `rules.finalize` 均保留临时安全门禁语义
- 未引入对每个变更都强制更新 `current-state.md` 的泛化义务

### 精确 diff

```diff
diff --git a/openspec/config.yaml b/openspec/config.yaml
index bc4c1716..f0f24e37 100644
--- a/openspec/config.yaml
+++ b/openspec/config.yaml
@@ -34,16 +34,19 @@ rules:
   tasks:
     - Keep tasks small, dependency-ordered, and individually verifiable.
     - Each task should identify files, behavior, tests, and validation steps.
-    - Update docs and current-state when behavior or storage contracts change.
+    - Update durable docs, including current-state, only when an approved change alters long-term capabilities, architecture boundaries, operations contracts, or recorded limitations.
   plan:
     - Break work into micro-steps with exact paths and validation checkpoints.
     - Prefer test-first execution where feasible and stop if new out-of-scope work appears.
     - Keep the plan focused on the active change only.
   apply:
     - Implement only approved paths and record any deviation before proceeding.
     - Keep work constrained to the active change and avoid unrelated refactors or scope expansion.
     - Preserve evidence of tests and task completion in the apply receipt.
+ Treat apply as a temporary execution gate: do not start high-risk implementation until the active change is authorized and the task scope is clear.
   verify:
     - Run structural validation and confirm task completion, scope compliance, and spec coherence.
     - Fail on unauthorized file changes or missing durable-asset updates.
     - Do not recommend finalize while a blocking issue remains.
   finalize:
     - Close out only after verify passes and repository-specific Git safety prerequisites are approved.
     - Do not broaden merge, push, cleanup, or PR actions beyond the active change and approved workflow.
     - Record the final outcome and evidence for archive and human review.
+ Treat finalize as a temporary closeout gate: do not perform Git/PR closeout until verification is green and the repository-specific safety review has approved the action.
```

## 5. OpenSpec 全量验证结果

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
?? docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
```

### `git diff --stat`

```text
 openspec/config.yaml | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)
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
- [x] 未修改 `work-items/README.md`
- [x] 未执行 `/opsx:*` lifecycle 命令
- [x] 未执行 commit / push / merge / reset / clean / stash / git add

## 8. Phase 2 + Phase 2A 提交结论

- 结论：`允许人工提交 Phase 2 + Phase 2A`

理由：

- 配置来源已回到整改 worktree 内的权威资产链。
- `rules.tasks` 已按要求收窄，不再将 `current-state.md` 设为每个变更的默认强制义务。
- `apply` 与 `finalize` 的临时安全门禁仍然保留。
- OpenSpec 全量验证保持 `0 failed`。
- 当前变更仍只限于 `openspec/config.yaml` 与本报告文件。

## 9. Phase 3 准入结论

- 结论：`允许进入 Phase 3`

前提仍是：Phase 2 + Phase 2A 先由人工统一提交，随后再进入下一阶段。
