# DiagnoseToolPy 全面适配 SuperSpec：Phase 2 项目 Context 与 Artifact Rules 注入执行任务书

> **交付对象**：Codex  
> **执行阶段**：Phase 2 — Project Context & SuperSpec Artifact Rules Injection  
> **执行任务书定位**：仓库外指令载体，**不得复制或保存到项目仓库中**  
> **执行工作区**：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> **执行分支**：`chore/superspec-governance-migration`  
> **依赖前置**：Phase 1 + Phase 1A 通过人工审核并完成提交；提交后 worktree clean  
> **已采用 Schema**：`danielhanold/superspec` version 4，upstream commit `e1c8f417ee3601208416d988ba3b37d83ddb63f2`  
> **本阶段性质**：将已有项目硬约束以最小、可注入方式接入 OpenSpec 配置；不得修改业务实现、living specs、上游 schema 或工具资产

---

## 0. 任务书存放纪律（新增硬规则）

本文件是交给 Codex 的**执行输入**，不是项目产生的正式证据资产。

### 0.1 本文件不得进入仓库

禁止将本任务书复制、另存或生成到：

```text
docs/rectification/
docs/
openspec/
项目根目录任意路径
```

本阶段仓库内只允许新增实际执行报告：

```text
docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
```

### 0.2 已出现的越界任务书处理前置条件

Phase 1A 回传显示当前整改 worktree 中存在未经授权的未跟踪文件：

```text
docs/rectification/04-superspec-living-spec-structural-normalization-codex-execution.md
```

该文件是任务输入，不属于可提交治理资产。

**本阶段开始前由用户人工处理：**

1. 从整改 worktree 中移除该未跟踪任务书文件；
2. 只提交 Phase 1 + Phase 1A 授权的 schema、living specs 结构修复和报告资产；
3. 确认提交后 `git status --short --branch --untracked-files=all` 为空。

Codex 不得自行删除该文件，也不得代替用户提交。

---

## 1. Phase 1 + Phase 1A 已确认成果

Phase 1 与 Phase 1A 的回传结果已确认：

```text
- 项目级 `openspec/schemas/superspec/` 已从上游原样引入；
- `openspec/config.yaml` 默认 schema 已最小切换为 `superspec`；
- `openspec schemas` 已识别 `superspec (project)`；
- 六个旧 living specs 已进行不改变行为合同的结构归一化；
- `openspec validate --all --json` 已达到 11 passed, 0 failed；
- Phase 1/1A 尚需由用户人工提交为新的干净基线。
```

### 1.1 Phase 1A 修复的 living specs

```text
openspec/specs/basic-case-retrieval/spec.md
openspec/specs/casebase-file-storage/spec.md
openspec/specs/docker-deployment/spec.md
openspec/specs/evidence-report-generation/spec.md
openspec/specs/manual-case-creation/spec.md
openspec/specs/react-frontend-shell/spec.md
```

本阶段不得再次修改这些 living specs。

---

## 2. 本阶段目标

本阶段只完成以下工作：

1. 验证 Phase 1 + Phase 1A 已由用户提交，工作区 clean，且 `openspec validate --all --json` 仍为全量通过。
2. 读取现有权威治理资产，提取已确定的、跨变更有效的最小项目上下文：
   - `AGENTS.md`
   - `docs/README.md`
   - 必要时只读核验 `docs/02-harness/` 与 `docs/03-openspec/` 中已有规则是否与拟注入内容一致。
3. 修改 `openspec/config.yaml`：
   - 保持 `schema: superspec`；
   - 新增或填写精简 `context: |`；
   - 新增或填写与 SuperSpec artifact IDs 对齐的 `rules:`；
   - 不将全文文档复制进配置。
4. 验证配置可被 OpenSpec 解析，且现有 living specs / archived changes 仍全部通过验证。
5. 生成本阶段执行报告。
6. 给出是否允许进入 Phase 3（工具执行端与 Superpowers 前提治理）的结论。

---

## 3. 官方工作流约束与规则键映射

### 3.1 OpenSpec 配置职责

OpenSpec 的项目配置文件：

```text
openspec/config.yaml
```

支持：

```text
- 设置默认 schema；
- 注入所有 artifact 共用的 project context；
- 以 artifact id 为键注入 per-artifact rules。
```

其中：

```text
context
```

会进入所有 artifact 的生成上下文，因此必须极简，只保存不可违背且长期有效的项目事实与路由入口。

```text
rules
```

只注入到匹配 artifact 的生成步骤，因此用于放置阶段专属门禁，而不是复制所有 harness 文档。

### 3.2 SuperSpec v4 Artifact IDs

当前项目采用的 SuperSpec v4 schema 中存在以下 artifact IDs：

```text
brainstorm
proposal
design
specs
tasks
plan
apply
verify
finalize
```

本阶段 `rules:` 只能使用这些键。不得发明：

```text
archive
implementation
review
bugfix
context
```

等 schema 中不存在的 artifact rule 键。

### 3.3 SuperSpec v4 高风险执行语义

后续真实 change 中：

```text
plan
```

会引导 Superpowers writing-plans；

```text
apply
```

会使用 worktree、subagent-driven-development、TDD 与 code review，并生成 `apply.md`；

```text
verify
```

会执行 `openspec validate --all --json` 等验证；

```text
finalize
```

具有合并 worktree branch、push feature branch、可能创建或更新 PR 并发布 reviewer orientation comment 的执行语义。

因此，项目规则必须明确：

```text
- 未完成验证前，不得进入 finalize；
- 工具/Git 自动化权限治理完成前，不得对真实业务 change 执行 apply/finalize；
- 当前配置注入阶段只增强 artifact 生成约束，不执行 lifecycle。
```

---

## 4. 严格允许范围

### 4.1 允许读取的路径

```text
AGENTS.md
docs/README.md
docs/02-harness/**
docs/03-openspec/**
docs/rectification/00-*
docs/rectification/01-*
docs/rectification/02-*
docs/rectification/03-*
docs/rectification/04-superspec-living-spec-structural-normalization-report.md
openspec/config.yaml
openspec/schemas/superspec/schema.yaml
openspec/schemas/superspec/README.md
openspec/schemas/superspec/INTEGRATION.md
openspec/specs/**
openspec/changes/**                         # 仅用于验证，不得修改
work-items/README.md
```

### 4.2 允许修改的文件

仅允许修改：

```text
openspec/config.yaml
```

### 4.3 允许新增的文件

仅允许新增：

```text
docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
```

---

## 5. 严格禁止范围

### 5.1 禁止修改的治理与规范资产

禁止修改：

```text
.gitignore
AGENT.md
AGENTS.md
CLAUDE.md
work-items/**
docs/README.md
docs/00-project/**
docs/01-architecture/**
docs/02-harness/**
docs/03-openspec/**
docs/04-development/**
docs/05-domain/**
docs/06-operations/**
docs/07-templates/**
docs/99-archive/**
docs/rectification/00-*
docs/rectification/01-*
docs/rectification/02-*
docs/rectification/03-*
docs/rectification/04-*
```

### 5.2 禁止修改的 OpenSpec / SuperSpec 资产

禁止修改：

```text
openspec/schemas/superspec/**
openspec/specs/**
openspec/changes/**
```

禁止创建：

```text
openspec/changes/<any-new-change>/
```

### 5.3 禁止修改的业务与工具资产

禁止修改：

```text
diagnose_tool/**
frontend/**
tests/**
config/**
data/**
diagnosis_prompt/**
main.py
pyproject.toml
uv.lock
Dockerfile
docker-compose.yml
.github/**
.claude/**
.opencode/**
README.md
README_ZH.md
```

### 5.4 禁止命令

严禁执行：

```bash
git add
git commit
git push
git merge
git reset
git restore
git clean
git stash
git checkout -- <path>
git switch
git branch -D
git worktree add
git worktree remove
git mv
git rm

openspec init
openspec update
openspec config set
openspec config profile
openspec schema init
openspec schema fork

任何 /opsx:* 或 opsx-* lifecycle 命令
任何 Superpowers skill 或安装命令
```

本阶段只允许第 12 节列出的 OpenSpec 只读/校验命令。

---

## 6. 启动门禁：必须是提交后的干净基线

### Step 1：检查分支、HEAD 与工作树

在整改 worktree 中执行：

```powershell
Set-Location E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance

git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git log --oneline -3
```

### 必须满足

```text
当前分支：chore/superspec-governance-migration
当前 HEAD：不同于 365c9a6e1c0f1df675a325a4127ade9c8aba4222
工作树：clean，无 modified / deleted / untracked 文件
```

### 停止条件

若出现任何未提交文件，包括：

```text
docs/rectification/04-superspec-living-spec-structural-normalization-codex-execution.md
```

立即停止，不得自行删除、移动、提交或忽略：

```text
STOPPED: Phase 1 + Phase 1A have not produced a clean committed baseline.
Unexpected pending files:
- <path>
No Phase 2 changes were made.
```

---

## 7. Schema 与验证基线核验

### Step 2：核验 schema/config 与存量 specs

仅在 Step 1 通过后执行：

```powershell
Get-Content openspec/config.yaml
Select-String -Path openspec/schemas/superspec/schema.yaml -Pattern "name:|version:|brainstorm|proposal|design|specs|tasks|plan|apply|verify|finalize"
openspec --version
openspec schemas
openspec validate --all --json
```

### 必须满足

| 核验项 | 要求 |
|---|---|
| `openspec/config.yaml` | 默认 schema 已为 `superspec`，尚未注入项目级有效 `context` / `rules` |
| schema 文件 | name/version/artifact IDs 与 Phase 1 引入结果一致 |
| OpenSpec CLI | 与前序阶段一致或可解释 |
| `openspec schemas` | 识别 `superspec (project)` |
| `openspec validate --all --json` | 全部通过，0 failed |

### 停止条件

出现以下情况立即停止：

- schema/config 已在本任务开始前被其他方式改写；
- living specs 再次出现验证失败；
- schema 文件与上游复制结果不一致；
- OpenSpec CLI 不可用。

---

## 8. 读取权威资产并核对拟注入规则

### Step 3：读取现有权威入口

读取：

```powershell
Get-Content AGENTS.md
Get-Content docs/README.md
Get-Content work-items/README.md
```

仅当需要核对某条拟注入规则在现有长期治理资产中是否已有依据时，允许读取：

```powershell
Get-ChildItem docs/02-harness -File
Get-Content docs/02-harness/<relevant-file>.md
Get-ChildItem docs/03-openspec -File
Get-Content docs/03-openspec/<relevant-file>.md
```

### Step 4：制作只写入报告的依据映射表

在 Phase 2 报告中记录：

| 拟注入约束 | 权威来源文件 | 是否已有明确依据 | 是否写入 config |
|---|---|---:|---:|
| 项目性质与技术栈 | | | |
| 文件型 durable knowledge / 可重建索引边界 | | | |
| 大日志 server-side streaming 路径 | | | |
| 不得无关重构 | | | |
| 按任务读取权威文档 | | | |
| OpenSpec changes 为未来修改治理路径 | | | |
| 生命周期阶段范围控制 | | | |

### 重要限制

若拟写入的任何规则在权威资产中没有依据，不得自行发明或注入；只在报告中记录“建议后续补充治理规则”。

---

## 9. `openspec/config.yaml` 修改原则

### 9.1 配置长度控制

本项目已经存在完整文档资产。`openspec/config.yaml` 不是文档全集，也不是 CodeWiki 式知识容器。

修改后的有效配置必须满足：

```text
- context 段不超过 25 行；
- rules 段每个 artifact 不超过 5 条规则；
- rules 总规则条目不超过 35 条；
- 不粘贴架构文档正文；
- 不粘贴 living spec 内容；
- 不粘贴执行模板全文；
- 不包含临时 Phase、分支、HEAD 或审计历史；
- 不包含仅适用于某一次 change 的约束。
```

若无法在上述规模内表达，则停止并报告，不得扩张 config 成为长文档。

### 9.2 Context 与 Rules 职责

| 内容类型 | 应放位置 |
|---|---|
| 所有 change 都必须知道的项目事实与不可违背边界 | `context` |
| 某类 artifact 生成时才相关的要求 | `rules.<artifact-id>` |
| 详细说明与领域知识 | 继续留在 `docs/`，通过读取路由引用 |
| 已生效行为合同 | 继续留在 `openspec/specs/` |
| Schema workflow 与模板 | 继续保留上游 `openspec/schemas/superspec/` 原文，不修改 |

---

## 10. 目标配置结构

### 10.1 修改方式

读取当前 `openspec/config.yaml` 后，以最小方式：

1. 保持第一行：

```yaml
schema: superspec
```

2. 将注释模板区域替换或填充为有效的 `context` 与 `rules`。
3. 不在 `rules` 中加入 schema 不存在的键。
4. 不修改 schema 目录。

### 10.2 推荐注入内容

以下为本阶段目标结构。Codex 必须先按第 8 节核对每条内容在现有权威文档中的依据；对于未找到依据的条目，不得直接注入，应从配置中省略并在报告中记录。

```yaml
schema: superspec

context: |
  Project: DiagnoseToolPy, a web-based diagnostic assistant for system stability work.
  Stack: Python backend managed with uv; React and TypeScript frontend.
  Canonical agent governance entry: AGENTS.md.
  Task-specific document routing entry: docs/README.md.
  Durable project knowledge is file-based; derived indexes are rebuildable caches, not authoritative storage.
  Large-log analysis must preserve server-side directory scanning and streaming-oriented processing boundaries.
  Do not introduce mandatory external infrastructure or databases unless an approved change explicitly revises that constraint.
  Future code, specification, architecture-governance, or behavior changes are governed through openspec/changes/.
  Read only authoritative documents relevant to the affected capability; do not bulk-load generated or unrelated documentation.
  Generated/reference documentation is non-authoritative unless promoted into an approved durable asset.

rules:
  brainstorm:
    - Identify the affected capability or capabilities and the authoritative docs/specs that must be read.
    - Separate durable behavior changes from implementation-only changes.
    - Record non-goals and prohibited expansion areas before proposing a solution.

  proposal:
    - State goals, non-goals, impact scope, risks, validation approach, and affected capabilities.
    - Identify whether living specs or durable architecture documents require updates.
    - Do not propose unrelated refactoring or infrastructure adoption outside the stated need.

  design:
    - Define affected modules and allowed file boundaries; preserve existing architecture constraints unless explicitly revised.
    - Explain decisions, alternatives, risks, rollback or migration considerations, and required validation.
    - Reference relevant authoritative docs rather than duplicating their full contents.

  specs:
    - Specify observable behavior using SHALL or MUST and testable Scenario sections.
    - Modify only capabilities identified in the proposal and preserve backward compatibility unless explicitly changed.
    - Do not encode implementation internals as behavioral requirements.

  tasks:
    - Separate implementation, tests, documentation/spec synchronization, and verification work.
    - Keep tasks within the approved impact scope; do not include incidental cleanup or unrelated refactoring.
    - Identify required durable asset updates explicitly.

  plan:
    - Use file-level micro-steps with validation for each task and list permitted modified paths.
    - Apply TDD for testable behavior; for non-unit-testable work, state an explicit repeatable validation method.
    - Stop and revise artifacts before implementing any newly discovered out-of-scope work.

  apply:
    - Implement only approved plan tasks and paths; record any required deviation before proceeding.
    - Do not execute real business implementation until tool-execution and Git-finalize safeguards are approved for this repository.
    - Preserve evidence of tests, review, worktree and task completion in the required receipt artifacts.

  verify:
    - Run structural validation and confirm task completion, scope compliance, behavior/spec coherence, and validation evidence.
    - Fail verification for unauthorized file changes, unresolved behavior drift, or missing durable-asset updates.
    - Do not recommend finalize while any blocking issue remains.

  finalize:
    - Execute closeout only after verify permits it and repository-specific Git/PR safety prerequisites have been approved.
    - Do not broaden merge, push, cleanup, or PR actions beyond the active change and approved workflow.
    - Record the final outcome and evidence required for later archive and human review.
```

### 10.3 对 `apply` 与 `finalize` 临时安全门禁的说明

上述规则中，下列两条是迁移期间必须保留的安全门禁：

```yaml
apply:
  - Do not execute real business implementation until tool-execution and Git-finalize safeguards are approved for this repository.

finalize:
  - Execute closeout only after verify permits it and repository-specific Git/PR safety prerequisites have been approved.
```

它们的目的不是永久阻塞 SuperSpec，而是在 Phase 3 完成以下工作前阻止误运行高风险链路：

```text
- 核验/安装 Superpowers；
- 明确 Codex、Claude Code、OpenCode 的执行角色；
- 治理 `.claude/` / `.opencode/` 重复入口；
- 审查 finalize 中 push / PR / cleanup 与本项目 Git 工作方式的兼容性。
```

后续 Phase 3 若完成验证，可通过单独 change 更新上述临时门禁。

---

## 11. 配置修改后自检

### Step 5：只读检查配置 diff

```powershell
git diff -- openspec/config.yaml
```

必须确认：

```text
- `schema: superspec` 未变化；
- 只新增/启用 `context` 与 `rules`；
- 没有删除或改写无关配置；
- rules 键严格限定为 brainstorm/proposal/design/specs/tasks/plan/apply/verify/finalize；
- 配置中没有长文档复制、Phase 临时信息或单次 change 内容。
```

若发现 config 有 YAML 缩进风险或无法安全修改，停止并报告。

---

## 12. 允许执行的验证命令

完成配置修改后执行：

```powershell
openspec --version
openspec schemas
openspec validate --all --json
openspec validate --all

git status --short --branch --untracked-files=all
git diff --stat
git diff --name-only
git diff -- openspec/config.yaml
git ls-files --others --exclude-standard docs/rectification/
```

### 12.1 必须验证结果

| 检查项 | 必须结果 |
|---|---|
| `openspec schemas` | 保持识别 `superspec (project)` |
| `openspec validate --all --json` | 0 failed |
| `openspec validate --all` | 全部通过 |
| `openspec/config.yaml` | 仅新增本阶段 context/rules 内容 |
| 新增文件 | 仅 Phase 2 报告 |
| living specs | 无修改 |
| schema templates | 无修改 |
| 业务/工具路径 | 无修改 |

### 12.2 失败处理

若 OpenSpec 在新增 `context` / `rules` 后解析或验证失败：

- 不得修改 schema templates；
- 不得修改 living specs；
- 不得删减既有规则后试错循环超过一次；
- 记录完整错误输出；
- 报告结论写为 `BLOCKED`；
- 向用户回传，由设计端修正配置方案。

允许一次针对 YAML 语法/缩进错误的最小修正；不得将失败扩大为规则重构。

---

## 13. 新增 Phase 2 执行报告

必须新增：

```text
docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
```

### 13.1 报告模板

```markdown
# DiagnoseToolPy SuperSpec Phase 2 项目 Context 与 Artifact Rules 注入报告

> 执行阶段：Phase 2
> 执行工具：Codex
> 执行日期：<YYYY-MM-DD>
> 整改工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`
> 整改分支：`chore/superspec-governance-migration`
> Phase 2 起始 HEAD：`<用户提交 Phase 1/1A 后的新 HEAD>`
> Schema：`superspec` version `4`
> 上游 schema commit：`e1c8f417ee3601208416d988ba3b37d83ddb63f2`

## 1. 执行摘要

- 执行结果：PASS / BLOCKED / STOPPED
- 启动时 worktree 是否 clean：
- `openspec validate --all --json` 启动基线：
- 是否注入 project context：
- 是否注入 artifact rules：
- 是否建议进入 Phase 3：

## 2. 启动门禁核验

| 检查项 | 结果 | 说明 |
|---|---|---|
| 当前 branch 正确 | | |
| Phase 1/1A 已提交且 HEAD 更新 | | |
| 工作树 clean | | |
| 无越界任务书残留 | | |
| 默认 schema 为 `superspec` | | |
| 项目 schema 可识别 | | |
| living specs 验证通过 | | |

## 3. 权威来源读取记录

| 读取资产 | 用途 | 是否修改 |
|---|---|---:|
| `AGENTS.md` | 项目级硬约束依据 | 否 |
| `docs/README.md` | 上下文路由依据 | 否 |
| `work-items/README.md` | 变更真相源冻结依据 | 否 |
| `<其他实际读取文件>` | `<用途>` | 否 |

## 4. 注入规则依据映射

| 注入内容 | 权威来源 | 是否等价提炼 | 备注 |
|---|---|---:|---|
| 项目与技术栈 context | | | |
| durable knowledge / derived index 约束 | | | |
| large-log streaming 边界 | | | |
| change 治理路径 | | | |
| artifact scope / no unrelated refactor | | | |
| apply 临时安全门禁 | | | |
| finalize 临时安全门禁 | | | |

## 5. `openspec/config.yaml` 修改摘要

- `context` 有效行数：
- `rules` artifact keys：
- `rules` 总条目数：
- 是否符合长度约束：
- 是否包含未在现有资产中找到依据的约束：

### 精确 diff

```diff
<粘贴 git diff -- openspec/config.yaml>
```

## 6. 规则键与 Schema 对齐核验

| Rule Key | 是否存在于 SuperSpec v4 Schema | 条目数 | 结论 |
|---|---:|---:|---|
| `brainstorm` | | | |
| `proposal` | | | |
| `design` | | | |
| `specs` | | | |
| `tasks` | | | |
| `plan` | | | |
| `apply` | | | |
| `verify` | | | |
| `finalize` | | | |

## 7. 验证结果

### `openspec schemas`

```text
<输出>
```

### `openspec validate --all --json`

```text
<摘要或完整关键输出>
```

### `openspec validate --all`

```text
<输出>
```

## 8. Git 变更集合

### `git status --short --branch --untracked-files=all`

```text
<输出>
```

### `git diff --stat`

```text
<输出>
```

### `git diff --name-only`

```text
<输出>
```

### 未跟踪文件

```text
<输出>
```

## 9. 保护范围确认

- [ ] 未修改 `AGENT.md` / `AGENTS.md` / `work-items/`
- [ ] 未修改 `docs/README.md` 或既有长期文档
- [ ] 未修改 `docs/rectification/00-*` 至 `04-*`
- [ ] 未修改 `openspec/schemas/superspec/**`
- [ ] 未修改 `openspec/specs/**`
- [ ] 未修改 `openspec/changes/**`
- [ ] 未修改业务、测试、数据、配置或工具专用路径
- [ ] 未复制执行任务书到仓库
- [ ] 未执行 lifecycle / Superpowers / Git 写入命令

## 10. Phase 3 准入结论

### 结论

- ALLOW / BLOCK

### 若 ALLOW，Phase 3 需要解决的问题

```text
- Codex / Claude Code / OpenCode 在本项目的角色边界；
- Superpowers 是否安装、在哪一实现端启用；
- `.claude/` / `.opencode/` 既有 OpenSpec command/skill 与 SuperSpec 的适配/重生成策略；
- `.claude/settings.local.json` 权限边界；
- SuperSpec apply/finalize 中 worktree、commit、push、PR 与当前仓库流程的安全策略；
- 何时解除 config 中 apply/finalize 的临时执行门禁。
```

### 推荐人工提交范围

```text
openspec/config.yaml
docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
```

### 推荐 commit message

```text
chore(openspec): inject project context and superspec artifact rules
```
```

---

## 14. 最终变更集合门禁

Phase 2 结束时，Git 可见变更只允许为：

```text
M  openspec/config.yaml
?? docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
```

不得出现：

```text
docs/rectification/*-codex-execution.md
AGENT.md
AGENTS.md
work-items/**
openspec/schemas/**
openspec/specs/**
openspec/changes/**
任何业务、测试、数据、工具专用文件
```

若出现越界路径：

```text
BLOCKED: Phase 2 produced or discovered out-of-scope paths.
Unexpected paths:
- <path>
No cleanup, staging, commit, or rollback was performed.
```

---

## 15. Codex 回传要求

执行完成后必须回传：

1. `docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md`；
2. Phase 2 启动 HEAD 与 clean status；
3. 启动时 `openspec validate --all --json` 结果；
4. 实际读取的权威规则文件清单；
5. 每项注入 context/rules 的来源映射；
6. `openspec/config.yaml` 精确 diff；
7. `context` 行数、rules 键列表与规则条目数；
8. `openspec schemas` 与最终 `openspec validate --all --json` / `--all` 结果；
9. 最终 `git status --short --branch --untracked-files=all`；
10. `git diff --stat`；
11. `git diff --name-only`；
12. 未跟踪文件列表；
13. 是否允许进入 Phase 3；
14. 未修改禁止路径、未复制执行任务书入库、未执行禁止命令的明确确认。

---

## 16. 用户人工提交策略

Codex 不得提交本阶段变更。

只有当报告结论为 `PASS / ALLOW`，且最终变更集合严格符合第 14 节时，用户方可人工提交：

```bash
git add openspec/config.yaml docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
git commit -m "chore(openspec): inject project context and superspec artifact rules"
```

提交后，用户应回传新的 HEAD 与 clean status，作为 Phase 3 的输入基线。

---

## 17. 后续阶段预告

下一阶段暂定：

```text
Phase 3：实现端与高风险执行链治理
```

其目标不是开发业务，而是处理：

```text
- Claude Code 作为主要 apply 执行端的 Superpowers 前置能力；
- Codex 作为设计/执行文档实施端与复核端的边界；
- OpenCode 备用兼容策略；
- `.claude/` / `.opencode/` 命令与 skills 是否应重生成、保留或冻结；
- worktree、commit、push、PR、finalize 的安全约束；
- 是否可以解除 apply/finalize 的临时禁用门禁。
```

在 Phase 3 完成以前，不得对真实业务 change 执行 SuperSpec 的 `apply` 或 `finalize`。

---

## 18. 参考依据

本任务书依据以下已验证事实编写：

1. OpenSpec 项目配置允许设置默认 schema、注入所有 artifact 共用的 `context`，并按 artifact id 注入 `rules`；项目级 custom schema 存于 `openspec/schemas/` 并随代码版本化。
2. 本项目已引入 `danielhanold/superspec` version 4，其 artifact IDs 为：
   `brainstorm`、`proposal`、`design`、`specs`、`tasks`、`plan`、`apply`、`verify`、`finalize`。
3. SuperSpec v4 中 `apply` 涉及 worktree、subagent-driven-development、TDD 与 review；`verify` 要求全量 OpenSpec 校验；`finalize` 具有 Git closeout、push 和 PR comment 行为。
4. Phase 1A 回传已确认现有 living specs 经结构归一化后验证通过，下一步应把项目长期硬约束接入配置，而不是修改 schema 或业务代码。
