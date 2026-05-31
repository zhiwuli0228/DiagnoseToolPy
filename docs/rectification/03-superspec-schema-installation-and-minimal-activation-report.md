# DiagnoseToolPy SuperSpec Phase 1 项目级 Schema 引入与最小激活报告

> 执行阶段：Phase 1  
> 执行工具：Codex  
> 执行日期：2026-05-31  
> 整改工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 整改分支：`chore/superspec-governance-migration`  
> Phase 1 起始 HEAD：`365c9a6e1c0f1df675a325a4127ade9c8aba4222`  
> 上游来源：`danielhanold/superspec`  
> 上游 schema version：`4`  
> 上游 commit：`e1c8f417ee3601208416d988ba3b37d83ddb63f2`

## 1. 执行摘要

- 执行结果：`PARTIAL`
- 是否安装项目级 schema：是
- 是否切换默认 schema：是
- 是否建议进入 Phase 2：否

结论说明：

- 已将官方 `danielhanold/superspec` 的 `openspec/schemas/superspec/` 原样复制到本项目。
- 已将 `openspec/config.yaml` 中的默认 schema 从 `spec-driven` 最小切换为 `superspec`。
- `openspec schemas` 已识别项目级 `superspec` schema。
- `openspec validate --all` 在切换后失败，且失败项是现有 living specs 的结构性校验错误，因此本阶段不能视为完整 PASS。

## 2. 启动门禁验证

| 检查项 | 结果 | 证据摘要 |
|---|---|---|
| 当前 branch 为整改分支 | PASS | `git branch --show-current` = `chore/superspec-governance-migration` |
| 起始 HEAD 已包含 Phase 0A/0B 提交 | PASS | `365c9a6e1c0f1df675a325a4127ade9c8aba4222` 不同于 Phase 0A/0B 基线 |
| 起始工作树 clean | PASS | `git status --short --branch` 仅显示 `## chore/superspec-governance-migration` |
| `openspec/config.yaml` 原值为 `spec-driven` | PASS | 读取前内容为 `schema: spec-driven` |
| `openspec/schemas/superspec/` 原本不存在 | PASS | `Test-Path openspec/schemas` 为 `False`，复制前目标目录不存在 |
| 无 active OpenSpec change | PASS | `openspec/changes/` 仅有 `archive/` |
| 引入前 OpenSpec validate 基线 | PASS | `openspec validate --all` 引入前可运行，但结果为现有 specs 的结构性失败 |

## 3. OpenSpec CLI 基线

- `openspec --version` 输出：`1.3.1`
- `openspec schemas` 引入前输出摘要：仅有 `spec-driven`
- `openspec validate` 引入前输出摘要：无参数模式提示使用 `--all` / `--changes` / `--specs`
- 处理方式：使用 `openspec validate --all` 与 `openspec validate --all --json` 进行只读验证

## 4. 上游 Schema 来源核验

| 项目 | 结果 |
|---|---|
| 上游仓库 | `danielhanold/superspec` |
| Clone 目录 | `E:/009workspace/claudecode/_tmp/superspec-upstream-phase1` |
| 上游 commit SHA | `e1c8f417ee3601208416d988ba3b37d83ddb63f2` |
| schema name | `SuperSpec` |
| schema version | `4` |
| artifact 链核验 | `brainstorm → proposal → design → specs → tasks → plan → apply → verify → finalize` |
| 是否与预期 v4 一致 | 是 |

## 5. 引入的 Schema 文件清单

```text
openspec/schemas/superspec/INTEGRATION.md
openspec/schemas/superspec/README.md
openspec/schemas/superspec/schema.yaml
openspec/schemas/superspec/templates/apply.md
openspec/schemas/superspec/templates/brainstorm.md
openspec/schemas/superspec/templates/design.md
openspec/schemas/superspec/templates/finalize.md
openspec/schemas/superspec/templates/plan.md
openspec/schemas/superspec/templates/proposal.md
openspec/schemas/superspec/templates/spec.md
openspec/schemas/superspec/templates/tasks.md
openspec/schemas/superspec/templates/verify.md
```

确认：

- 文件从上游原样复制；
- 未进行项目定制改写；
- 定制化 context / rules 延期至 Phase 2。

## 6. `openspec/config.yaml` 最小修改

### 修改前

```yaml
schema: spec-driven
```

### 修改后

```yaml
schema: superspec
```

### Diff 结论

- 是否仅替换 `schema: spec-driven` → `schema: superspec`：是
- 是否新增 context / rules：否
- 是否删除其他内容：否

## 7. 引入后验证结果

### `openspec schemas`

```text
Available schemas:

  spec-driven
    Default OpenSpec workflow - proposal → specs → design → tasks
    Artifacts: proposal → specs → design → tasks

  superspec (project)
    Spec-driven workflow integrated with Superpowers skills. brainstorm → proposal → specs → tasks → plan → apply → verify → finalize.
    ...
    Artifacts: brainstorm → proposal → design → specs → tasks → plan → apply → verify → finalize
```

### `openspec validate --all`

```text
✓ spec/log-reader-and-multiline
✓ spec/project-skeleton
✓ spec/server-directory-scan
✓ spec/settings-config-api
✓ spec/settings-page-ui
Totals: 5 passed, 6 failed (11 items)
- Validating...
✗ spec/basic-case-retrieval
✗ spec/casebase-file-storage
✗ spec/docker-deployment
✗ spec/evidence-report-generation
✗ spec/manual-case-creation
✗ spec/react-frontend-shell
```

### `openspec validate --all --json`

```json
{
  "summary": {
    "totals": {
      "items": 11,
      "passed": 5,
      "failed": 6
    }
  }
}
```

### 失败明细摘要

- `basic-case-retrieval`：缺少 `## Purpose` / `## Requirements`
- `casebase-file-storage`：缺少 `## Requirements`
- `docker-deployment`：缺少 `## Purpose`
- `evidence-report-generation`：缺少 `## Requirements`
- `manual-case-creation`：缺少 `## Requirements`
- `react-frontend-shell`：缺少 `## Purpose`

### 验证结论

| 验证项 | PASS / FAIL | 说明 |
|---|---|---|
| 项目级 `superspec` schema 可识别 | PASS | `openspec schemas` 显示 `superspec (project)` |
| 已有 living specs 保持有效 | FAIL | 6 个 living specs 在 `openspec validate --all` 中失败 |
| 已归档 changes 保持有效 | PASS | `openspec/changes/` 仅 archive，未发现 active change |
| schema/config 之外无项目文件被修改 | PASS | 本阶段仅修改 `openspec/config.yaml`、新增 `openspec/schemas/superspec/**`、新增本报告 |

## 8. 最终 Git 可见变更集合

### `git status --short --branch --untracked-files=all`

```text
## chore/superspec-governance-migration
 M openspec/config.yaml
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
?? docs/rectification/03-superspec-schema-installation-and-minimal-activation-report.md
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

### 新增未跟踪 Schema / 报告文件

```text
openspec/schemas/superspec/INTEGRATION.md
openspec/schemas/superspec/README.md
openspec/schemas/superspec/schema.yaml
openspec/schemas/superspec/templates/apply.md
openspec/schemas/superspec/templates/brainstorm.md
openspec/schemas/superspec/templates/design.md
openspec/schemas/superspec/templates/finalize.md
openspec/schemas/superspec/templates/plan.md
openspec/schemas/superspec/templates/proposal.md
openspec/schemas/superspec/templates/spec.md
openspec/schemas/superspec/templates/tasks.md
openspec/schemas/superspec/templates/verify.md
docs/rectification/03-superspec-schema-installation-and-minimal-activation-report.md
```

## 9. 保护范围确认

- [x] 未修改 `diagnose_tool/`
- [x] 未修改 `frontend/`
- [x] 未修改 `tests/`
- [x] 未修改 `config/`
- [x] 未修改 `data/`
- [x] 未修改 `.claude/`
- [x] 未修改 `.opencode/`
- [x] 未修改 `AGENT.md` / `AGENTS.md` / `work-items/`
- [x] 未修改 `openspec/specs/` 或 `openspec/changes/`
- [x] 未执行 OpenSpec lifecycle 命令
- [x] 未安装 Superpowers
- [x] 未执行 commit / push / merge / reset / clean / stash / git add

## 10. Phase 2 准入结论

### 结论

- `BLOCK`

### 原因

`openspec validate --all` 在 schema 切换后失败，且失败项是现有 living specs 的结构性问题（缺少 `Purpose` / `Requirements` 章节）。这意味着本阶段虽然完成了 schema 安装与默认激活，但当前 OpenSpec 基线并未达到可安全进入 Phase 2 的状态。

### Phase 2 预期内容

若未来解除阻塞，下一阶段仅处理：

```text
- 为 openspec/config.yaml 注入精简 project context
- 为 SuperSpec artifacts 注入与 DiagnoseToolPy 对齐的 rules
- 建立文档路由与 config 注入之间的职责边界
- 不修改 schema 原始模板、不修改业务代码
```

### 尚未处理但不属于本阶段阻塞的事项

```text
- `.claude/` / `.opencode/` 工具专用资产适配
- Superpowers 安装与可用性验证
- schema artifact DAG 的演练 change
- 真实业务 change
```

