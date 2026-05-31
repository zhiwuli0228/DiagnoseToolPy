# DiagnoseToolPy SuperSpec 迁移审计与基线报告

> 执行阶段：Phase 0  
> 执行工具：Codex  
> 执行日期：2026-05-31  
> 本地仓库路径：`E:/009workspace/claudecode/DiagnoseToolPy`  
> 当前分支：`claude_master`  
> HEAD Commit：`391e496b22dc0bef430dc2cf1d9ac76a1c3c4212`  
> 审计性质：只读审计，仅新增本报告文件

## 1. 执行摘要

- 审计结论：**暂缓进入 Phase 1**
- BLOCKER 数量：1
- HIGH 数量：4
- 是否发现本阶段范围外修改：是
- 是否存在未提交工作需要保护：是

当前仓库已经具备完整的 OpenSpec `spec-driven` 资产，但工作区并不干净，且同时存在 `AGENT.md` / `AGENTS.md` 双入口、`.claude/` 与 `.opencode/` 双套 opsx 工作流、`work-items/` 与 `openspec/` 并行任务语义等治理风险。由于已有未提交的业务代码和生成数据改动，本次不适合直接进入 SuperSpec schema 引入阶段。

## 2. 审计边界与实际执行动作

### 2.1 本次读取范围

已只读读取或确认以下范围：

- 仓库根目录与 Git 状态
- `openspec/config.yaml`
- `docs/README.md`
- `docs/00-project/project-brief.md`
- `docs/00-project/current-state.md`
- `docs/02-harness/harness-standard.md`
- `docs/03-openspec/proposal-rule.md`
- `docs/03-openspec/design-rule.md`
- `docs/03-openspec/spec-rule.md`
- `docs/03-openspec/tasks-rule.md`
- `AGENT.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.claude/`
- `.opencode/`
- `openspec/specs/`
- `openspec/changes/`
- `work-items/`
- `docs/rectification/`
- 代表性的 `work-items/*` 状态文件
- 代表性的 `openspec/specs/*` 规范文件
- 代表性的 `openspec/changes/archive/*` 归档文件

### 2.2 本次新增文件

- `docs/rectification/00-superspec-migration-audit-report.md`

### 2.3 未执行动作确认

确认未执行：

- schema 安装
- `openspec/config.yaml` 配置切换
- 业务代码修改
- Git 写操作
- OpenSpec lifecycle 命令

## 3. Git 与仓库身份基线

| 项目 | 结果 | 证据/说明 |
|---|---|---|
| 仓库根目录 | `E:/009workspace/claudecode/DiagnoseToolPy` | `git rev-parse --show-toplevel` |
| 当前分支 | `claude_master` | `git branch --show-current` |
| HEAD Commit | `391e496b22dc0bef430dc2cf1d9ac76a1c3c4212` | `git rev-parse HEAD` |
| Remote | `origin git@github.com:zhiwuli0228/DiagnoseToolPy.git` | `git remote -v` |
| 工作区状态 | 已有未提交改动与大量未跟踪生成物 | `git status --short --branch` |
| Existing worktrees | 仅当前 worktree | `git worktree list` |

工作区状态要点：

- 已修改的 tracked 文件：
  - `.claude/settings.local.json`
  - `data/indexes/bm25/corpus.jsonl`
  - `diagnose_tool/analyzer/cluster_analyzer.py`
  - `diagnose_tool/analyzer/log_aggregator.py`
  - `diagnose_tool/analyzer/reader.py`
- 已存在的 untracked 目录/文件：
  - `.claude/settings.json`
  - `.playwright-mcp/*`
  - `analysis-tasks-page.png`
  - `cluster-analysis-form.png`
  - `cluster-form-visible.png`
  - `data/output/*`
  - `data/temp/*`
  - `docs/rectification/`
  - `page-2026-05-31T03-41-47-231Z.yml`

## 4. 当前目录与资产概览

### 4.1 顶层目录概览

当前顶层包含：

- `.claude/`
- `.github/`
- `.opencode/`
- `.playwright-mcp/`
- `.pytest_cache/`
- `.ruff_cache/`
- `.trunk/`
- `.venv/`
- `config/`
- `data/`
- `diagnose_tool/`
- `diagnosis_prompt/`
- `docs/`
- `frontend/`
- `openspec/`
- `tests/`
- `work-items/`
- `AGENT.md`
- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `README_ZH.md`
- `main.py`
- `pyproject.toml`
- `uv.lock`

### 4.2 治理资产目录概览

| 目录/文件 | 资产层级判断 | 实际状态摘要 |
|---|---|---|
| `AGENT.md` | 入口约束资产 | 项目级 AI 规则文件，内容完整且覆盖硬约束、模块边界、测试规则、OpenSpec 规则 |
| `AGENTS.md` | 入口约束资产 | 与 `AGENT.md` 实质重复，且同样被项目文档链路引用 |
| `CLAUDE.md` | 工具专用资产 | 面向 Claude Code 的执行指引，含前端浏览器验证要求与工作流说明 |
| `.claude/` | 工具专用资产 | 包含 `opsx` 命令与 `openspec-*` skills，以及本地权限配置 |
| `.opencode/` | 工具专用资产 | 也包含一整套 `opsx` 命令与 `openspec-*` skills，和 `.claude/` 高度同构 |
| `docs/` | 长期项目知识资产 | 作为 harness context hub 与领域/架构/开发规则入口，职责清晰 |
| `openspec/` | Schema / 流程模板资产 | 当前仍是 `spec-driven`，已有 `specs/` 和 `archive` 化的 `changes/` |
| `work-items/` | Legacy / 临时任务资产 | 仍保留独立任务状态记录，但当前大多已完成或历史化 |
| `diagnose_tool/` | 业务实现资产 | Python 后端业务代码，属于迁移保护范围 |
| `frontend/` | 业务实现资产 | React/Vite 前端实现，属于迁移保护范围 |
| `tests/` | 业务实现资产 | 业务验证代码，属于迁移保护范围 |
| `config/` | 业务/配置资产 | 应用配置与规则文件所在地，属于保护范围 |
| `data/` | 业务运行资产 | 包含输出、索引、案例与运行时文件，当前有生成物和未提交内容 |

### 4.3 公开远程快照与本地差异

| 路径/事项 | 公开 main 快照观察 | 本地结果 | 差异影响 |
|---|---|---|---|
| 根级目录 | 包含 `.claude/`、`.opencode/`、`docs/`、`openspec/`、`work-items/`、业务代码目录 | 一致，并额外存在 `.playwright-mcp/`、`diagnosis_prompt/`、`README_ZH.md` 等本地资产 | 说明本地已发生额外演进，不能仅依赖公开快照 |
| `openspec/config.yaml` | 公开快照为 `schema: spec-driven` | 仍然是 `schema: spec-driven`，且无 `context` / `rules` | 当前不需要先修复 schema 配置，但也还没进入 SuperSpec |
| `docs/README.md` | 项目上下文中心，要求按任务类型分层阅读 | 与快照一致 | 规则链路保持稳定 |
| `AGENTS.md` / `AGENT.md` | 公开快照已提示两者并存风险 | 本地确实同时存在，且内容基本重复 | 需要后续统一入口 |
| `work-items/` | 公开快照中存在独立任务资产 | 本地仍存在，且有 DONE/NEW 状态文件 | 继续构成第二套任务语义来源 |

## 5. Agent 与工具专用资产审计

| 文件/目录 | 当前职责摘要 | 被谁引用 | 是否权威候选 | 冲突/风险 | 后续建议 |
|---|---|---|---:|---|---|
| `AGENT.md` | 项目级规则、硬约束、模块边界、测试和 OpenSpec 规范 | `docs/README.md`、项目说明、`AGENTS.md` 内容链路 | 是 | 与 `AGENTS.md` 重复 | 后续应统一入口并保留单一权威源 |
| `AGENTS.md` | 与 `AGENT.md` 基本重复的项目级规则文件 | `AGENT.md`、项目文档链路 | 是 | 命名与职责重复，容易造成双入口 | 后续应统一为单一入口，避免双文件并行 |
| `CLAUDE.md` | Claude Code 运行指导、浏览器验证要求、前端命令 | Claude Code 场景 | 是 | 与 `.claude/` 内命令体系叠加，职责边界不够单薄 | 后续仅保留工具特定指南，避免覆盖项目级规则 |
| `.claude/commands/opsx/*` | OpenSpec 变更生命周期命令 | Claude Code | 否 | 与 `.opencode/` 命令重复，且含 OpenSpec 流程自动化 | 后续需明确是工具本地实现还是共享规范 |
| `.claude/skills/openspec-*` | OpenSpec 相关技能封装 | Claude Code | 否 | 与 `.opencode/skills/` 重复 | 后续应减少重复，避免多工具不一致 |
| `.claude/settings.local.json` | 本地权限与插件配置 | Claude Code 本地环境 | 否 | 包含较宽泛 allow list，存在执行面过宽风险 | 后续应收敛权限，避免未来误触写操作 |
| `.opencode/commands/opsx-*.md` | OpenCode 变更生命周期命令 | OpenCode | 否 | 与 `.claude/` 结构几乎同构 | 后续应明确单一规范来源 |
| `.opencode/skills/openspec-*` | OpenCode 相关技能封装 | OpenCode | 否 | 与 `.claude/skills/` 重复 | 后续应统一实现或抽象共享规范 |

### 5.1 `AGENT.md` 与 `AGENTS.md` 命名/职责结论

两者当前内容几乎完全重复，且都在承担项目级入口约束职责。  
从可维护性看，这不是两个独立权威源，而是一个重复资产。后续迁移中应统一成单一入口，避免新流程同时读取两份规则。

### 5.2 Claude / OpenCode / Codex 资产结论

- `.claude/` 和 `.opencode/` 都已经内置 `opsx` 工作流命令和 `openspec-*` skills。
- 这意味着项目目前不是“单一工具入口”，而是“多工具同构入口”。
- `.claude/settings.local.json` 还启用了较宽泛的命令 allow list，包括 `git checkout *`、`curl *`、`powershell *` 等，未来若与 SuperSpec 的 apply/finalize 行为叠加，容易造成误操作风险。
- 当前不建议在 Phase 1 继续扩展新的工具专用命令集，先收敛职责边界更安全。

### 5.3 Git 自动化与 SuperSpec finalize 冲突风险

- 现有 `.claude/` 和 `.opencode/` 命令已经表达了自动化 OpenSpec 流程。
- SuperSpec 后续还会引入 worktree、apply、finalize 等更强的 Git closeout 行为。
- 如果不先统一入口和权限边界，未来可能出现“工具指令 + schema 流程 + 本地 allow list”三层叠加，导致不可审计的 Git 行为。

## 6. `docs/` 长期资产审计

| 目录/文件 | 声明职责 | 实际内容摘要 | 资产层级判断 | 问题等级 | 后续建议 |
|---|---|---|---|---|---|
| `docs/README.md` | 文档入口与阅读策略 | 明确分层读取策略与硬规则 | 长期知识资产 | NONE | 维持当前职责即可 |
| `docs/00-project/` | 项目目标、当前状态、术语、路线图 | 反映项目基线与演进状态 | 长期知识资产 | LOW | 保留，但要避免被临时任务污染 |
| `docs/01-architecture/` | 架构、模块边界、存储契约、ADR | 架构约束完整 | 长期知识资产 | NONE | 继续作为项目稳定约束来源 |
| `docs/02-harness/` | harness 标准与执行规则 | 规定 AI 工作方式和连续性要求 | 长期知识资产 | LOW | 与 `AGENT.md` 保持一致性 |
| `docs/03-openspec/` | OpenSpec proposal/design/spec/tasks 规则 | 规范化 OpenSpec 产物格式 | Schema / 流程模板资产 | NONE | 继续保留为 schema 迁移参考 |
| `docs/04-development/` | 开发、测试、依赖、运行指南 | 研发流程与命令文档 | 长期知识资产 | NONE | 维持 |
| `docs/05-domain/` | 领域模板与分析规则 | 日志分析、案例、提示模板 | 长期知识资产 | NONE | 维持 |
| `docs/06-operations/` | 部署与运维 | 运行、容器、目录访问、安全 | 长期知识资产 | NONE | 维持 |
| `docs/07-templates/` | 模板库 | ADR / proposal / spec / tasks 模板 | 长期知识资产 | LOW | 维持，避免与 schema artifacts 混淆 |
| `docs/99-archive/` | 历史文档归档 | 存放废弃或历史资料 | 归档资产 | NONE | 维持 |
| `docs/rectification/` | 整改 / 审计输出目录 | 当前仅用于本次迁移审计产物 | 过程资产 | LOW | 可继续用于审计，但不应承载长期规则 |

### 6.1 长期文档与 change 过程资产边界

`docs/` 的长期职责总体清晰，问题不在结构本身，而在“长期知识”和“单次任务过程”之间的边界需要更严格地分离。  
当前 `docs/rectification/` 是合理的审计输出位置，但不要把阶段性审计结果进一步扩散到长期规则文档里。

### 6.2 规则重复与过度更新要求

`docs/README.md` 与 `AGENT.md`/`AGENTS.md` 的规则链路基本一致，但 `docs/README.md` 仍强调完成变更后更新 `current-state.md`。这一要求本身可接受，不过后续应避免把所有短任务都抬升为长期状态变更，防止状态文件被过度更新。

### 6.3 生成型 / CodeWiki 类资产现状

本次审计未发现独立的 `docs/generated/` 或明显 CodeWiki 导出目录。  
但存在大量运行时生成物和浏览器采集产物（例如 `.playwright-mcp/`、截图、`data/output/`、`data/temp/`），这些都不应被误当作长期规则资产。

## 7. OpenSpec 状态与 SuperSpec 迁移差距

### 7.1 当前 `openspec/config.yaml`

- 当前 schema：`spec-driven`
- 当前内容：仅有 `schema: spec-driven`，无 `context`，无 `rules`
- 与项目文档：未见失效路径引用
- SuperSpec 相关配置：**不存在**

### 7.2 Current Living Specs

| Capability | 状态摘要 | 后续迁移保护要求 |
|---|---|---|
| `project-skeleton` | 定义可运行 FastAPI 骨架、配置、目录与 whitelist 验证 | 作为基础系统能力保留 |
| `server-directory-scan` | 服务端目录扫描 | 保留为分析入口能力 |
| `log-reader-and-multiline` | 流式读与多行合并 | 作为大日志处理基础能力保留 |
| `header-parser-and-classifier` | 复杂头解析与分类 | 保留 |
| `evidence-report-generation` | 证据包/报告生成 | 保留 |
| `casebase-file-storage` | 案例文件存储 | 保留 |
| `manual-case-creation` | 人工建案例 | 保留 |
| `basic-case-retrieval` | 基于关键词/规则/BM25 的检索 | 保留 |
| `docker-deployment` | Docker 部署 | 保留 |
| `react-frontend-shell` | 前端壳 | 保留 |
| `settings-config-api` / `settings-page-ui` | 配置 API 与 UI | 保留 |

Living specs 与当前项目能力总体相符，没有看到明显“空壳 spec”或和业务边界冲突的情况。

### 7.3 Current Changes / Archives

| Change | Active/Archived | Artifact 结构 | 与迁移的关系 |
|---|---|---|---|
| `openspec/changes/archive/*` 下的所有 change | Archived | `proposal.md` / `design.md` / `tasks.md` / `specs/*/spec.md` / `.openspec.yaml` | 说明项目历史上采用的是 spec-driven 过程资产 |
| `openspec/changes/` 根目录 | 无 active change | 仅有 `archive/` | 当前没有活动变更，说明没有正在进行的 OpenSpec 过程冲突 |

当前 `openspec/changes/` 没有 active change，这一点对迁移是正面的。

### 7.4 Current Schemas

`openspec/schemas/` 当前不存在。  
这意味着本地没有已安装的 `superspec` schema，也没有与之冲突的自定义 schema 资产。

### 7.5 SuperSpec v4 差距矩阵

| SuperSpec 目标要求 | 当前本地状态 | 差距/冲突 | 风险等级 | Phase 1 是否可处理 |
|---|---|---|---|---:|
| `openspec/schemas/superspec/schema.yaml` | 不存在 | 尚未安装 schema 资产 | NONE | 是 |
| `openspec/schemas/superspec/templates/*` | 不存在 | 尚未安装模板资产 | NONE | 是 |
| `openspec/config.yaml` 可切换 `schema: superspec` | 当前仍为 `spec-driven` | 需引入新 schema 后再切换 | MEDIUM | 否 |
| 现有 active changes 可被保护 | 当前无 active changes | 保护成本低 | NONE | 是 |
| Agent 工具具备未来执行前提 | 现有多工具重复资产已存在 | 入口与权限需要先收敛 | HIGH | 否 |
| Git/worktree 策略无阻塞冲突 | 当前只有一个 worktree，但工作区已 dirty | 未提交工作会影响迁移基线 | HIGH | 否 |

结论：**当前可以确认没有现成的 SuperSpec 冲突 schema，但不适合直接进入 Phase 1，因为工作区与工具入口都尚未收敛到可审计基线。**

## 8. `work-items/` 与任务真相源审计

| Work item | 当前内容类型 | 是否仍活跃 | 对应 OpenSpec change | 迁移/归档建议 | 风险 |
|---|---|---:|---|---|---|
| `cr-001-code-review-fix` | 代码审查修复记录与状态 | 否 | 未发现 active change 对应 | 作为历史记录保留，后续可归档到 legacy 区 | MEDIUM |
| `fe-002-frontend-tests` | 前端测试补充记录与状态 | 否 | 未发现 active change 对应 | 作为历史记录保留，后续可归档到 legacy 区 | MEDIUM |

### 8.1 Source of Truth 当前判断

| 事项 | 当前实际 source of truth | 是否唯一 | 冲突资产 | 后续建议 |
|---|---|---:|---|---|
| AI 通用硬约束 | `AGENT.md` + `docs/README.md` + `docs/02-harness/*` | 否 | `AGENTS.md` 重复 | 统一入口文件，避免双份权威源 |
| 项目架构边界 | `docs/01-architecture/*` | 是 | 无明显冲突 | 维持唯一来源 |
| 系统行为合同 | `openspec/specs/*` + `docs/05-domain/*` | 是 | 无 active change | 维持唯一来源 |
| 变更任务状态 | `openspec/changes/` 为主，但 `work-items/` 仍存在 | 否 | `work-items/` | 后续应冻结为 legacy，不再新增活跃任务 |
| OpenSpec schema / artifact rules | `openspec/config.yaml` + `docs/03-openspec/*` | 是 | 无 superspec schema | 继续保留 spec-driven 现状，待 Phase 1 引入新 schema |

`work-items/` 当前更像历史/协作记录，而不是项目的唯一活动任务源；但它仍在场，因此未来很容易重新变成第二套真相源。迁移前必须先明确它的地位。

## 9. 业务实现保护范围登记

| 路径 | 是否存在 | 当前职责 | 是否已有未提交变动 | 后续治理阶段保护结论 |
|---|---:|---|---:|---|
| `diagnose_tool/` | 是 | Python 后端业务实现 | 是 | Phase 0 保护路径，不得修改 |
| `frontend/` | 是 | React/Vite 前端实现 | 未在本次 diff 中确认变动，但属于保护路径 | Phase 0 保护路径，不得修改 |
| `tests/` | 是 | 测试代码 | 未在本次 diff 中确认变动，但属于保护路径 | Phase 0 保护路径，不得修改 |
| `config/` | 是 | 应用配置与规则 | 未在本次 diff 中确认变动，但属于保护路径 | Phase 0 保护路径，不得修改 |
| `data/` | 是 | 输出、索引、案例与运行数据 | 是 | Phase 0 保护路径，不得修改 |
| `main.py` | 是 | 入口脚本 | 未见本次变动记录 | 后续阶段原则上不改 |
| `pyproject.toml` | 是 | Python 项目配置 | 未见本次变动记录 | 后续阶段原则上不改 |
| `uv.lock` | 是 | 依赖锁定 | 未见本次变动记录 | 后续阶段原则上不改 |
| `Dockerfile` | 是 | 容器构建 | 未见本次变动记录 | 后续阶段原则上不改 |
| `docker-compose.yml` | 是 | 本地部署编排 | 未见本次变动记录 | 后续阶段原则上不改 |
| `.github/workflows/` | 是 | CI 配置 | 未见本次变动记录 | 后续阶段原则上不改 |

当前的未提交变动已经触及业务代码和索引数据，因此 Phase 1 绝不能在不明确保护策略的情况下启动。

## 10. 问题清单与整改优先级

| ID | 问题 | 证据路径 | 风险等级 | 拟处理阶段 | 本阶段是否已修改 |
|---|---|---|---|---|---:|
| AUD-001 | 工作区已 dirty，且包含业务代码、索引与生成物改动，无法在同一基线上安全引入新 schema | `git status --short --branch`，`diagnose_tool/analyzer/*.py`，`data/indexes/bm25/corpus.jsonl`，`data/output/*` | BLOCKER | Phase 0 先清理/隔离，Phase 1 再引入 | 否 |
| AUD-002 | `AGENT.md` 与 `AGENTS.md` 双入口重复，职责边界不唯一 | `AGENT.md`，`AGENTS.md`，`docs/README.md` | HIGH | Phase 0/0A 统一入口 | 否 |
| AUD-003 | `.claude/` 与 `.opencode/` 均持有同构 `opsx` 命令与 `openspec-*` skills，工具级流程重复 | `.claude/commands/opsx/*`，`.claude/skills/openspec-*`，`.opencode/commands/opsx-*.md`，`.opencode/skills/openspec-*` | HIGH | Phase 0/0A 收敛工具入口与权限 | 否 |
| AUD-004 | `work-items/` 仍是独立任务语义来源，和 OpenSpec 变更流并存 | `work-items/*`，`openspec/changes/*` | HIGH | Phase 0B 冻结 legacy 任务源 | 否 |
| AUD-005 | `.claude/settings.local.json` 含较宽泛命令 allow list，未来可能与 SuperSpec apply/finalize 行为冲突 | `.claude/settings.local.json` | HIGH | Phase 0 先收敛权限 | 否 |

## 11. Phase 1 准入结论

### 11.1 结论

**暂缓进入 Phase 1。**

### 11.2 结论依据

1. 当前工作区不是干净基线，且改动已经落在业务代码、索引数据和运行产物上。
2. `AGENT.md` / `AGENTS.md` 仍是重复入口，无法作为后续 SuperSpec 迁移的单一权威规则源。
3. `.claude/` 与 `.opencode/` 已形成两套同构 OpenSpec 工作流命令，未来如果直接叠加 SuperSpec schema，风险会进一步放大。
4. `work-items/` 仍然存在，虽然当前看起来是历史状态，但它仍然是一个独立任务真相源。
5. 当前没有 `openspec/schemas/superspec/` 冲突资产，也没有 active change，这一点是正面的，但不足以抵消当前基线的不稳定性。

### 11.3 Phase 1 允许修改范围建议

若后续解除阻塞并重新进入 Phase 1，建议只允许修改：

- `openspec/config.yaml`
- `openspec/schemas/superspec/`
- `docs/rectification/` 中与本次审计直接相关的后续说明文件
- 与 schema 引入直接相关、且不会覆盖现有业务/生成物的最小配置文件

### 11.4 Phase 1 仍需禁止修改范围建议

后续 Phase 1 仍应禁止修改：

- `diagnose_tool/`
- `frontend/`
- `tests/`
- `config/`
- `data/` 中的现有业务输出与索引
- `AGENT.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.claude/`
- `.opencode/`
- 任何 Git 写操作

## 12. Codex 执行回传摘要

- 新增文件：`docs/rectification/00-superspec-migration-audit-report.md`
- 修改现有文件：应为无
- 删除/移动文件：应为无
- 未完成审计项：无
- 需要用户或设计端决策的问题：
  1. 是否先做 Phase 0A，统一 `AGENT.md` / `AGENTS.md` 的单一权威入口
  2. 是否冻结或归档 `work-items/`，避免其继续作为第二套任务源
  3. 是否先收敛 `.claude/` / `.opencode/` 的重复 OpenSpec 工作流资产，再进入 SuperSpec schema 引入

