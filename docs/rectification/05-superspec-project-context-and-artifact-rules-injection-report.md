# DiagnoseToolPy SuperSpec Phase 2 项目 Context 与 Artifact Rules 注入报告

> 执行阶段：Phase 2  
> 执行工具：Codex  
> 执行日期：2026-05-31  
> 整改工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 整改分支：`chore/superspec-governance-migration`  
> Phase 2 起始 HEAD：`d34c81ba6355309ebe577006c3b981fde8d08736`  
> 本阶段性质：仅向 `openspec/config.yaml` 注入项目 context 与 artifact rules，不修改 schema 模板、living specs 或业务资产

## 1. 执行摘要

- 执行结果：`PASS`
- 修改文件：`openspec/config.yaml`
- 新增报告：`docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md`
- 是否修改 schema templates：否
- 是否修改 living specs：否
- 是否修改业务代码 / 测试 / 数据 / `.claude/` / `.opencode/`：否
- 是否建议进入 Phase 3：是

本阶段仅在 `openspec/config.yaml` 中注入了与 DiagnoseToolPy 一致的精简项目 context 和 SuperSpec artifact rules。注入内容严格来源于项目治理资产，聚焦文件系统为真源、流式日志分析、无强制数据库、无 embedding 默认依赖、以及 AI 仅作辅助诊断等约束。

## 2. 读取的权威治理资产

本阶段实际读取并据此抽取规则的文件如下：

- `AGENTS.md`
- `docs/README.md`
- `docs/02-harness/harness-standard.md`
- `docs/01-architecture/module-boundaries.md`
- `docs/01-architecture/storage-contract.md`
- `docs/06-operations/server-directory-access.md`
- `docs/06-operations/security-policy.md`
- `docs/03-openspec/proposal-rule.md`
- `docs/03-openspec/design-rule.md`
- `docs/03-openspec/spec-rule.md`
- `docs/03-openspec/tasks-rule.md`
- `openspec/config.yaml`
- `openspec/schemas/superspec/schema.yaml`

## 3. 注入规则来源映射

| 配置项 | 注入内容摘要 | 主要来源 |
|---|---|---|
| `context` | DiagnoseToolPy 项目定位、技术栈、权威入口、文件系统为真源、无强制数据库、流式读取、检索无需 embeddings、AI 仅作辅助 | `AGENTS.md`、`docs/README.md`、`docs/02-harness/harness-standard.md`、`docs/01-architecture/storage-contract.md`、`docs/01-architecture/module-boundaries.md`、`docs/06-operations/server-directory-access.md`、`docs/06-operations/security-policy.md` |
| `rules.brainstorm` | 先读权威文档、聚焦变更能力、区分行为与实现、避免无关扩展 | `docs/03-openspec/proposal-rule.md`、`docs/03-openspec/design-rule.md`、`docs/02-harness/harness-standard.md` |
| `rules.proposal` | 必须包含问题、目标、范围、非目标、影响模块、存储影响、风险、验证 | `docs/03-openspec/proposal-rule.md`、`docs/02-harness/harness-standard.md` |
| `rules.design` | 保持无强制数据库、流式处理、模块边界、失败处理与安全约束 | `docs/01-architecture/storage-contract.md`、`docs/01-architecture/module-boundaries.md`、`docs/06-operations/security-policy.md` |
| `rules.specs` | 使用 MUST/MUST NOT、每条需求配场景、只描述可观察行为、写文件需说明路径与回收/重建 | `docs/03-openspec/spec-rule.md`、`docs/01-architecture/storage-contract.md` |
| `rules.tasks` | 任务拆小、可验证、说明文件/行为/测试/校验、同步 docs 与 current-state | `docs/03-openspec/tasks-rule.md`、`docs/02-harness/harness-standard.md` |
| `rules.plan` | 微步骤、精确路径、验证检查点、测试优先、避免扩展范围 | `docs/03-openspec/tasks-rule.md`、`docs/02-harness/harness-standard.md` |
| `rules.apply` | 仅实现授权路径、记录偏差、限制在活跃变更内、保留测试证据 | `docs/03-openspec/tasks-rule.md`、`docs/02-harness/harness-standard.md` |
| `rules.verify` | 结构验证、范围合规、失败即阻止 finalize、不得推荐带阻塞问题的收尾 | `docs/03-openspec/tasks-rule.md`、`docs/03-openspec/spec-rule.md` |
| `rules.finalize` | 仅在 verify 通过后收尾，遵守 Git/PR 安全前置条件，不扩大到额外动作 | `docs/03-openspec/tasks-rule.md`、`docs/02-harness/harness-standard.md` |

## 4. 配置精确 diff

### `openspec/config.yaml`

```diff
diff --git a/openspec/config.yaml b/openspec/config.yaml
index 48443ffa..d4c0a7a8 100644
--- a/openspec/config.yaml
+++ b/openspec/config.yaml
@@ -8,6 +8,17 @@ context: |
   Stack: Python 3.11+, uv, FastAPI backend, and a React/TypeScript frontend.
   AGENTS.md is the canonical project-level agent entry; docs/README.md routes task-specific reading.
   File system is the source of truth; durable artifacts use Markdown, YAML, JSON, JSONL, HTML, or plain text.
   Local indexes are rebuildable caches, not durable truth; mandatory external databases are prohibited.
   Primary workflow is server-side directory scanning and streaming log analysis; browser upload is optional for small files.
   Large logs must be streamed line by line; never load entire files into memory.
   Retrieval must work without embeddings; default matching uses keywords, rules, and BM25 when available.
   AI diagnosis is assistive; preserve human-confirmed root cause, review, lessons learned, and follow-up fields.
   OpenSpec artifacts should stay aligned with the authoritative governance docs; avoid scope creep into unrelated assets.
```

## 5. OpenSpec 验证结果

### `openspec schemas`

```text
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
## chore/superspec-governance-migration
 M openspec/config.yaml
?? docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
```

### `git diff --stat`

```text
 openspec/config.yaml | 35 +++++++++++++++++++++++++++++++++++
 1 file changed, 35 insertions(+)
```

### `git diff --name-only`

```text
openspec/config.yaml
```

## 7. 保护范围确认

- [x] 未修改 schema templates
- [x] 未修改 living specs
- [x] 未修改历史整改报告
- [x] 未修改业务代码
- [x] 未修改测试代码
- [x] 未修改数据
- [x] 未修改 `.claude/`
- [x] 未修改 `.opencode/`
- [x] 未修改 `openspec/changes/`
- [x] 未执行 `/opsx:*` lifecycle 命令
- [x] 未执行 commit / push / merge / reset / clean / stash / git add

## 8. Phase 3 准入结论

- 结论：`允许进入 Phase 3`

理由：项目级 context 与 artifact rules 已按权威治理资产最小注入，且验证结果保持 `0 failed`。当前变更仅限于 OpenSpec 配置与本执行报告，未扩大到 schema、living specs、业务实现或其他受限资产。
