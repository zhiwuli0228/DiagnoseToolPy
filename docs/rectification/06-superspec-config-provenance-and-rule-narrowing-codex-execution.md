# DiagnoseToolPy 全面适配 SuperSpec：Phase 2A 配置来源一致性复核与规则收口执行任务书

> **交付对象**：Codex  
> **执行阶段**：Phase 2A — Configuration Provenance Audit & Rule Narrowing  
> **执行任务书定位**：仓库外指令载体，**不得保存或复制到项目仓库中**  
> **执行工作区**：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> **执行分支**：`chore/superspec-governance-migration`  
> **执行前状态**：Phase 2 已执行但尚未提交，当前只有 `openspec/config.yaml` 修改与 Phase 2 执行报告新增  
> **目标 Schema**：`danielhanold/superspec` version 4，upstream commit `e1c8f417ee3601208416d988ba3b37d83ddb63f2`  
> **本阶段性质**：对未提交的 Phase 2 配置注入进行来源一致性复核与必要最小修正；不得进入工具执行端治理阶段

---

## 0. 为什么需要 Phase 2A

Phase 2 已取得以下正面结果：

```text
- `openspec/config.yaml` 已注入 project context 与 artifact rules；
- `openspec schemas` 已识别 `superspec (project)`；
- `openspec validate --all --json` 已达到 11 passed, 0 failed；
- 可见变更范围表面上符合 Phase 2 允许范围。
```

但回传同时暴露两个不能直接放行提交的问题。

### 0.1 权威来源读取路径错误

Phase 2 任务要求在整改 worktree 内读取当前分支的权威资产。然而，Codex 回传的实际读取路径为：

```text
E:/009workspace/claudecode/DiagnoseToolPy/AGENTS.md
E:/009workspace/claudecode/DiagnoseToolPy/docs/README.md
E:/009workspace/claudecode/DiagnoseToolPy/docs/02-harness/harness-standard.md
E:/009workspace/claudecode/DiagnoseToolPy/docs/01-architecture/module-boundaries.md
E:/009workspace/claudecode/DiagnoseToolPy/docs/01-architecture/storage-contract.md
E:/009workspace/claudecode/DiagnoseToolPy/docs/06-operations/server-directory-access.md
E:/009workspace/claudecode/DiagnoseToolPy/docs/06-operations/security-policy.md
E:/009workspace/claudecode/DiagnoseToolPy/docs/03-openspec/*.md
```

这些文件来自原工作区，而不是当前待提交配置所在的整改 worktree：

```text
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance/
```

这会导致：

```text
config 中的规则来源
≠
当前整改分支中将被提交的权威资产来源
```

即使两边正文恰好相同，也必须重新以整改 worktree 内的文件作为来源进行复核并留下证据。

### 0.2 可能重新引入过度更新规则

Phase 2 回传摘要称：

```text
rules.tasks:
- 同步 docs 与 current-state
```

此前治理判断已经明确：

```text
`docs/00-project/current-state.md` 仅在系统长期能力、对外行为、
架构边界、关键依赖/运行方式或已知限制发生变化时更新；
普通 bugfix、纯实现调整和短期任务不得强制更新该文件。
```

因此需要读取实际 `openspec/config.yaml` 内容，确认它是否将“更新 current-state”写成所有 task 的默认强制义务。

若存在该表达，必须将其收窄为：

```text
Only identify/update durable project documents when the approved change alters long-term capability, architecture boundary, operational contract, or documented limitation.
```

---

## 1. 本阶段结论目标

本阶段结束时，应形成以下结论之一：

### PASS

满足：

```text
- 所有注入到 config 的约束都能在整改 worktree 内的权威资产中找到依据；
- 若原工作区与整改 worktree 来源文件存在差异，已证明 config 以整改 worktree 为准；
- `rules.tasks` 等规则未强制所有变更更新 `current-state.md`，或已经最小修正；
- `apply` 与 `finalize` 的临时安全门禁仍存在；
- OpenSpec 全量验证继续通过；
- 变更仍仅限于 `openspec/config.yaml` 与新增 Phase 2/2A 报告。
```

### BLOCK

任一成立即 BLOCK：

```text
- config 中存在无法从整改 worktree 权威资产找到依据的长期约束；
- config 注入内容改变了已批准的项目约束，而无法通过最小删除/收窄修复；
- 除允许路径外出现其他工作树变更；
- OpenSpec 全量验证失败；
- 发现 Phase 2 报告与实际配置不一致且无法安全归一。
```

---

## 2. 本阶段严格不允许提交 Phase 2 当前状态

Codex 不得在本阶段执行提交。用户也应等待 Phase 2A 结论后再提交。

当前允许保留的 Phase 2 未提交集合应为：

```text
M  openspec/config.yaml
?? docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
```

Phase 2A 最终新增：

```text
?? docs/rectification/06-superspec-config-provenance-and-rule-narrowing-report.md
```

---

## 3. 任务书文件存放纪律

本任务书是执行输入，不是项目治理产物。

严禁将本文件复制、移动或另存为：

```text
docs/rectification/*-codex-execution.md
docs/**
openspec/**
项目根目录任何文件
```

仓库中只允许新增 Codex 实际执行形成的报告：

```text
docs/rectification/06-superspec-config-provenance-and-rule-narrowing-report.md
```

若启动时发现任意新的 `*-codex-execution.md` 出现在仓库内，立即停止，不得自行删除。

---

## 4. 严格允许范围

### 4.1 允许读取：整改 worktree 中的权威资产

所有治理依据读取**必须优先且实际来自整改 worktree**：

```text
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance/AGENTS.md
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance/docs/README.md
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance/docs/02-harness/**
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance/docs/01-architecture/module-boundaries.md
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance/docs/01-architecture/storage-contract.md
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance/docs/06-operations/server-directory-access.md
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance/docs/06-operations/security-policy.md
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance/docs/03-openspec/**
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance/work-items/README.md
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance/openspec/config.yaml
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance/openspec/schemas/superspec/schema.yaml
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance/docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
```

### 4.2 允许读取：原工作区，仅用于来源偏差比对

为评估 Phase 2 误读来源的影响，允许只读访问原工作区中 Phase 2 已报告读取过的同路径文件：

```text
E:/009workspace/claudecode/DiagnoseToolPy/AGENTS.md
E:/009workspace/claudecode/DiagnoseToolPy/docs/README.md
E:/009workspace/claudecode/DiagnoseToolPy/docs/02-harness/harness-standard.md
E:/009workspace/claudecode/DiagnoseToolPy/docs/01-architecture/module-boundaries.md
E:/009workspace/claudecode/DiagnoseToolPy/docs/01-architecture/storage-contract.md
E:/009workspace/claudecode/DiagnoseToolPy/docs/06-operations/server-directory-access.md
E:/009workspace/claudecode/DiagnoseToolPy/docs/06-operations/security-policy.md
E:/009workspace/claudecode/DiagnoseToolPy/docs/03-openspec/proposal-rule.md
E:/009workspace/claudecode/DiagnoseToolPy/docs/03-openspec/design-rule.md
E:/009workspace/claudecode/DiagnoseToolPy/docs/03-openspec/spec-rule.md
E:/009workspace/claudecode/DiagnoseToolPy/docs/03-openspec/tasks-rule.md
```

限制：

```text
- 原工作区只用于 hash/diff 比对，不得作为本阶段 config 规则依据；
- 若两边有差异，必须以整改 worktree 内容为准；
- 不得修改原工作区任意文件。
```

### 4.3 允许修改的既有文件

仅允许在确有必要时修改：

```text
openspec/config.yaml
```

### 4.4 允许新增的文件

仅允许新增：

```text
docs/rectification/06-superspec-config-provenance-and-rule-narrowing-report.md
```

### 4.5 允许保留但不得修改的 Phase 2 文件

```text
docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
```

---

## 5. 严格禁止范围

禁止修改或新增：

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
docs/rectification/05-*
openspec/schemas/**
openspec/specs/**
openspec/changes/**
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

禁止执行：

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

任何 /opsx:* 或 opsx-* lifecycle
任何 Superpowers skill 或安装命令
```

---

## 6. 启动门禁

### Step 1：检查工作区身份与 Phase 2 未提交集合

在整改 worktree 中执行：

```powershell
Set-Location E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance

git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git diff --name-only
git diff --stat
git diff -- openspec/config.yaml
git ls-files --others --exclude-standard docs/rectification/
```

必须满足：

```text
分支：chore/superspec-governance-migration
工作树变更仅为：
  M  openspec/config.yaml
  ?? docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
无其他未跟踪任务书或范围外文件。
```

### 停止条件

若出现任何范围外路径，包括：

```text
docs/rectification/*-codex-execution.md
```

立即停止并回传：

```text
STOPPED: Phase 2 pending-change set contains out-of-scope files.
Unexpected paths:
- <path>
No Phase 2A edits were made.
```

---

## 7. 基线验证

### Step 2：验证当前 schema 与配置仍可工作

执行：

```powershell
openspec --version
openspec schemas
openspec validate --all --json
openspec validate --all
```

必须满足：

```text
- `openspec schemas` 识别 `superspec (project)`；
- `openspec validate --all --json` 为 11 passed, 0 failed；
- `openspec validate --all` 为 11 passed, 0 failed。
```

若验证失败，停止，不得修改 config。

---

## 8. Phase 2 来源偏差复核

### Step 3：对 Phase 2 所读来源做文件级比对

对下列文件分别在原工作区和整改 worktree 中计算 hash，并仅在 hash 不一致时输出文本 diff：

```powershell
$Original = "E:/009workspace/claudecode/DiagnoseToolPy"
$Governance = "E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance"

$Paths = @(
  "AGENTS.md",
  "docs/README.md",
  "docs/02-harness/harness-standard.md",
  "docs/01-architecture/module-boundaries.md",
  "docs/01-architecture/storage-contract.md",
  "docs/06-operations/server-directory-access.md",
  "docs/06-operations/security-policy.md",
  "docs/03-openspec/proposal-rule.md",
  "docs/03-openspec/design-rule.md",
  "docs/03-openspec/spec-rule.md",
  "docs/03-openspec/tasks-rule.md"
)

foreach ($p in $Paths) {
  Get-FileHash "$Original/$p" -Algorithm SHA256
  Get-FileHash "$Governance/$p" -Algorithm SHA256
}
```

若某个路径在任一工作区中不存在：

- 记录缺失；
- 不得推断其内容；
- 若 config 中对应约束只能依赖缺失文件，则将该约束认定为未有当前分支依据。

### Step 4：差异处理原则

| 结果 | 处理方式 |
|---|---|
| 两边 hash 相同 | Phase 2 的来源路径错误不造成文本依据偏差，但仍需在报告中纠正 provenance |
| 两边 hash 不同，但整改 worktree 可支撑现有 config 条目 | 保留条目，报告中以整改 worktree 为新依据 |
| 两边 hash 不同，现有 config 条目只由原工作区支持 | 从 config 删除或收窄该条目 |
| 整改 worktree 文件缺失而条目依赖它 | 删除或收窄条目；若为关键规则则 BLOCK |

---

## 9. 逐条核验 `openspec/config.yaml`

### Step 5：读取实际配置全文

执行：

```powershell
Get-Content openspec/config.yaml
```

在报告中记录：

```text
- `context` 实际有效行数；
- `rules` 实际存在的 artifact key；
- 每个 rule key 的实际条目数；
- apply/finalize 临时门禁是否存在；
- 是否包含对 `current-state.md` 的无条件更新要求；
- 是否包含没有被当前 worktree 权威资产支持的事实或约束。
```

### Step 6：必须核验的 context 条目

对配置中的每一条 context 事实，必须在整改 worktree 中找到依据。重点核验：

| Config 内容类型 | 是否可保留的判定 |
|---|---|
| 项目定位、技术栈 | `AGENTS.md` 或 `docs/README.md` 有依据 |
| 文件系统为 durable truth | `storage-contract.md` / harness 有依据 |
| 索引可重建、非权威数据 | `storage-contract.md` / architecture 有依据 |
| 禁止强制外部数据库 | 权威文档有明确约束 |
| 服务端目录扫描、流式日志处理 | architecture / operations 文档有依据 |
| 不依赖 embeddings 的 retrieval | 权威文档有明确约束 |
| AI 诊断辅助性、保留人工确认字段 | 权威文档有明确约束；若无则移除 |
| 避免 scope creep | harness / governance 有依据 |

不得因为配置内容“听起来合理”而保留没有权威来源的条目。

### Step 7：必须核验的 rules 条目

规则键必须且只能为：

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

必须核验：

```text
- 每个键不超过 5 条；
- 总条目不超过 35 条；
- 每条均有当前整改 worktree 内的治理依据；
- `apply` 仍明确禁止在工具与 Git-finalize 安全治理完成前执行真实业务实现；
- `finalize` 仍明确要求完成 repository-specific Git/PR safety prerequisites 后才可运行 closeout；
- 不存在“所有变更都必须更新 current-state.md”或等价过度要求。
```

---

## 10. 必要时的最小修正规则

只有在第 8、9 节发现问题时，才允许编辑 `openspec/config.yaml`。

### 10.1 对无依据 context 的处理

若 config 中存在无法由整改 worktree 权威资产支持的条目：

```text
- 删除该条目；或
- 收窄为可由已有资产支持的等价描述。
```

不得修改权威文档来反向支持配置。

### 10.2 对 `current-state.md` 过度更新要求的处理

若实际 `rules.tasks`、`rules.verify` 或其他规则中包含：

```text
- Always update docs and current-state.
- Synchronize docs/current-state for every task/change.
- 每个变更完成必须更新 current-state.md。
```

或语义等价的强制要求，替换为以下收窄规则之一，保持条目数量不增加：

```yaml
  tasks:
    - Identify durable documentation or living-spec updates only when the approved change alters long-term capability, architecture boundary, operational contract, or documented limitation.
```

若该要求位于 `verify` 中，则改为：

```yaml
  verify:
    - Confirm durable documentation updates only when the approved change alters long-term capability, architecture boundary, operational contract, or documented limitation.
```

不得要求普通 bugfix、格式修正、实现细节修改默认更新 `current-state.md`。

### 10.3 对 Apply / Finalize 临时门禁的修复

若配置未包含以下等价门禁，必须在相应已有条目内进行最小修正；不得增加到超过每个 key 5 条或总数 35 条：

```yaml
  apply:
    - Do not execute real business implementation until tool-execution and Git-finalize safeguards are approved for this repository.

  finalize:
    - Execute closeout only after verify permits it and repository-specific Git/PR safety prerequisites have been approved.
```

### 10.4 禁止扩大配置

不得在本阶段新增：

```text
- 新的技术栈选择；
- 新业务能力；
- 新工具安装策略；
- 新 schema 行为；
- 任何具体真实 change 的要求；
- 详细架构正文。
```

---

## 11. 生成 Phase 2A 报告

必须新增：

```text
docs/rectification/06-superspec-config-provenance-and-rule-narrowing-report.md
```

### 报告模板

```markdown
# DiagnoseToolPy SuperSpec Phase 2A 配置来源一致性复核与规则收口报告

> 执行阶段：Phase 2A
> 执行工具：Codex
> 执行日期：<YYYY-MM-DD>
> 整改工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`
> 整改分支：`chore/superspec-governance-migration`
> Phase 2 起始 HEAD：`<当前 HEAD>`
> Schema：`superspec` version `4`
> 上游 schema commit：`e1c8f417ee3601208416d988ba3b37d83ddb63f2`

## 1. 执行摘要

- 执行结果：PASS / BLOCKED / STOPPED
- Phase 2 判定：CONDITIONAL PASS
- 触发 Phase 2A 原因：
  - Phase 2 读取了原工作区的权威资产，而非整改 worktree 的同路径资产
  - 需要核验 `current-state.md` 是否被写成默认强制更新目标
- 是否修改 `openspec/config.yaml`：
- 是否建议提交 Phase 2 + Phase 2A：
- 是否建议进入 Phase 3：

## 2. 启动门禁与验证基线

| 项目 | 结果 | 说明 |
|---|---|---|
| 当前 branch | | |
| 当前 HEAD | | |
| Phase 2 待提交集合是否仅包含授权路径 | | |
| `openspec schemas` | | |
| `openspec validate --all --json` | | |
| 是否存在任务书误入仓库 | | |

## 3. Phase 2 读取来源偏差确认

- Phase 2 实际错误读取根路径：`E:/009workspace/claudecode/DiagnoseToolPy`
- 本阶段权威读取根路径：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`

| Relative Path | 原工作区 SHA256 | 整改 Worktree SHA256 | 是否一致 | 差异对 Config 的影响 |
|---|---|---|---:|---|
| `AGENTS.md` | | | | |
| `docs/README.md` | | | | |
| `docs/02-harness/harness-standard.md` | | | | |
| `docs/01-architecture/module-boundaries.md` | | | | |
| `docs/01-architecture/storage-contract.md` | | | | |
| `docs/06-operations/server-directory-access.md` | | | | |
| `docs/06-operations/security-policy.md` | | | | |
| `docs/03-openspec/proposal-rule.md` | | | | |
| `docs/03-openspec/design-rule.md` | | | | |
| `docs/03-openspec/spec-rule.md` | | | | |
| `docs/03-openspec/tasks-rule.md` | | | | |

### Provenance 修正结论

- 当前 config 规则最终以哪些整改 worktree 文件为依据：
- 是否存在只能由原工作区支撑、不能由整改 worktree 支撑的配置条目：
- 处理结果：

## 4. 实际 Config 内容检查

### Context 统计

- 有效行数：
- 是否超过 25 行：
- 是否包含无权威依据条目：

| Context 条目摘要 | 整改 Worktree 权威依据 | 保留/删除/收窄 | 理由 |
|---|---|---|---|
| | | | |

### Rules 统计

| Rule Key | 条目数 | Schema 中是否存在 | 是否有当前分支依据 | 是否需要修正 |
|---|---:|---:|---:|---:|
| `brainstorm` | | | | |
| `proposal` | | | | |
| `design` | | | | |
| `specs` | | | | |
| `tasks` | | | | |
| `plan` | | | | |
| `apply` | | | | |
| `verify` | | | | |
| `finalize` | | | | |

- Rules 总条目数：
- 是否超过 35 条：
- 是否存在 schema 不支持的 key：

## 5. 重点风险核验

### 5.1 `current-state.md` 更新范围

- 配置是否存在默认强制更新 `current-state.md` 的表达：
- 若存在，原文：
- 修正后文本：
- 修正结论：仅在长期能力、架构边界、运维合同或已记录限制改变时更新 durable docs。

### 5.2 `apply` 临时安全门禁

- 是否存在：
- 实际文本：
- 是否需要修正：

### 5.3 `finalize` 临时安全门禁

- 是否存在：
- 实际文本：
- 是否需要修正：

## 6. `openspec/config.yaml` 最终 Diff

```diff
<粘贴相对于当前 HEAD 的完整 git diff -- openspec/config.yaml>
```

说明：

- Phase 2 已加入的 context/rules：
- Phase 2A 是否进一步做最小修正：
- 未修改 schema、specs 或业务资产的确认：

## 7. 验证结果

### `openspec schemas`

```text
<输出>
```

### `openspec validate --all --json`

```text
<输出摘要>
```

### `openspec validate --all`

```text
<输出>
```

## 8. 最终 Git 变更集合

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

### 未跟踪报告文件

```text
<输出>
```

## 9. 保护范围确认

- [ ] 未修改原工作区任何资产
- [ ] 未修改 `AGENTS.md`、`docs/README.md` 或既有长期文档
- [ ] 未修改 `docs/rectification/00-*` 至 `05-*`
- [ ] 未修改 `openspec/schemas/**`
- [ ] 未修改 `openspec/specs/**`
- [ ] 未修改 `openspec/changes/**`
- [ ] 未修改业务、测试、数据、工具专用文件
- [ ] 未将执行任务书复制进入仓库
- [ ] 未执行 lifecycle、Superpowers 或禁止的 Git 命令

## 10. 提交与 Phase 3 准入建议

### 结论

- 是否建议用户提交 Phase 2 + Phase 2A：ALLOW / BLOCK
- 是否允许进入 Phase 3：ALLOW / BLOCK

### 若允许提交，文件范围

```text
openspec/config.yaml
docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
docs/rectification/06-superspec-config-provenance-and-rule-narrowing-report.md
```

### 建议 commit message

```text
chore(openspec): inject governed superspec context and artifact rules
```
```

---

## 12. 修正后验证命令

完成必要的最小修正并生成报告后，执行：

```powershell
openspec schemas
openspec validate --all --json
openspec validate --all

git status --short --branch --untracked-files=all
git diff --stat
git diff --name-only
git diff -- openspec/config.yaml
git ls-files --others --exclude-standard docs/rectification/
```

### 必须满足

```text
- `openspec schemas` 仍识别 `superspec (project)`；
- `openspec validate --all --json` 为 11 passed, 0 failed；
- 最终可见变更仅包含：
    M  openspec/config.yaml
    ?? docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
    ?? docs/rectification/06-superspec-config-provenance-and-rule-narrowing-report.md
- 不存在任何 `*-codex-execution.md` 入库；
- 不存在其他越界文件。
```

若 config 无需修正，则 `openspec/config.yaml` 仍保留 Phase 2 的修改状态，报告中记录“复核后无需修改”。

---

## 13. Codex 回传要求

执行结束后必须回传：

1. `docs/rectification/06-superspec-config-provenance-and-rule-narrowing-report.md`；
2. 启动状态与当前 HEAD；
3. 原工作区与整改 worktree 权威文件的 SHA256 比对表；
4. 实际 `openspec/config.yaml` 中 context/rules 的统计；
5. 对 `current-state.md` 过度更新风险的核验结果及必要修正；
6. 对 `apply` / `finalize` 临时安全门禁的核验结果；
7. `openspec/config.yaml` 完整 diff；
8. `openspec schemas`、`openspec validate --all --json`、`openspec validate --all` 结果；
9. 最终 Git 可见变更集合；
10. 是否允许用户提交 Phase 2 + Phase 2A；
11. 是否允许进入 Phase 3；
12. 未修改禁止路径、未将任务书入库、未执行禁止命令的明确确认。

---

## 14. 用户提交策略

Codex 不得提交。

只有当 Phase 2A 结论为 `ALLOW` 且最终集合符合门禁时，用户可人工提交：

```bash
git add openspec/config.yaml docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md docs/rectification/06-superspec-config-provenance-and-rule-narrowing-report.md
git commit -m "chore(openspec): inject governed superspec context and artifact rules"
```

提交后必须验证工作树 clean，并将新的 HEAD 回传，作为 Phase 3 的基线。

---

## 15. Phase 3 预告

Phase 2A 通过并提交后，进入：

```text
Phase 3：实现端与 SuperSpec 高风险执行链治理
```

该阶段将处理：

```text
- Claude Code 是否作为默认 `apply` / Superpowers 执行端；
- Codex 在项目中的设计文档执行、验证与审计角色边界；
- OpenCode 的备用兼容方式；
- `.claude/` / `.opencode/` 当前 opsx commands/skills 是否需要冻结、刷新或重新生成；
- Superpowers 安装与能力验证；
- apply 所需 worktree、TDD、review 的安全验证；
- finalize 涉及 merge、push、PR comment 行为的安全控制；
- 是否解除 config 中对真实业务 apply/finalize 的临时门禁。
```

Phase 3 完成前，仍不得对真实业务 change 执行 SuperSpec 的 `apply` 或 `finalize`。
