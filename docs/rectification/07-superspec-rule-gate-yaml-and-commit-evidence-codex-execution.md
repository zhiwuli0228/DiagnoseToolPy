# DiagnoseToolPy 全面适配 SuperSpec：Phase 2B 配置门禁语法修正与提交证据链复核执行任务书

> **交付对象**：Codex  
> **执行阶段**：Phase 2B — Rule-Gate YAML Correction & Commit-Evidence Reconciliation  
> **执行任务书定位**：仓库外指令载体，**不得复制、生成或保存到项目仓库内**  
> **执行工作区**：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> **执行分支**：`chore/superspec-governance-migration`  
> **已采用 Schema**：`danielhanold/superspec` version 4，upstream commit `e1c8f417ee3601208416d988ba3b37d83ddb63f2`  
> **前一阶段报告文件**：`docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md`  
> **本阶段性质**：修正尚未生效的执行安全门禁；核对 Phase 2 报告/配置的提交证据链；不得进入 Phase 3

---

## 0. Phase 2A 审核结论：未通过

Phase 2A 报告给出了以下配置 diff 片段：

```diff
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

这暴露两个阻塞问题：

### 0.1 YAML 结构位置错误

新增的两条门禁没有表现为：

```yaml
  apply:
    - <rule>

  finalize:
    - <rule>
```

中的列表项，而表现为无缩进、无 `-` 前缀的顶层 YAML mapping key。

因此，即使 YAML 文件仍能解析、`openspec validate --all` 仍能通过，也不能证明门禁会被作为：

```text
rules.apply
rules.finalize
```

注入对应阶段。

**Phase 2A 的核心目标是保证执行门禁成为实际有效的 artifact rules；当前报告不能证明该目标已完成。**

### 0.2 `apply` 门禁语义被弱化

原定门禁为：

```text
在 Phase 3 完成工具执行端与 Git-finalize 安全治理前，
不得对真实业务 change 执行 SuperSpec apply。
```

但 Phase 2A 新文本仅限制：

```text
do not start high-risk implementation until the active change is authorized and the task scope is clear
```

这存在两个问题：

- 它只限制“high-risk implementation”，未限制普通真实业务实现；
- 它将解锁条件弱化为“change 已授权且 scope 清晰”，未要求 Phase 3 完成工具/worktree/review/Git 安全批准。

因此，即使缩进修正，该文本仍不足以守住迁移期间的风险边界。

### 0.3 Phase 2 报告资产状态不一致

Phase 2 回传曾显示新增：

```text
docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
```

但 Phase 2A 最终 `git status` 只显示：

```text
M  openspec/config.yaml
?? docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
```

并且 Phase 2A 基线 HEAD 已变为：

```text
d34c81ba6355309ebe577006c3b981fde8d08736
```

这可能意味着 Phase 2 已在 Phase 2A 开始前被提交，也可能意味着 `05-*` 报告没有被保留。二者对治理证据链的影响不同，必须查明并记录。

---

## 1. 本阶段目标

本阶段只完成以下工作：

1. 验证当前工作区仍保持 Phase 2A 回传所描述的待修正状态。
2. 核对 `docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md` 与 Phase 2 配置是否已经进入 Git 历史；记录是否发生了未按门禁顺序的提前提交。
3. 读取 `openspec/config.yaml` 的实际完整 YAML 结构，确认 Phase 2A 门禁条目当前真实解析位置。
4. 对 `openspec/config.yaml` 做最小修正：
   - 保留 `rules.tasks` 已完成的 durable docs 收窄规则；
   - 删除错误位置或弱语义的 `apply` / `finalize` 门禁文本；
   - 将严格门禁作为正确缩进的 `rules.apply` / `rules.finalize` 列表项写入。
5. 通过 YAML 解析结果与 OpenSpec 校验双重验证：
   - 门禁文本确实位于 `rules.apply` 和 `rules.finalize` 列表；
   - OpenSpec 项目仍为 `11 passed, 0 failed`。
6. 新增 Phase 2B 报告，给出 Phase 2 系列是否可提交/补充提交，以及是否允许进入 Phase 3 的结论。

---

## 2. 本阶段不应发生的操作

### 2.1 不得提交

Codex 不得执行：

```bash
git add
git commit
git push
git merge
```

用户也应等待本阶段回传后，再决定是否提交或补充提交。

### 2.2 不得进入 Phase 3

本阶段仅修复 Phase 2A 门禁生效性与证据链，不允许：

```text
- 安装 Superpowers
- 修改 `.claude/` / `.opencode/`
- 执行任何 SuperSpec change lifecycle
- 创建演练 change
- 执行 apply / verify / finalize
- 修改业务代码或测试
```

### 2.3 执行任务书不得入库

禁止将本任务书保存到：

```text
docs/rectification/
docs/
openspec/
项目仓库任意位置
```

仓库内本阶段只允许新增正式执行报告：

```text
docs/rectification/07-superspec-rule-gate-yaml-and-commit-evidence-report.md
```

---

## 3. 严格允许范围

### 3.1 允许读取的路径

仅允许读取整改 worktree 内以下路径：

```text
openspec/config.yaml
openspec/schemas/superspec/schema.yaml
docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
AGENTS.md
docs/README.md
work-items/README.md
```

允许通过 Git 只读查询历史涉及的路径：

```text
openspec/config.yaml
docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
```

### 3.2 允许修改的既有文件

仅允许修改：

```text
openspec/config.yaml
```

### 3.3 允许新增的文件

仅允许新增：

```text
docs/rectification/07-superspec-rule-gate-yaml-and-commit-evidence-report.md
```

### 3.4 允许保留但不得修改的已有未提交文件

若启动时已存在：

```text
docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
```

允许其继续处于未跟踪状态，但不得编辑内容。

---

## 4. 严格禁止范围

严禁新增、修改、删除、移动或格式化：

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
docs/rectification/06-*
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
git rm
git mv

openspec init
openspec update
openspec config set
openspec config profile
openspec schema init
openspec schema fork

任何 /opsx:* 或 opsx-* lifecycle 命令
任何 Superpowers skill 或安装命令
```

---

## 5. 启动门禁：验证当前待修正状态

在整改 worktree 中执行：

```powershell
Set-Location E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance

git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git diff --stat
git diff --name-only
git diff -- openspec/config.yaml
git ls-files --others --exclude-standard docs/rectification/
```

### 5.1 必须满足的分支

```text
chore/superspec-governance-migration
```

### 5.2 当前允许存在的待修正集合

依据 Phase 2A 回传，启动时仅允许：

```text
M  openspec/config.yaml
?? docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
```

### 5.3 停止条件

若启动时出现：

```text
- 任意业务、schema、living specs 或工具目录变更；
- 任意 `*-codex-execution.md` 文件；
- 除 `openspec/config.yaml` 与 `06-*` 报告以外的未提交变更；
```

立即停止，不做配置修正：

```text
STOPPED: Phase 2A pending-change baseline contains unexpected paths.
Unexpected paths:
- <path>
No Phase 2B edits were made.
```

---

## 6. 提交证据链复核

### Step 1：核验 Phase 2 报告是否存在且是否已跟踪

执行：

```powershell
Test-Path docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
git ls-files docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
git log --oneline --follow -- docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
git log --oneline --follow -- openspec/config.yaml
git show --stat --oneline HEAD
```

### Step 2：分类记录

| 情况 | 处理 |
|---|---|
| `05-*` 存在且已被 Git 跟踪，log 显示其已随 Phase 2 配置提交 | 记录“Phase 2 在 Phase 2A 审查完成前已提前提交”；不回退，不 BLOCK 本阶段语法修复 |
| `05-*` 存在但未跟踪，且未显示于 status | 记录 Git 状态异常，BLOCK；不得继续修 config |
| `05-*` 不存在且未在 Git 历史中出现 | BLOCK；Phase 2 执行证据缺失 |
| `05-*` 已跟踪，但 `openspec/config.yaml` 未随其进入同一或可解释的提交 | BLOCK；配置与报告证据链不一致 |

### Step 3：若发现提前提交

若 Phase 2 已提前提交，不得回退该提交。报告中必须记录：

```text
PROCESS DEVIATION:
Phase 2 changes were committed before Phase 2A/2B gate review completed.
This historical deviation is retained for traceability and corrected by Phase 2B.
```

最终提交建议应表述为：

```text
提交 Phase 2A + Phase 2B 修正变更
```

而不是：

```text
提交 Phase 2 + Phase 2A + Phase 2B
```

---

## 7. 配置真实结构解析验证

### Step 4：读取 Config 全文

执行：

```powershell
Get-Content openspec/config.yaml
```

在报告中记录完整相关片段：

```yaml
rules:
  tasks:
    ...
  apply:
    ...
  verify:
    ...
  finalize:
    ...
```

### Step 5：使用 YAML Parser 检查规则归属

优先使用当前 Python/uv 环境执行只读解析。不得新增依赖。

先检查解析能力：

```powershell
python -c "import yaml; print('PyYAML available')"
```

若系统 Python 无 `yaml`，允许执行：

```powershell
uv run python -c "import yaml; print('PyYAML available')"
```

若均不可用，允许使用已存在的 Node.js 环境且不安装依赖的情况下尝试已存在 YAML parser；若没有可用 parser，停止并报告，不得靠人工目视认定门禁已生效。

若 PyYAML 可用，执行：

```powershell
python -c "import yaml, pathlib, json; p=pathlib.Path('openspec/config.yaml'); d=yaml.safe_load(p.read_text(encoding='utf-8')); print('top-level keys=', list(d.keys())); print('rule keys=', list((d.get('rules') or {}).keys())); print('apply=', json.dumps((d.get('rules') or {}).get('apply'), ensure_ascii=False)); print('finalize=', json.dumps((d.get('rules') or {}).get('finalize'), ensure_ascii=False)); print('unexpected top-level gate keys=', [k for k in d.keys() if isinstance(k, str) and (k.startswith('Treat apply') or k.startswith('Treat finalize'))])"
```

### 必须确认的问题

修正前，记录：

| 检查项 | 结果 |
|---|---|
| `rules.apply` 是否包含 Phase 2A 新增门禁 | |
| `rules.finalize` 是否包含 Phase 2A 新增门禁 | |
| 顶层是否存在 `Treat apply...` key | |
| 顶层是否存在 `Treat finalize...` key | |
| YAML 是否存在其他超出 `schema/context/rules` 的异常顶层键 | |

### 停止条件

若 YAML 无法解析，停止并报告；不得在无法证明配置当前结构的情况下盲改。

---

## 8. 配置最小修正要求

仅在第 5、6、7 节通过且确认需要修正后，修改：

```text
openspec/config.yaml
```

### 8.1 保留 `rules.tasks` 已完成的收窄规则

必须保留以下语义，不得改回泛化更新义务：

```yaml
  tasks:
    - Update durable docs, including current-state, only when an approved change alters long-term capabilities, architecture boundaries, operations contracts, or recorded limitations.
```

允许保持现有等价文本；不得扩展为每个 change 默认更新 durable docs。

### 8.2 删除错误归属的顶层门禁键

若 YAML 解析显示存在类似以下顶层 key：

```yaml
Treat apply as a temporary execution gate: ...
Treat finalize as a temporary closeout gate: ...
```

必须删除这些顶层键。

### 8.3 正确写入 `rules.apply` 临时硬门禁

在 `rules.apply` 列表中新增或替换为以下严格规则：

```yaml
    - Do not execute real business implementation through SuperSpec apply until Phase 3 approves the implementation tool, worktree, review, and Git-safety prerequisites for this repository.
```

完整结构必须类似：

```yaml
  apply:
    - Implement only approved paths and record any deviation before proceeding.
    - Keep work constrained to the active change and avoid unrelated refactors or scope expansion.
    - Preserve evidence of tests and task completion in the apply receipt.
    - Do not execute real business implementation through SuperSpec apply until Phase 3 approves the implementation tool, worktree, review, and Git-safety prerequisites for this repository.
```

### 8.4 正确写入 `rules.finalize` 临时硬门禁

在 `rules.finalize` 列表中新增或替换为以下严格规则：

```yaml
    - Do not execute Git/PR closeout through SuperSpec finalize until Phase 3 approves the repository-specific merge, push, cleanup, and pull-request safety prerequisites.
```

完整结构必须类似：

```yaml
  finalize:
    - Close out only after verify passes and repository-specific Git safety prerequisites are approved.
    - Do not broaden merge, push, cleanup, or PR actions beyond the active change and approved workflow.
    - Record the final outcome and evidence for archive and human review.
    - Do not execute Git/PR closeout through SuperSpec finalize until Phase 3 approves the repository-specific merge, push, cleanup, and pull-request safety prerequisites.
```

### 8.5 配置限制

修改后必须满足：

```text
- 顶层键只包含 schema、context、rules 以及项目原有可解释配置键；
- `rules.apply` 是 list，包含严格 apply 门禁；
- `rules.finalize` 是 list，包含严格 finalize 门禁；
- 每个 rule key 不超过 5 条；
- 不新增新的项目事实、技术选型或业务能力；
- 不修改 schema templates、living specs 或长期文档。
```

---

## 9. 修正后的结构验证

### Step 6：再次使用 YAML Parser 核验

若 PyYAML 可用，修正后必须执行：

```powershell
python -c "import yaml, pathlib, json; p=pathlib.Path('openspec/config.yaml'); d=yaml.safe_load(p.read_text(encoding='utf-8')); rules=d.get('rules') or {}; print('top-level keys=', list(d.keys())); print('rule keys=', list(rules.keys())); print('apply=', json.dumps(rules.get('apply'), ensure_ascii=False)); print('finalize=', json.dumps(rules.get('finalize'), ensure_ascii=False)); assert isinstance(rules.get('apply'), list); assert isinstance(rules.get('finalize'), list); assert any('Do not execute real business implementation through SuperSpec apply until Phase 3 approves' in x for x in rules['apply']); assert any('Do not execute Git/PR closeout through SuperSpec finalize until Phase 3 approves' in x for x in rules['finalize']); assert not any(isinstance(k, str) and (k.startswith('Treat apply') or k.startswith('Treat finalize')) for k in d.keys()); print('CONFIG_GATE_STRUCTURE_VALID')"
```

若使用 `uv run python` 才能解析，则将命令中的 `python` 替换为 `uv run python`。

### 必须输出

```text
CONFIG_GATE_STRUCTURE_VALID
```

---

## 10. OpenSpec 与 Git 范围验证

### Step 7：执行允许的验证命令

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

### 10.1 必须达到的结果

| 项目 | 必须结果 |
|---|---|
| `openspec schemas` | 识别 `superspec (project)` |
| `openspec validate --all --json` | `11 passed, 0 failed` |
| `openspec validate --all` | `11 passed, 0 failed` |
| YAML Parser Gate Check | `CONFIG_GATE_STRUCTURE_VALID` |
| 修改既有文件 | 仅 `openspec/config.yaml` |
| 新增报告 | `06-*` 可保留，新增 `07-*` |
| schema / specs / changes | 无修改 |
| 业务 / 工具资产 | 无修改 |

### 10.2 允许的最终变更集合

根据证据链核验结果分两种情况。

#### 情况 A：Phase 2 已提前提交，当前仅需提交修正

允许最终可见集合：

```text
M  openspec/config.yaml
?? docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
?? docs/rectification/07-superspec-rule-gate-yaml-and-commit-evidence-report.md
```

#### 情况 B：Phase 2 尚未提交且 `05-*` 仍为可见未跟踪资产

允许最终可见集合：

```text
M  openspec/config.yaml
?? docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
?? docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
?? docs/rectification/07-superspec-rule-gate-yaml-and-commit-evidence-report.md
```

出现其他路径即 `BLOCKED`。

---

## 11. 新增 Phase 2B 正式报告

必须新增：

```text
docs/rectification/07-superspec-rule-gate-yaml-and-commit-evidence-report.md
```

### 报告模板

```markdown
# DiagnoseToolPy SuperSpec Phase 2B 配置门禁语法修正与提交证据链复核报告

> 执行阶段：Phase 2B
> 执行工具：Codex
> 执行日期：<YYYY-MM-DD>
> 整改工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`
> 整改分支：`chore/superspec-governance-migration`
> 起始 HEAD：`<current HEAD>`
> Schema：`superspec` version `4`
> 上游 schema commit：`e1c8f417ee3601208416d988ba3b37d83ddb63f2`

## 1. 执行摘要

- 执行结果：PASS / BLOCKED / STOPPED
- Phase 2A 审核结论：未通过
- 本阶段修复目标：
  - 纠正 `rules.apply` / `rules.finalize` 门禁 YAML 归属
  - 恢复严格的 Phase 3 前真实执行禁用语义
  - 查明 Phase 2 `05-*` 报告与配置的提交证据状态
- 是否修改 `openspec/config.yaml`：
- 是否建议用户提交本阶段修正：
- 是否允许进入 Phase 3：

## 2. 启动状态核验

| 检查项 | 结果 | 说明 |
|---|---|---|
| 当前 branch | | |
| 当前 HEAD | | |
| 启动可见变更集合 | | |
| 是否仅包含预期 Phase 2A 待修正资产 | | |
| 是否存在任务书误入仓库 | | |

## 3. Phase 2 提交证据链复核

### 查询结果

```text
<粘贴 Test-Path / git ls-files / git log -- docs/rectification/05-* / git log -- openspec/config.yaml 的关键输出>
```

| 核验项 | 结果 |
|---|---|
| `05-*` 报告是否存在 | |
| `05-*` 报告是否 tracked | |
| `05-*` 报告对应 commit | |
| Phase 2 config 是否已进入历史 | |
| 是否发生 Phase 2 提前提交 | |
| 证据链是否可继续修正而无需回退 | |

### 过程偏差记录（如适用）

```text
<若已提前提交，写入 PROCESS DEVIATION 记录；若未发生则写“无”。>
```

## 4. 修正前 YAML 结构解析

### Config 相关原文片段

```yaml
<粘贴修正前 rules.tasks / apply / verify / finalize 片段>
```

### Parser 输出

```text
<粘贴修正前 YAML parser 的 top-level keys / rule keys / apply / finalize / unexpected top-level gate keys 输出>
```

| 检查项 | 修正前结果 |
|---|---|
| `rules.apply` 是否包含严格门禁 | |
| `rules.finalize` 是否包含严格门禁 | |
| 是否存在错误顶层 `Treat apply...` key | |
| 是否存在错误顶层 `Treat finalize...` key | |
| 是否存在其他未知顶层键 | |

## 5. 配置最小修正记录

### `rules.tasks`

- 是否保留 durable docs 收窄语义：
- 实际最终文本：

### `rules.apply`

- 删除/替换的错误或弱门禁文本：
- 最终严格门禁文本：
- 是否确认为 YAML list item：

### `rules.finalize`

- 删除/替换的错误或弱门禁文本：
- 最终严格门禁文本：
- 是否确认为 YAML list item：

## 6. 修正后 YAML Parser 验证

```text
<粘贴 CONFIG_GATE_STRUCTURE_VALID 及关键解析输出>
```

| 检查项 | 修正后结果 |
|---|---|
| 顶层是否无错误门禁 key | |
| `rules.apply` 是否为 list | |
| `rules.apply` 是否包含严格 Phase 3 门禁 | |
| `rules.finalize` 是否为 list | |
| `rules.finalize` 是否包含严格 Phase 3 门禁 | |

## 7. OpenSpec 验证结果

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

- [ ] 未修改 schema / living specs / changes
- [ ] 未修改历史整改报告 `00-*` 至 `06-*`
- [ ] 未修改业务、测试、数据、工具资产
- [ ] 未修改 `AGENTS.md`、`work-items/README.md` 或其他权威来源
- [ ] 未将执行任务书复制入库
- [ ] 未执行 lifecycle / Superpowers / Git 写入命令

## 10. 提交与 Phase 3 准入结论

### 提交范围

根据 Phase 2 是否已提前提交，列出准确提交文件集合。

### 结论

- 是否允许人工提交本阶段修正：ALLOW / BLOCK
- 是否允许进入 Phase 3：ALLOW / BLOCK

### 建议提交信息

若 Phase 2 已提前提交：

```text
fix(openspec): enforce superspec apply and finalize safety gates
```

若 Phase 2 尚未提交：

```text
chore(openspec): inject governed superspec context and execution gates
```
```

---

## 12. 人工提交策略

Codex 不得提交。

若 Phase 2B 结果为 `ALLOW`，用户只按报告确定的实际证据状态提交：

### 若 Phase 2 已提前提交

```bash
git add openspec/config.yaml docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md docs/rectification/07-superspec-rule-gate-yaml-and-commit-evidence-report.md
git commit -m "fix(openspec): enforce superspec apply and finalize safety gates"
```

### 若 Phase 2 尚未提交

```bash
git add openspec/config.yaml docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md docs/rectification/07-superspec-rule-gate-yaml-and-commit-evidence-report.md
git commit -m "chore(openspec): inject governed superspec context and execution gates"
```

提交后请核验：

```bash
git status --short --branch --untracked-files=all
git rev-parse HEAD
```

工作树 clean 后，再将新 HEAD 与 Phase 2B 报告回传以进入 Phase 3。

---

## 13. 参考事实

- OpenSpec `openspec/config.yaml` 通过 `context` 与按 artifact id 组织的 `rules` 向工作流阶段注入项目约束；规则必须实际嵌套在对应 artifact key 下才构成该阶段的规则。
- 当前项目已采用 SuperSpec v4 schema，包含 `apply` 与 `finalize` artifact；对其安全门禁的治理必须以对应 `rules.apply` / `rules.finalize` 条目实际存在为准。
- `openspec validate --all` 证明 living specs 的结构校验通过，但不能替代对 `config.yaml` 中自定义规则归属与语义的独立验证。
