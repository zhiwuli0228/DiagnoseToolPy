# DiagnoseToolPy 全面适配 SuperSpec：Phase 0A 干净迁移基线与治理权威收敛执行任务书

> **交付对象**：Codex  
> **执行阶段**：Phase 0A — Clean Rectification Baseline & Governance Authority  
> **前置阶段**：Phase 0 迁移审计与基线报告已完成  
> **目标项目**：`E:/009workspace/claudecode/DiagnoseToolPy`  
> **目标工作流**：OpenSpec + `danielhanold/superspec` schema  
> **执行前置条件**：用户已手动提交截止当前的所有已有修改，使原工作区回到干净状态  
> **本阶段性质**：治理整改；不得修改业务实现；不得安装或启用 SuperSpec schema

---

## 1. 本阶段目标

Phase 0 审计已经确认：

1. 当前项目尚未安装 `openspec/schemas/superspec/`，且 `openspec/config.yaml` 仍采用 `schema: spec-driven`。
2. 当前没有 active OpenSpec change，因此后续迁移不会与进行中的 OpenSpec change 直接冲突。
3. 审计时原工作区包含未提交业务代码、索引与运行产物改动，不能作为治理整改的可靠执行基线。
4. `AGENT.md` 与 `AGENTS.md` 承担重复的项目入口规则职责。
5. `work-items/` 与 `openspec/changes/` 并存，未来存在双重任务真相源风险。
6. `.claude/` 与 `.opencode/` 存在重复 OpenSpec 命令/skills 资产，但该问题不应阻断建立独立迁移基线；它将在后续专门阶段治理。

本阶段只完成以下四件事：

1. 在用户已提交现有修改的前提下，验证原仓库为干净基线。
2. 从该干净 HEAD 创建独立整改 branch 与 linked worktree，后续 SuperSpec 整改仅在该隔离工作区进行。
3. 在不丢失任何既有规则的前提下，统一 `AGENT.md` / `AGENTS.md` 的项目级权威入口关系。
4. 冻结 `work-items/` 作为 legacy 资产来源，明确未来代码变更任务以 `openspec/changes/` 为唯一治理路径。

**本阶段不安装 SuperSpec schema，不修改 OpenSpec 默认 schema，不修改业务代码，不治理 `.claude/` / `.opencode/` 内容。**

---

## 2. 执行依据与重要修正

### 2.1 采用独立 worktree 的原因

本项目接下来的治理整改会持续多个阶段，并且未来 SuperSpec 的实现链路本身涉及 worktree、验证和 Git closeout。整改工作必须与原业务开发工作区隔离。

Git linked worktree 允许同一仓库在不同目录同时检出不同分支，每个 worktree 具有独立的工作目录、`HEAD` 与 index。因此，本阶段必须创建专用整改 worktree，而不是在原 `claude_master` 工作目录中直接开始修改治理资产。

### 2.2 对审计结论的处理修正

Phase 0 报告提出 `.claude/` 与 `.opencode/` 的重复工具资产可能阻塞 Phase 1。该风险真实存在，但**不是本阶段的前置阻塞**：

- OpenSpec custom schema 是项目级资产，可单独存放于 `openspec/schemas/<schema-name>/`；
- `openspec/config.yaml` 可在后续阶段独立激活默认 schema；
- 工具专用命令/skills 是否重生成或收敛，应在 schema 引入和验证方案明确后处理，避免提前破坏已有工具入口。

因此，本阶段不修改 `.claude/` 或 `.opencode/`，仅记录其待治理状态。

### 2.3 参考依据

- OpenSpec 官方 customization：`openspec/config.yaml` 支持默认 schema、项目 context 与 artifact rules；项目级 custom schemas 存储于 `openspec/schemas/`。
- OpenSpec 官方 concepts / CLI：schema 定义 artifact 类型及依赖，支持项目级 schema validation。
- Git 官方 `git-worktree` 文档：`git worktree add -b <branch> <path> <commit-ish>` 从指定 commit 创建新 branch 并在独立 linked worktree 检出。

---

## 3. 本阶段完成标准

本阶段完成后，必须满足：

```text
原工作区：
E:/009workspace/claudecode/DiagnoseToolPy
- 保持用户提交后的干净状态
- 保持所在分支不被整改任务修改
- 不新增治理修改

整改工作区：
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance
- 基于用户提交后的最新 HEAD 创建
- 分支为 chore/superspec-governance-migration
- 仅包含本任务允许的治理文档/入口变更
```

并形成以下治理结论：

```text
AGENTS.md
- 作为跨 Agent 的项目级权威入口文件

AGENT.md
- 仅作为历史兼容入口，指向 AGENTS.md
- 不再维护独立规则副本

work-items/
- 标记为 legacy / frozen
- 不再创建新的实现任务
- 未来所有导致代码修改的开发事项通过 openspec/changes/ 管理

.claude/ 与 .opencode/
- 本阶段保持原状
- 记录为后续迁移阶段待治理项
```

---

## 4. 严格执行范围

### 4.1 本阶段允许执行的 Git 操作

仅允许在确认原工作区干净之后执行以下 Git 写操作：

1. 创建整改分支与 linked worktree：

```bash
git worktree add -b chore/superspec-governance-migration E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance HEAD
```

2. 在整改 worktree 中查看状态与 diff：

```bash
git status --short --branch
git diff --stat
git diff -- <allowed-path>
```

3. 本阶段完成后，**不得自行 commit 或 push**。向用户回传 diff，由用户决定是否提交。

### 4.2 本阶段允许新增或修改的文件

仅允许在新建的整改 worktree 中修改以下路径：

```text
AGENT.md
AGENTS.md
docs/README.md                         # 仅当其仍引用 AGENT.md 作为权威入口时允许最小修正
docs/rectification/01-superspec-clean-baseline-and-governance-authority-report.md
work-items/README.md                   # 仅在不存在时新增；若已存在则按停止规则处理
```

### 4.3 本阶段禁止修改的范围

严禁修改、移动、删除或格式化以下任意路径：

```text
diagnose_tool/
frontend/
tests/
config/
data/
diagnosis_prompt/
main.py
pyproject.toml
uv.lock
Dockerfile
docker-compose.yml
.github/
openspec/config.yaml
openspec/specs/
openspec/changes/
openspec/schemas/
docs/00-project/
docs/01-architecture/
docs/02-harness/
docs/03-openspec/
docs/04-development/
docs/05-domain/
docs/06-operations/
docs/07-templates/
docs/99-archive/
.claude/
.opencode/
CLAUDE.md
README.md
README_ZH.md
```

严禁执行：

```bash
git commit
git push
git merge
git reset
git restore
git clean
git stash
git checkout -- <path>
git switch <existing-branch>
git worktree remove
openspec init
openspec schema init
openspec schema fork
openspec schema validate
任何 /opsx:* 或 opsx-* lifecycle 命令
```

---

## 5. 启动前验证与停止条件

### Step 1：在原工作区验证用户已提交基线

在原路径执行：

```bash
cd E:/009workspace/claudecode/DiagnoseToolPy
git branch --show-current
git rev-parse HEAD
git status --short --branch
git worktree list
```

将结果记录下来。

### 必须停止的条件

若 `git status --short --branch` 除分支标识行外仍显示任意 modified、deleted、renamed 或 untracked 文件，立即停止执行，并回传：

```text
STOPPED: Original workspace is not clean after the user's baseline commit.
No rectification worktree has been created.
```

不得代替用户提交、删除、stash 或清理文件。

### 允许继续的条件

仅当原工作区无任何待提交或未跟踪文件时，继续下一步。

---

## 6. 创建独立整改 Worktree

### Step 2：检查目标分支与目录不存在

在原工作区执行只读检查：

```bash
git branch --list chore/superspec-governance-migration
git worktree list
```

同时检查路径是否已存在：

```powershell
Test-Path E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance
```

### 必须停止的条件

出现以下任一情况时停止，不得覆盖、重置或复用：

- 分支 `chore/superspec-governance-migration` 已存在；
- 目标 worktree 路径已存在；
- `git worktree list` 已包含相同用途的整改工作区。

回传：

```text
STOPPED: Governance migration branch or target worktree path already exists.
Manual decision is required; no overwrite/reset was performed.
```

### Step 3：创建 worktree

条件满足后执行：

```bash
git worktree add -b chore/superspec-governance-migration E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance HEAD
```

进入新 worktree：

```bash
cd E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance
git branch --show-current
git rev-parse HEAD
git status --short --branch
```

验证：

- 当前分支必须为 `chore/superspec-governance-migration`；
- 当前 HEAD 必须等于原工作区在 Step 1 记录的 HEAD；
- 新 worktree 必须为 clean。

若任一不符合，立即停止，不做文件修改。

---

## 7. 权威入口收敛：`AGENTS.md` / `AGENT.md`

### 7.1 治理决策

本项目今后的项目级 Agent 规则权威入口应为：

```text
AGENTS.md
```

原因：

- `AGENTS.md` 可作为跨 Codex / OpenCode 等 Agent 的通用入口；
- Claude 专属执行补充可继续留在 `CLAUDE.md`，但不得覆盖项目级硬约束；
- 当前 `AGENT.md` 与 `AGENTS.md` 内容基本重复，继续双维护会产生规则漂移风险。

### 7.2 修改前必须核验内容是否等价

在整改 worktree 内对以下文件进行读取与对比：

```text
AGENT.md
AGENTS.md
docs/README.md
```

检查：

1. `AGENT.md` 是否包含 `AGENTS.md` 中不存在的硬约束；
2. `AGENTS.md` 是否包含 `AGENT.md` 中不存在的硬约束；
3. `docs/README.md` 是否将 `AGENT.md` 声明为权威入口，或同时要求读取两者；
4. 是否存在其他治理文档明确要求保持两份独立规则文件。

### 停止条件：存在非等价规则

若发现 `AGENT.md` 与 `AGENTS.md` 存在实质性规则差异，**不得合并或删改任一文件**。仅创建报告文件，记录：

- 差异章节；
- 可能丢失的规则；
- 建议的后续人工决策。

此时本阶段状态应为：

```text
PARTIAL: Clean worktree created, but authority consolidation blocked by non-equivalent AGENT/AGENTS rules.
```

### 7.3 内容等价时的允许修改

仅当确认两份文件的硬规则等价时，执行以下收敛：

#### A. 保留 `AGENTS.md` 为完整权威规则文件

不得在本阶段大规模压缩、重写或重新组织 `AGENTS.md`。仅允许在其开头增加一段短声明（若不存在同类声明）：

```markdown
> **Authority Notice**
>
> This file is the canonical project-level instruction entry for AI development agents.
> Tool-specific instructions may exist in `CLAUDE.md`, `.claude/`, or `.opencode/`, but they must not override the non-negotiable project constraints and change-governance rules defined here.
```

若文件为中文为主，可使用对应中文声明：

```markdown
> **权威入口说明**
>
> 本文件是 AI 开发代理使用的项目级权威约束入口。`CLAUDE.md`、`.claude/` 或 `.opencode/` 可提供工具专用执行说明，但不得覆盖本文件定义的不可违背项目约束与变更治理规则。
```

保持文件原有语言风格，不得同时加入中英文重复说明。

#### B. 将 `AGENT.md` 替换为兼容入口文件

在确认规则已经完整保留于 `AGENTS.md` 后，将 `AGENT.md` 内容替换为以下短文；不得保留一份完整规则副本：

```markdown
# Compatibility Entry for AI Agents

This file is retained only for compatibility with tooling or historical references that look for `AGENT.md`.

The canonical project-level AI development rules are maintained in:

- [`AGENTS.md`](./AGENTS.md)
- [`docs/README.md`](./docs/README.md) for task-specific context routing

Before analyzing, designing, implementing, or reviewing changes in this repository, read `AGENTS.md` first. Do not treat this compatibility file as an independent rule source.
```

若现有文件以中文为主，改用：

```markdown
# AI Agent 兼容入口

本文件仅为兼容仍会查找 `AGENT.md` 的工具或历史引用而保留。

项目级 AI 开发规则的权威来源为：

- [`AGENTS.md`](./AGENTS.md)
- [`docs/README.md`](./docs/README.md)，用于按任务类型路由上下文

在本仓库进行需求分析、设计、实现或审查前，必须首先读取 `AGENTS.md`。本文件不得作为独立规则来源维护。
```

#### C. 最小修正 `docs/README.md`

仅当 `docs/README.md` 仍要求优先读取 `AGENT.md`，或将 `AGENT.md` 与 `AGENTS.md` 都视为独立规则源时，允许将其入口引用最小修改为：

```text
AGENTS.md：项目级权威 AI 开发约束入口
AGENT.md：仅兼容旧工具或历史引用，不承载独立规则
CLAUDE.md：Claude Code 专用补充，不得覆盖 AGENTS.md
```

不得在本阶段重写其文档路由策略或其他内容。

---

## 8. 冻结 `work-items/` 的任务真相源地位

### 8.1 治理决策

后续所有会修改代码、规范或项目治理资产的开发事项，应通过：

```text
openspec/changes/<change-name>/
```

管理。

`work-items/` 中已有资产保留为历史/遗留协作记录，不在本阶段移动或删除，但不得继续新增新的活跃实现任务。

### 8.2 检查步骤

在整改 worktree 中检查：

```text
work-items/
work-items/README.md
```

### 停止/分支规则

- 若 `work-items/README.md` 已存在且已明确声明该目录 frozen / legacy / 不再创建新任务，则不修改该文件，仅在报告中记录已有策略。
- 若 `work-items/README.md` 已存在但仍将该目录声明为活动任务入口，不得覆盖；在报告中标记为 `HIGH` 冲突，等待后续决策。
- 若 `work-items/README.md` 不存在，则允许新增该文件。

### 8.3 允许新增的 `work-items/README.md` 内容

```markdown
# Legacy Work Items

This directory contains historical task records created before the SuperSpec governance migration.

## Status

- This directory is **frozen** for new implementation work.
- Existing records are retained for historical traceability only.
- Do not create new active tasks, change plans, or implementation tracking records here.

## Current Source of Truth for Changes

Any future work that modifies code, specifications, architecture governance, or project behavior must be managed through:

```text
openspec/changes/<change-name>/
```

The active OpenSpec schema determines the required artifacts for each change.

## Migration Note

Existing records in this directory may be archived or indexed in a later governance phase. They must not be rewritten or deleted during Phase 0A.
```

若本目录既有文档主要为中文，可使用中文版本：

```markdown
# 历史任务记录（Legacy Work Items）

本目录保存 SuperSpec 治理迁移之前形成的历史任务记录。

## 当前状态

- 本目录已**冻结**，不再用于创建新的实现任务。
- 既有记录仅用于历史追踪。
- 不得在此新增活跃任务、变更计划或实现状态记录。

## 后续变更的唯一治理路径

今后任何会修改代码、规格、架构治理资产或系统行为的工作，必须通过以下路径管理：

```text
openspec/changes/<change-name>/
```

每个 change 需要生成哪些 artifact，由当前启用的 OpenSpec schema 决定。

## 迁移说明

本目录中的既有记录可在后续治理阶段进行归档或索引，但 Phase 0A 不得重写或删除这些历史记录。
```

---

## 9. 本阶段整改报告

必须在整改 worktree 中新增：

```text
docs/rectification/01-superspec-clean-baseline-and-governance-authority-report.md
```

报告至少包含以下内容：

```markdown
# DiagnoseToolPy SuperSpec Phase 0A 执行报告

## 1. 执行摘要
- 执行日期
- 原工作区路径、分支、基线 HEAD
- 新 worktree 路径、分支、HEAD
- 执行结果：PASS / PARTIAL / STOPPED

## 2. 基线清洁性验证
- 原工作区执行前 `git status --short --branch` 输出
- 是否满足 clean precondition
- 新 worktree 创建后的状态

## 3. Worktree 与分支创建记录
- 执行命令
- 分支名称
- worktree 路径
- 是否与基线 HEAD 一致

## 4. AGENT/AGENTS 权威入口核验
- 两文件是否等价
- 比对发现
- 是否实施 canonicalization
- 实际修改文件

## 5. work-items 冻结核验
- 是否已有 README
- 是否新增冻结声明
- 是否发现活动任务语义冲突

## 6. 本阶段明确保留但未处理的问题
- `.claude/` / `.opencode/` 重复流程资产
- `.claude/settings.local.json` 权限范围
- `openspec/config.yaml` 尚未切换 SuperSpec
- `openspec/schemas/superspec/` 尚未引入

## 7. 文件变更清单
- 新增文件
- 修改文件
- 未修改的保护路径确认

## 8. Git Diff 与验证结果
- `git status --short --branch`
- `git diff --stat`
- `git diff --name-only`

## 9. Phase 1 准入建议
- 是否建议进入 `superspec` schema 引入阶段
- 剩余 BLOCKER / HIGH 项
- Phase 1 推荐允许修改范围
```

---

## 10. 本阶段验证命令

完成允许的文件修改后，在**整改 worktree** 执行：

```bash
git branch --show-current
git rev-parse HEAD
git status --short --branch
git diff --stat
git diff --name-only
git diff -- AGENT.md AGENTS.md docs/README.md work-items/README.md docs/rectification/01-superspec-clean-baseline-and-governance-authority-report.md
```

### 必须确认

`git diff --name-only` 中只允许出现：

```text
AGENT.md
AGENTS.md
docs/README.md
docs/rectification/01-superspec-clean-baseline-and-governance-authority-report.md
work-items/README.md
```

其中 `docs/README.md`、`AGENT.md`、`AGENTS.md`、`work-items/README.md` 是否出现取决于前述核验结果。

若出现任意禁止路径变更，立即停止，不得自行恢复或清理；向用户报告越界文件列表和原因。

---

## 11. Codex 必须回传的结果

执行完成后，请向用户完整回传：

1. `docs/rectification/01-superspec-clean-baseline-and-governance-authority-report.md` 的文件内容或文件本身；
2. 原工作区的基线分支和基线 HEAD；
3. 新整改 worktree 路径、分支和 HEAD；
4. `AGENT.md` 与 `AGENTS.md` 是否等价以及最终处理结果；
5. `work-items/README.md` 的处理结果；
6. `git status --short --branch` 输出；
7. `git diff --stat` 输出；
8. `git diff --name-only` 输出；
9. 是否建议进入 Phase 1：SuperSpec schema 引入；
10. 执行期间未修改业务代码、未修改 OpenSpec schema/config、未修改工具专用资产、未 commit/push 的明确确认。

---

## 12. 失败处理规则

| 情况 | 必须采取的动作 |
|---|---|
| 原工作区仍不干净 | 停止；不得替用户提交、stash 或清理 |
| 目标 branch 或 worktree 已存在 | 停止；不得用 `-B`、`--force` 或删除已有目录 |
| 新 worktree HEAD 与原基线 HEAD 不一致 | 停止；不得继续写文件 |
| `AGENT.md` 与 `AGENTS.md` 存在非等价硬规则 | 不做入口合并；只记录报告 |
| `work-items/README.md` 声明仍为 active source of truth | 不覆盖；只记录冲突 |
| 发现必须修改禁止路径才能完成任务 | 停止；记录需要扩大范围的理由 |
| 误修改禁止路径 | 立即停止并回传文件清单；不得自行 reset/restore/clean |
| Codex 判断本指令与仓库事实冲突 | 以仓库事实为准停止执行，详细回传冲突，不得推断性扩展修改 |

---

## 13. 本阶段不包含的后续工作

以下工作全部明确延期，Codex 不得在本阶段顺便执行：

```text
- 复制或安装 danielhanold/superspec schema
- 修改 openspec/config.yaml 为 schema: superspec
- 配置 artifact rules 或 context
- 重组 docs/03-openspec/
- 移动历史 work-items 目录
- 修改 .claude/ 或 .opencode/ commands / skills
- 收紧 .claude/settings.local.json 权限
- 创建真实业务 change
- 开发大模型诊断模块
- 提交、推送或创建 PR
```

---

## 14. 后续阶段预告

仅当本阶段报告结论为 `PASS` 且用户确认 diff 合理后，下一份执行任务书才会进入：

```text
Phase 1：引入并验证 danielhanold/superspec 项目级 schema 基础设施
```

Phase 1 预计只允许操作：

```text
openspec/schemas/superspec/
openspec/config.yaml
docs/rectification/
```

并要求先验证 OpenSpec CLI 版本与 schema validation 能力，再决定是否切换默认 schema。
