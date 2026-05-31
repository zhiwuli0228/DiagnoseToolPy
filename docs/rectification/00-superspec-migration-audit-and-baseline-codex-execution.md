# DiagnoseToolPy 全面适配 SuperSpec：Phase 0 迁移审计与基线固化执行任务书

> **交付对象**：Codex 执行端  
> **项目**：`DiagnoseToolPy`  
> **目标工作流**：`danielhanold/superspec`（OpenSpec Custom Schema + Superpowers）  
> **文档版本**：v1.0  
> **编制日期**：2026-05-31  
> **阶段性质**：Bootstrap Audit / Read-Only Investigation + Single Audit Report Output

---

## 0. Codex 执行指令摘要

你正在执行 `DiagnoseToolPy` 项目全面适配 `danielhanold/superspec` 之前的 **Phase 0：迁移审计与基线固化**。

本阶段不是安装阶段、不是迁移阶段、不是业务开发阶段，也不是目录重构阶段。你的任务是基于**本地真实仓库状态**完成资产审计，并只新增一份审计报告，为后续 SuperSpec 引入和资产治理提供可验证的基线。

### 本阶段只允许产生的仓库修改

仅允许新增以下文件；如果目录不存在，可以创建该目录：

```text
docs/rectification/00-superspec-migration-audit-report.md
```

### 本阶段禁止动作

严禁执行以下行为：

- 不修改任何现有文件，包括 `AGENT.md`、`AGENTS.md`、`CLAUDE.md`、`docs/README.md`、`openspec/config.yaml`。
- 不修改 `diagnose_tool/`、`frontend/`、`tests/`、`config/`、`data/` 中的任何文件。
- 不新增、删除、移动或重命名任何现有资产目录。
- 不复制或安装 `openspec/schemas/superspec/`。
- 不将 `openspec/config.yaml` 切换为 `schema: superspec`。
- 不安装或升级 OpenSpec、Superpowers、Claude Code、Codex、OpenCode 相关能力。
- 不创建 OpenSpec change，不运行 `/opsx:new`、`/opsx:continue`、`/opsx:apply`、`/opsx:verify`、`/opsx:archive`。
- 不运行会改写工作区、分支、索引或远端状态的 Git 操作，包括 `git add`、`git commit`、`git checkout`、`git switch`、`git restore`、`git reset`、`git clean`、`git merge`、`git rebase`、`git pull`、`git push`。
- 不自动修复本审计过程中发现的问题。

### 执行原则

1. **本地仓库为事实源**：本任务书中的“公开仓库快照发现”仅用于提示核验重点；如果本地代码与远程 `main` 不一致，以本地实际状态为准，并在报告中记录差异。
2. **只记录，不修复**：发现错误、重复资产、过时规则或未提交修改时，只写入报告，不进行整改。
3. **证据优先**：每项结论应给出文件路径、相关标题/关键配置或只读命令结果作为依据。
4. **不扩大范围**：本阶段不得借机整理格式、更新 README、优化代码或生成新的流程资产。

---

## 1. 背景与后续目标

### 1.1 当前整改目标

项目后续将全面适配 **`danielhanold/superspec`**。该项目不是独立替代 OpenSpec 的 CLI，而是一个 OpenSpec custom schema：

- OpenSpec 继续负责 versioned proposal、delta specs、tasks、verify 与 archive；
- Superpowers 负责 brainstorming、plan-writing、worktree 隔离、subagent-driven TDD 与 code review；
- SuperSpec schema 将二者组织为一条可审计的变更流水线。

SuperSpec v4 的标准 change 产物链路为：

```text
brainstorm.md
→ proposal.md
→ design.md（可选）
→ specs/*/spec.md
→ tasks.md
→ plan.md
→ apply.md
→ verify.md
→ finalize.md
→ archive
```

其 `apply` 和 `finalize` 阶段可能触发 worktree、分支合并、push 和 PR 辅助动作。因此，在安装或启用该 schema 之前，必须先确认当前项目的资产来源、Git 使用方式、工具专用规则以及已有 OpenSpec 状态，避免迁移后产生错误执行或多套真相源。

### 1.2 本阶段为什么不能直接迁移

当前公开仓库快照已经显示项目存在以下需要本地确认的潜在风险：

- 根目录同时存在 `AGENT.md` 与 `AGENTS.md`，且 AI 规则文件内部可能引用了不同名称；
- 根目录存在 `.claude/` 与 `.opencode/`，意味着已有多工具指令资产；
- `openspec/config.yaml` 的公开快照仍以 `schema: spec-driven` 开始，尚未承接 SuperSpec；
- `docs/` 已经承担项目级 harness context hub 职责；
- `work-items/` 与 `openspec/` 同时存在，可能构成并行任务来源；
- 业务代码同时包含 Python 后端与 React/TypeScript 前端，迁移治理不得误触业务实现。

以上均为**核验假设**，不得直接当作本地事实；必须在报告中逐项确认、否定或补充。

---

## 2. 执行输入与事实来源

### 2.1 必须审计的本地仓库

在你接收到本任务书后，进入用户提供的 `DiagnoseToolPy` 本地 Git 仓库根目录执行审计。不要假设本地路径固定；先通过 Git 命令确认当前目录是否位于目标仓库。

若当前目录不是该项目根目录，停止修改操作，并向用户说明需要在本地 `DiagnoseToolPy` 仓库根目录重新执行本任务书。

### 2.2 公开远程快照：仅作为核验参考

审计开始前已知的公开 GitHub `main` 快照包含以下顶层项目：

```text
.claude/
.github/workflows/
.opencode/
config/
data/
diagnose_tool/
docs/
frontend/
openspec/
tests/
work-items/
AGENT.md
AGENTS.md
CLAUDE.md
README.md
pyproject.toml
uv.lock
```

公开快照还表明：

- `README.md` 将项目描述为面向稳定性工作的轻量 Web 诊断助手；
- `openspec/config.yaml` 当前起始配置为 `schema: spec-driven`；
- `docs/README.md` 规定了按任务类型读取文档的策略与若干硬规则；
- `AGENTS.md` 中包含项目目标、硬约束、模块边界、OpenSpec 工作方式和测试要求。

你的报告必须明确说明：本地是否与上述公开快照一致；不一致时列明差异，但不得尝试同步、拉取或修复。

### 2.3 SuperSpec 目标基线：仅用于兼容性差距分析

后续迁移目标的官方仓库信息如下，审计报告可以引用这些目标来识别差距，但本阶段不得实施安装：

- SuperSpec 为 `danielhanold/superspec`，当前 README 标记为 Schema version 4；
- 官方项目布局要求把 schema 放在 `openspec/schemas/superspec/`；
- 启用后的项目配置会将 `openspec/config.yaml` 设置为 `schema: superspec`；
- schema artifacts 包含 `brainstorm`、`proposal`、可选 `design`、`specs`、`tasks`、`plan`、`apply`、`verify`、`finalize`；
- `apply` 依赖 worktree 与 Superpowers 执行能力，`finalize` 包含 Git closeout 行为。

---

## 3. 本阶段交付目标

本阶段必须完成以下交付：

```text
docs/rectification/00-superspec-migration-audit-report.md
```

该报告应解决以下问题：

1. 当前本地仓库真实目录与 Git 状态是什么？
2. 当前项目有哪些长期资产、单次变更资产、执行工具资产、历史/遗留资产和可能的生成型资产？
3. 当前哪些文件正在承担 AI 约束、OpenSpec 规则或任务来源职责？
4. 是否存在文件命名、职责重叠、相互引用错误或规则冲突？
5. 现有 OpenSpec 目录和配置是否可安全迁移到 SuperSpec？
6. `.claude/`、`.opencode/`、`CLAUDE.md` 与未来 Codex/Claude Code/OpenCode 使用方式之间可能有哪些冲突？
7. `work-items/` 是否正在与 `openspec/changes/` 形成双重 source of truth？
8. 是否存在需要在迁移前保护的业务代码、规范资产或未提交工作？
9. 后续 Phase 1 能否进入 SuperSpec schema 引入阶段？如不能，阻塞项是什么？

---

## 4. 审计范围与分类规则

### 4.1 必查目录与文件

必须读取并审计以下路径；路径不存在时也要在报告中记录为“不存在”：

```text
.git/
.gitignore
.github/
.claude/
.opencode/
AGENT.md
AGENTS.md
CLAUDE.md
README.md
pyproject.toml
uv.lock
config/
data/
diagnose_tool/
frontend/
tests/
docs/
docs/README.md
docs/00-project/
docs/01-architecture/
docs/02-harness/
docs/03-openspec/
docs/04-development/
docs/05-domain/
docs/06-operations/
docs/07-templates/
docs/99-archive/
openspec/
openspec/config.yaml
openspec/specs/
openspec/changes/
openspec/schemas/
work-items/
```

### 4.2 资产分类

将扫描发现的所有治理相关资产按下表分类：

| 分类 | 定义 | 典型目标位置 | 本阶段需要判断的问题 |
|---|---|---|---|
| A. 入口约束资产 | 所有 Agent 每次工作前必须遵守或读取的最短规则 | `AGENTS.md`、工具入口文件 | 是否重复、命名混乱、过长或冲突 |
| B. 长期项目知识资产 | 反映项目目标、架构、领域和开发标准的稳定知识 | `docs/` | 是否职责清晰、是否存在 change 流水账污染 |
| C. Living Specs | 当前系统已承诺的可验证行为合同 | `openspec/specs/` | 是否存在、是否与代码/文档边界合理 |
| D. Change 资产 | 单次需求的 proposal/design/spec/tasks/验证过程 | `openspec/changes/` | 是否存在未完成或与 `work-items` 重叠的 change |
| E. Schema / 流程模板资产 | 定义 OpenSpec artifact DAG 与模板的内容 | `openspec/schemas/`、`openspec/config.yaml` | 是否已存在自定义 schema，迁移是否冲突 |
| F. 工具专用资产 | Claude、Codex、OpenCode 等实现工具读取的指令、skill、command | `.claude/`、`.opencode/`、`CLAUDE.md` | 是否包含旧流程命令或互相冲突的规则 |
| G. Legacy / 临时任务资产 | 未纳入 OpenSpec lifecycle 的任务或历史材料 | `work-items/`、旧目录 | 是否仍作为活跃任务源使用 |
| H. 自动生成 / 非权威资产 | CodeWiki、自动图谱、生成式模块解读等辅助资料 | 可能的 `docs/generated/` 或其他位置 | 是否存在、是否被误当作规则来源 |
| I. 业务实现资产 | 实际代码、测试、配置、运行数据 | `diagnose_tool/`、`frontend/`、`tests/` 等 | 本阶段仅登记保护范围，不分析业务正确性 |

### 4.3 Source of Truth 判定规则

在报告中必须尝试确认以下问题：

| 事项 | 当前实际 source of truth | 是否唯一 | 冲突资产 | 后续建议 |
|---|---|---:|---|---|
| AI 通用硬约束 | 待审计 | 待审计 | 待审计 | 待审计 |
| Claude Code 专用执行说明 | 待审计 | 待审计 | 待审计 | 待审计 |
| OpenCode 专用执行说明 | 待审计 | 待审计 | 待审计 | 待审计 |
| 项目架构边界 | 待审计 | 待审计 | 待审计 | 待审计 |
| 当前系统行为合同 | 待审计 | 待审计 | 待审计 | 待审计 |
| 变更任务状态 | 待审计 | 待审计 | 待审计 | 待审计 |
| OpenSpec schema 和 artifact 规则 | 待审计 | 待审计 | 待审计 | 待审计 |
| 自动生成代码理解文档 | 待审计 | 待审计 | 待审计 | 待审计 |

注意：报告中不得仅写“应当如何”。必须先描述“当前真实状态是什么”，再给出后续迁移建议。

---

## 5. 只读执行步骤

## Step 1：确认仓库身份与 Git 安全基线

### 目标

确认正在审计正确仓库，并记录迁移前不可破坏的 Git 状态。

### 允许执行的只读命令

在仓库根目录使用等价的只读命令，建议执行：

```bash
git rev-parse --show-toplevel
git rev-parse --is-inside-work-tree
git branch --show-current
git rev-parse HEAD
git status --short --branch
git remote -v
git log -1 --oneline --decorate
```

如当前环境为 PowerShell，也可直接运行以上 Git 命令。

### 必须记录到报告的内容

- 仓库根目录绝对路径；
- 当前分支；
- 当前 HEAD commit；
- remote 列表；
- 工作区是否已有未提交变更；
- 若存在未提交变更，列出文件但不得修改、暂存或清理；
- 是否存在 worktree：可执行 `git worktree list` 读取状态；
- 是否已存在与 OpenSpec/SuperSpec 相关的 feature branch，仅记录即可。

### 阻断规则

- 若不是 Git 仓库：不得创建报告文件，直接向用户报告无法执行。
- 若仓库明显不是 `DiagnoseToolPy`：不得创建报告文件，直接向用户报告路径错误。
- 若工作区存在未提交变更：**不阻断审计**，但报告必须把它列为后续整改保护项。

---

## Step 2：生成顶层与治理资产目录清单

### 目标

确认本地实际资产布局，而不是沿用远端快照假设。

### 读取方式

使用只读命令列出目录结构。可选择以下方式之一：

```bash
git ls-files
```

或：

```bash
find . -maxdepth 4 -type f | sort
```

在 Windows 环境也可以使用 Python 或 PowerShell 的只读枚举命令。不要安装 `tree` 等新工具。

### 范围控制

- `data/` 若包含大量运行数据，只列出目录层级与是否有 tracked 文件，不读取大文件内容。
- `node_modules/`、`.venv/`、缓存、构建输出目录若存在，仅记录，不遍历其全部文件。
- 不读取日志样本、压缩包或大体量运行数据内容。

### 必须写入报告

输出一份“治理相关目录概览”，至少展示：

```text
根级 Agent / 工具规则文件
.claude/ 与 .opencode/ 资产概览
docs/ 两到三级目录概览
openspec/ 两到三级目录概览
work-items/ 两到三级目录概览
业务模块一级目录概览
```

---

## Step 3：审计 Agent 入口资产与工具专用资产

### 必查文件

```text
AGENT.md
AGENTS.md
CLAUDE.md
.claude/**
.opencode/**
```

### 核验内容

1. `AGENT.md` 与 `AGENTS.md` 是否同时存在。
2. 二者是否内容重复、相互冲突、标题与文件名不一致或被其他文档错误引用。
3. 哪个文件被 `CLAUDE.md`、`.claude/`、`.opencode/`、`docs/README.md` 或 `openspec/config.yaml` 引用。
4. `.claude/` 下是否存在 skills、commands、settings、memory 或其他与 OpenSpec / Superpowers / Git 操作相关内容。
5. `.opencode/` 下是否存在 agents、commands、skills、rules 或其他旧 OpenSpec 工作流指令。
6. 当前是否已有 Codex 专用资产；若无，只记录“不存在”，不要创建。
7. 是否存在以下高风险规则：
   - 自动提交、自动 push、自动创建 PR；
   - 自动 archive 或自动 apply；
   - 绕过人工审核；
   - 允许无范围限制地重构；
   - 与未来 SuperSpec worktree/finalize 重复的 Git 操作。

### 报告输出格式

在报告中建立表格：

| 文件/目录 | 当前职责摘要 | 被谁引用 | 是否权威候选 | 冲突/风险 | Phase 1/2 建议 |
|---|---|---|---:|---|---|

### 特别检查：文件命名异常

公开快照显示 `AGENTS.md` 的文本开头可能写为 `# AGENT.md`，并且其读取顺序可能要求读取 `AGENT.md`。请在本地确认：

- 是否真实存在该命名/内容不一致；
- `AGENT.md` 和 `AGENTS.md` 各自到底承载何种内容；
- 哪一个应当在后续整改中成为统一入口文件。

本阶段只给出建议，不重命名、不合并、不删除文件。

---

## Step 4：审计 `docs/` 长期项目资产

### 必查内容

```text
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
```

### 核验目标

对每个一级目录回答：

- 当前实际包含哪些文件；
- 目录职责是否与 `docs/README.md` 宣称的一致；
- 是否存在过时、重复、空文件或位置明显不合理的资产；
- 是否含有应进入 OpenSpec schema/config 的 artifact 规则；
- 是否含有单次 change 的过程内容，导致长期文档污染；
- 是否出现生成型文档、CodeWiki 导出、AI 自动摘要或类似资产；
- 是否存在敏感信息、运行数据或不应长期提交的内容迹象。

### 必查潜在规则问题

公开快照中的 `docs/README.md` 可能要求“每个完成的 change 都更新 `docs/00-project/current-state.md`”。请核验该规则是否存在，并在报告中判断：

- 它是否导致普通 bugfix 也必须修改长期状态资产；
- 是否应在后续整改中收缩为“仅当能力、架构、运行方式或长期约束变化时更新”；
- 是否存在其他同类过度更新规则。

### 报告输出格式

| 目录/文件 | 声明职责 | 实际内容摘要 | 资产层级判断 | 问题等级 | 后续动作建议 |
|---|---|---|---|---|---|

问题等级只允许使用：

```text
BLOCKER / HIGH / MEDIUM / LOW / NONE
```

---

## Step 5：审计 OpenSpec 当前状态与 SuperSpec 迁移差距

### 必查内容

```text
openspec/config.yaml
openspec/specs/**
openspec/changes/**
openspec/schemas/**
```

### 核验内容

#### 5.1 `openspec/config.yaml`

记录：

- 当前默认 schema；
- 是否已有 `context`；
- 是否已有 per-artifact `rules`；
- 是否引用了项目级文档；
- 是否包含失效路径；
- 是否已经包含 SuperSpec 相关配置。

#### 5.2 Living Specs

记录：

- `openspec/specs/` 下当前 capability 列表；
- capability 是否与项目已有功能相符；
- 是否存在明显空缺、重复或命名问题；
- 不做内容修订，不进行 behavior/code 一致性深度验证；仅评估迁移保护范围。

#### 5.3 Active / Archived Changes

记录：

- `openspec/changes/` 是否存在；
- 当前 active changes 与 archived changes 的列表；
- active change 是否仍未完成；
- change artifacts 当前采用哪些文件结构；
- 是否已有文件名与未来 SuperSpec artifacts 重叠或冲突。

#### 5.4 Custom Schemas

记录：

- `openspec/schemas/` 是否存在；
- 是否已经放入自定义 schema；
- 是否已经存在名为 `superspec` 的 schema；
- 若存在，不得覆盖，必须记录其来源、版本线索与潜在冲突。

### 与目标 SuperSpec 的差距矩阵

在报告中完成以下表格：

| SuperSpec 目标要求 | 当前本地状态 | 差距/冲突 | 风险等级 | Phase 1 是否可直接处理 |
|---|---|---|---|---:|
| `openspec/schemas/superspec/schema.yaml` | 待核验 | 待核验 | 待核验 | 待判断 |
| `openspec/schemas/superspec/templates/*` | 待核验 | 待核验 | 待核验 | 待判断 |
| `openspec/config.yaml` 可切换 `schema: superspec` | 待核验 | 待核验 | 待核验 | 待判断 |
| 现有 active changes 可被保护 | 待核验 | 待核验 | 待核验 | 待判断 |
| Agent 工具具备未来执行前提 | 待核验 | 待核验 | 待核验 | 待判断 |
| Git/worktree 策略无阻塞冲突 | 待核验 | 待核验 | 待核验 | 待判断 |

### 注意

本阶段**不要**执行 OpenSpec 校验或工具命令，除非你可以确认该命令是只读、工具已经存在且不会生成或更新配置文件。若不确定，报告中将“工具可运行性验证”列为 Phase 1 的前置动作，不要冒险执行。

---

## Step 6：审计 `work-items/` 与任务真相源冲突

### 必查内容

```text
work-items/**
openspec/changes/**
```

### 核验问题

1. `work-items/` 是否存在活跃开发任务，或仅为历史记录。
2. 每个 work item 是否对应已存在的 OpenSpec change、Git commit、已完成代码或未知状态。
3. 是否存在同一需求在两套目录中分别描述、但状态不同的情况。
4. `work-items/` 中是否包含后续仍应保留的验收记录、review 记录或缺陷复盘。
5. 后续是否可以将其标记为 legacy，并停止新增内容。

### 报告输出格式

| Work item | 当前内容类型 | 是否仍活跃 | 对应 OpenSpec change | 迁移/归档建议 | 风险 |
|---|---|---:|---|---|---|

### 迁移判定规则

报告中应给出建议，但不得实际移动文件：

- 若 `work-items/` 仅为历史信息：建议 Phase 4 归档到 `docs/99-archive/legacy-work-items/`。
- 若存在未完成工作：建议在迁移前明确继续用旧方式完成，还是建立新的 SuperSpec change 接管；不得由 Codex 本阶段擅自决定。
- 若与 active OpenSpec changes 重复：标为 `HIGH` 或 `BLOCKER`。

---

## Step 7：登记业务实现保护范围

### 目标

本阶段不审核代码逻辑，仅确保后续治理迁移不会误改业务实现。

### 必须登记的路径

```text
diagnose_tool/
frontend/
tests/
config/
data/
main.py
pyproject.toml
uv.lock
Dockerfile
docker-compose.yml
.github/workflows/
```

### 报告要求

对每个路径只写：

- 是否存在；
- 大致职责；
- 是否 tracked；
- 是否当前已有未提交变动；
- Phase 0 是否保护为禁止修改路径；
- 后续 Phase 1/2 是否原则上仍不应修改。

不要阅读大量业务源码，不要运行业务测试，不要启动前后端服务。

---

## Step 8：产出 Phase 1 准入结论

报告必须在结尾作出以下二选一结论：

### 结论 A：允许进入 Phase 1 — SuperSpec Schema 基础设施引入

只有在以下条件满足时选择：

- 本阶段仅新增审计报告，未误改现有文件；
- 没有无法解释的 active change / task 真相源冲突；
- 没有现存 `openspec/schemas/superspec/` 冲突资产；
- Git 状态中的未提交变更不会被 Phase 1 修改覆盖；
- 已明确后续哪些文件允许在 Phase 1 修改，哪些必须继续保护。

### 结论 B：暂缓进入 Phase 1 — 需先解决阻塞项

如果出现以下任一情况，应选择此结论：

- 项目已经有一套来源不明的 SuperSpec schema；
- 存在多个 active 任务体系且无法判断当前真实执行状态；
- 当前工作区有与迁移目标文件重叠的未提交修改；
- Agent 规则之间存在会导致迁移误操作的高风险冲突；
- 本地目录与预期仓库不符或关键治理资产缺失严重。

无论采用哪种结论，必须列出后续下一份执行文档应处理的边界。

---

## 6. 审计报告文件模板

请严格按以下结构编写：

```markdown
# DiagnoseToolPy SuperSpec 迁移审计与基线报告

> 执行阶段：Phase 0  
> 执行工具：Codex  
> 执行日期：YYYY-MM-DD  
> 本地仓库路径：...  
> 当前分支：...  
> HEAD Commit：...  
> 审计性质：只读审计，仅新增本报告文件

## 1. 执行摘要

- 审计结论：允许进入 Phase 1 / 暂缓进入 Phase 1
- BLOCKER 数量：
- HIGH 数量：
- 是否发现本阶段范围外修改：
- 是否存在未提交工作需要保护：

## 2. 审计边界与实际执行动作

### 2.1 本次读取范围

### 2.2 本次新增文件

### 2.3 未执行动作确认

确认未执行：schema 安装、配置切换、业务代码修改、Git 写操作、OpenSpec lifecycle 命令。

## 3. Git 与仓库身份基线

| 项目 | 结果 | 证据/说明 |
|---|---|---|
| 仓库根目录 | | |
| 当前分支 | | |
| HEAD Commit | | |
| Remote | | |
| 工作区状态 | | |
| Existing worktrees | | |

## 4. 当前目录与资产概览

### 4.1 顶层目录概览

### 4.2 治理资产目录概览

### 4.3 公开远程快照与本地差异

| 路径/事项 | 公开 main 快照观察 | 本地结果 | 差异影响 |
|---|---|---|---|

## 5. Agent 与工具专用资产审计

| 文件/目录 | 当前职责摘要 | 被谁引用 | 是否权威候选 | 冲突/风险 | 后续建议 |
|---|---|---|---:|---|---|

### 5.1 `AGENT.md` 与 `AGENTS.md` 命名/职责结论

### 5.2 Claude / OpenCode / Codex 资产结论

### 5.3 Git 自动化与 SuperSpec finalize 冲突风险

## 6. `docs/` 长期资产审计

| 目录/文件 | 声明职责 | 实际内容摘要 | 资产层级判断 | 问题等级 | 后续建议 |
|---|---|---|---|---|---|

### 6.1 长期文档与 change 过程资产边界

### 6.2 规则重复与过度更新要求

### 6.3 生成型 / CodeWiki 类资产现状

## 7. OpenSpec 状态与 SuperSpec 迁移差距

### 7.1 当前 `openspec/config.yaml`

### 7.2 Current Living Specs

| Capability | 状态摘要 | 后续迁移保护要求 |
|---|---|---|

### 7.3 Current Changes / Archives

| Change | Active/Archived | Artifact 结构 | 与迁移的关系 |
|---|---|---|---|

### 7.4 Current Schemas

### 7.5 SuperSpec v4 差距矩阵

| SuperSpec 目标要求 | 当前本地状态 | 差距/冲突 | 风险等级 | Phase 1 是否可处理 |
|---|---|---|---|---:|

## 8. `work-items/` 与任务真相源审计

| Work item | 当前内容类型 | 是否仍活跃 | 对应 OpenSpec change | 迁移/归档建议 | 风险 |
|---|---|---:|---|---|---|

### 8.1 Source of Truth 当前判断

| 事项 | 当前实际 source of truth | 是否唯一 | 冲突资产 | 后续建议 |
|---|---|---:|---|---|
| AI 通用硬约束 | | | | |
| 项目架构边界 | | | | |
| 系统行为合同 | | | | |
| 变更任务状态 | | | | |
| OpenSpec schema / artifact rules | | | | |

## 9. 业务实现保护范围登记

| 路径 | 是否存在 | 当前职责 | 是否已有未提交变动 | 后续治理阶段保护结论 |
|---|---:|---|---:|---|

## 10. 问题清单与整改优先级

| ID | 问题 | 证据路径 | 风险等级 | 拟处理阶段 | 本阶段是否已修改 |
|---|---|---|---|---|---:|
| AUD-001 | | | | | 否 |

## 11. Phase 1 准入结论

### 11.1 结论

允许进入 Phase 1 / 暂缓进入 Phase 1。

### 11.2 结论依据

### 11.3 Phase 1 允许修改范围建议

### 11.4 Phase 1 仍需禁止修改范围建议

## 12. Codex 执行回传摘要

- 新增文件：
- 修改现有文件：应为无
- 删除/移动文件：应为无
- 未完成审计项：
- 需要用户或设计端决策的问题：
```

---

## 7. 报告中的问题等级规则

| 等级 | 判定标准 | 示例 |
|---|---|---|
| `BLOCKER` | 不处理就无法安全进入 SuperSpec 基础设施引入 | 已有不明来源 `superspec` schema；迁移目标配置存在未提交冲突；无法判断活跃任务来源 |
| `HIGH` | 可进入后续设计，但必须在正式启用 SuperSpec 前解决 | `AGENT.md` 与 `AGENTS.md` 权威入口冲突；现有 Git 自动化可能与 finalize 冲突；双重任务源 |
| `MEDIUM` | 不阻塞 schema 引入，但应在资产治理阶段整改 | 文档命名不清；长期文档过度更新；旧流程说明需迁移 |
| `LOW` | 可记录并后续顺便清理 | 非关键陈旧表述；格式不统一 |
| `NONE` | 已确认无迁移风险 | 目录职责清晰且无冲突 |

---

## 8. Codex 必须回传给用户的内容

执行完成后，Codex 不应继续进入 Phase 1，而应立即向用户回传：

1. `docs/rectification/00-superspec-migration-audit-report.md` 的完整文件路径；
2. 审计结论：`允许进入 Phase 1` 或 `暂缓进入 Phase 1`；
3. BLOCKER / HIGH 问题摘要；
4. `git diff --stat` 或等价输出，证明只新增了审计报告；
5. `git status --short` 输出，明确本次新增文件与审计前已存在的未提交文件；
6. 未执行的动作确认：未安装 schema、未切换配置、未修改代码、未 commit、未 push；
7. 将审计报告内容交还给用户，由用户转交设计端进行下一阶段评审。

### 回传格式建议

````markdown
## Phase 0 执行回传

- 审计报告：`docs/rectification/00-superspec-migration-audit-report.md`
- 准入结论：允许进入 Phase 1 / 暂缓进入 Phase 1
- BLOCKER：...
- HIGH：...

### 本次文件变更

```text
<git status --short 或 diff --stat 输出>
```

### 明确未执行动作

- [x] 未修改业务代码
- [x] 未修改现有治理资产
- [x] 未安装或启用 SuperSpec schema
- [x] 未执行 OpenSpec lifecycle 命令
- [x] 未进行 git commit / push / merge / reset / clean

### 需要设计端确认的问题

1. ...
````

---

## 9. 执行失败或异常处理规则

| 异常场景 | 处理方式 |
|---|---|
| 当前不在 `DiagnoseToolPy` 仓库根目录 | 停止；不创建文件；报告路径问题 |
| 仓库存在大量未提交修改 | 继续只读审计；在报告中列为保护项；不得清理 |
| `docs/rectification/00-superspec-migration-audit-report.md` 已存在 | 不覆盖；向用户报告冲突并请求设计端决定版本策略 |
| 发现已经安装 SuperSpec schema | 不覆盖、不切换；完整记录其内容和来源线索；视冲突程度判为 BLOCKER/HIGH |
| 发现 OpenSpec 命令不可用 | 记录即可；本阶段不安装、不修复 |
| 发现敏感信息或密钥 | 不在报告中复制值；仅注明文件路径与“疑似敏感信息需治理” |
| 发现业务代码严重问题 | 不修复；仅在报告附加“范围外观察”条目 |
| 发现 CodeWiki 或大规模生成文档 | 只记录其位置、体量与是否被规则引用；不读取全量内容 |

---

## 10. 本阶段完成定义（Definition of Done）

仅当以下全部条件满足时，Phase 0 才视为完成：

- [ ] 已确认本地仓库身份、分支、HEAD、remote 与初始工作区状态。
- [ ] 已扫描并分类 Agent、docs、OpenSpec、work-items 与业务保护资产。
- [ ] 已核验 `AGENT.md` / `AGENTS.md` / `CLAUDE.md` / `.claude/` / `.opencode/` 的职责与风险。
- [ ] 已核验 `openspec/config.yaml`、living specs、changes、schemas 当前状态。
- [ ] 已对照 SuperSpec v4 目标布局输出差距矩阵。
- [ ] 已明确 `work-items/` 与 `openspec/changes/` 是否造成任务真相源冲突。
- [ ] 已列出所有 BLOCKER / HIGH / MEDIUM / LOW 问题与证据路径。
- [ ] 已形成是否准入 Phase 1 的明确结论。
- [ ] 仓库中本阶段只新增 `docs/rectification/00-superspec-migration-audit-report.md`。
- [ ] 未执行安装、迁移、代码修改或 Git 写操作。
- [ ] 已按要求将结果回传用户，等待下一份整改文档。

---

## 11. 设计端预期的后续动作（Codex 不执行）

完成审计报告并回传后，停止执行。设计端将基于真实报告决定下一份交付文档是否为：

```text
Phase 1：引入 openspec/schemas/superspec/ 基础设施并设置可回滚配置
```

或者先执行一项阻塞问题修复，例如：

```text
Phase 0A：统一 Agent 入口资产职责但不启用 SuperSpec
Phase 0B：保护或收敛当前活跃任务真相源
```

除非收到新的明确执行文档，不得自行进入以上任何阶段。

---

## 12. 参考基线（供审计理解，非执行指令）

以下上游材料定义了本次迁移审计的目标语义。Codex 可阅读以理解差距，但本阶段不应执行其中的安装或迁移命令：

1. `danielhanold/superspec` README  
   `https://github.com/danielhanold/superspec`
2. SuperSpec project layout  
   `https://github.com/danielhanold/superspec/blob/main/docs/project-layout.md`
3. SuperSpec schema v4  
   `https://github.com/danielhanold/superspec/blob/main/openspec/schemas/superspec/schema.yaml`
4. OpenSpec Customization documentation  
   `https://github.com/Fission-AI/OpenSpec/blob/main/docs/customization.md`
5. DiagnoseToolPy remote repository snapshot  
   `https://github.com/zhiwuli0228/DiagnoseToolPy`

---

**执行边界再次确认：本任务书只授权 Codex 读取本地仓库并新增一份审计报告，不授权任何迁移、安装、整理、修复、提交或推送操作。**
