# DiagnoseToolPy 全面适配 SuperSpec：Phase 0B 治理证据可追踪性修正与 Phase 1 最终准入执行任务书

> **交付对象**：Codex  
> **执行阶段**：Phase 0B — Governance Evidence Trackability & Final Readiness Gate  
> **前置阶段**：Phase 0 审计、Phase 0A 干净迁移基线与治理权威收敛已执行  
> **执行工作区**：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> **执行分支**：`chore/superspec-governance-migration`  
> **基线 HEAD**：`fcd3de0f3220635d57878d414ba05e52dd8ff0d1`  
> **目标工作流**：OpenSpec + `danielhanold/superspec` schema  
> **本阶段性质**：补正 Phase 0A 暴露的治理证据链缺口；不得安装或启用 SuperSpec schema

---

## 1. 本阶段判定背景

Phase 0A 回传结果表明：

```text
- 原工作区已形成干净基线；
- 已基于 HEAD fcd3de0f3220635d57878d414ba05e52dd8ff0d1 建立独立整改 worktree；
- AGENTS.md 已作为项目级权威入口；
- AGENT.md 已降级为兼容入口；
- work-items/README.md 已新增冻结声明；
- Phase 0A 执行报告已生成；
- 未修改业务代码、OpenSpec schema/config 或工具专用资产。
```

上述工作方向正确，但同时暴露一个必须在 Phase 1 前处理的问题：

```text
docs/rectification/ 被 .gitignore 忽略，
导致 Phase 0A 执行报告存在于磁盘，但不会进入常规 Git 变更清单。
```

此外，Phase 0A 回传中的：

```text
git diff --name-only
```

只显示 tracked 文件的修改，不包含新增未跟踪的：

```text
work-items/README.md
```

因此，**Phase 0A 结论调整为 CONDITIONAL PASS**：

- 治理入口收敛和 worktree 隔离成果可保留；
- 但在整改报告进入版本证据链、全部新增治理资产可在 Git 变更清单中观察之前，不得进入 SuperSpec schema 引入阶段。

---

## 2. 本阶段目标

本阶段只完成以下任务：

1. 核验 Phase 0A 已完成变更仍严格位于允许范围内，且业务保护路径未发生修改。
2. 定位 `docs/rectification/` 被忽略的具体规则来源。
3. 若忽略规则属于仓库内可治理的 `.gitignore` 规则，以最小修改方式使整改报告目录成为可版本化治理资产。
4. 将 Phase 0 迁移审计报告与 Phase 0A 执行报告纳入当前整改 worktree 的可提交变更集合。
5. 新增 Phase 0B 执行报告，并确保它同样能够被 Git 识别。
6. 输出进入 Phase 1（SuperSpec schema 基础设施引入）的最终准入结论。

**本阶段不得修改 Phase 0A 已收敛的 `AGENT.md` / `AGENTS.md` 内容，不得安装 SuperSpec schema，不得修改 OpenSpec 配置，不得修改任何业务代码。**

---

## 3. 治理决策：整改报告必须纳入版本控制

### 3.1 资产定性

以下报告不是临时输出、缓存、运行日志或本地调试产物：

```text
docs/rectification/00-superspec-migration-audit-report.md
docs/rectification/01-superspec-clean-baseline-and-governance-authority-report.md
docs/rectification/02-superspec-governance-evidence-trackability-report.md
```

它们属于：

```text
项目治理迁移的决策、证据与准入记录
```

应与治理变更一并进入版本控制，以支持：

- 后续 Codex / Claude Code / 人工审查理解迁移依据；
- 追踪为什么统一入口、冻结旧任务源、引入 SuperSpec；
- 后续回滚或修正规则时具备事实基线；
- 保证迁移过程不是只存在于本地机器的不可审计信息。

### 3.2 与生成型文件的区别

本阶段不得将下列运行型/生成型内容解禁或纳入版本控制：

```text
.playwright-mcp/
data/output/
data/temp/
截图文件
浏览器页面采集 yml
本地缓存、日志、索引生成物
```

整改报告需要可追踪，不意味着运行生成物应被纳入仓库。

---

## 4. 严格执行范围

### 4.1 本阶段允许读取的路径

允许读取：

```text
.gitignore
.git/info/exclude
AGENT.md
AGENTS.md
docs/README.md
docs/rectification/
work-items/README.md
openspec/config.yaml
openspec/schemas/
```

允许使用以下只读检查命令：

```bash
git status --short --branch --untracked-files=all
git diff --stat
git diff --name-only
git diff -- AGENT.md AGENTS.md work-items/README.md .gitignore
git check-ignore -v <path>
git ls-files <path>
git branch --show-current
git rev-parse HEAD
git worktree list
git config --get core.excludesFile
```

若需要判断全局 ignore 来源，只允许读取由 `git config --get core.excludesFile` 返回的文件内容。

### 4.2 本阶段允许新增或修改的路径

仅允许：

```text
.gitignore
docs/rectification/00-superspec-migration-audit-report.md
docs/rectification/01-superspec-clean-baseline-and-governance-authority-report.md
docs/rectification/02-superspec-governance-evidence-trackability-report.md
```

并保留 Phase 0A 已产生、但本阶段不得进一步修改的变更：

```text
AGENT.md
AGENTS.md
work-items/README.md
```

### 4.3 本阶段禁止修改的路径

严禁新增、修改、移动、删除或格式化：

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
.claude/
.opencode/
CLAUDE.md
README.md
README_ZH.md
AGENT.md                     # 已完成 Phase 0A 修改，本阶段不得再次编辑
AGENTS.md                    # 已完成 Phase 0A 修改，本阶段不得再次编辑
work-items/README.md         # 已完成 Phase 0A 新增，本阶段不得再次编辑
```

### 4.4 禁止 Git / OpenSpec 操作

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
git switch
git branch -D
git worktree remove
git add
git rm
git mv
openspec init
openspec schema init
openspec schema fork
openspec schema validate
任何 /opsx:* 或 opsx-* lifecycle 命令
```

> 本阶段仅产生待用户审查和手动提交的工作树变更。不得由 Codex 进行暂存或提交。

---

## 5. 启动前状态验证

在整改 worktree 中执行：

```bash
cd E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance

git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git diff --name-only
git worktree list
```

### 5.1 必须匹配的基础信息

应满足：

```text
分支：chore/superspec-governance-migration
HEAD：fcd3de0f3220635d57878d414ba05e52dd8ff0d1
```

### 5.2 启动时允许存在的 Phase 0A 变更

启动状态中只允许存在：

```text
M  AGENT.md
M  AGENTS.md
?? work-items/README.md
```

`docs/rectification/01-superspec-clean-baseline-and-governance-authority-report.md` 可能因被忽略而不显示，这是本阶段要修正的问题。

### 5.3 必须停止的条件

若启动时出现以下任一情况，立即停止，仅回传状态：

- 当前分支或 HEAD 不匹配；
- `AGENT.md`、`AGENTS.md`、`work-items/README.md` 之外出现其他可见变更；
- 任何业务保护路径存在新增或修改；
- Phase 0A 的三项预期变更缺失。

回传格式：

```text
STOPPED: Phase 0A working-tree baseline no longer matches the approved pending-change set.
Unexpected paths:
- <path>
No Phase 0B changes were made.
```

---

## 6. 审核 Phase 0A 已有 Diff，不得改写

本阶段需要只读核验 Phase 0A 的内容是否符合任务要求，但不得编辑以下文件：

```bash
git diff -- AGENT.md AGENTS.md
```

对于未跟踪的 `work-items/README.md`，直接读取其内容。

### 6.1 核验重点

#### `AGENT.md`

应只保留兼容入口含义：

- 声明本文件仅为兼容历史引用或工具查找保留；
- 明确 `AGENTS.md` 为项目级权威入口；
- 指向 `docs/README.md` 的上下文路由职责；
- 不继续保留完整的规则副本。

#### `AGENTS.md`

应只增加短小权威声明：

- 不应在 Phase 0A 被大面积重写；
- 不应丢失原有硬约束；
- 应声明工具特定资产不得覆盖项目级规则。

#### `work-items/README.md`

应明确：

- 目录已冻结；
- 既有记录仅供历史追踪；
- 不再创建新的实现任务；
- 后续变更通过 `openspec/changes/<change-name>/` 管理。

### 6.2 停止条件

若发现 Phase 0A 实际修改不符合以上要求，停止本阶段，不修改 `.gitignore` 或整改报告目录，并在回传中说明：

```text
STOPPED: Phase 0A governance changes require correction before evidence trackability can be finalized.
```

---

## 7. 定位 `docs/rectification/` 的 Ignore 来源

### 7.1 检查需追踪的报告文件

在整改 worktree 中，首先检查报告文件存在性：

```powershell
Test-Path docs/rectification/01-superspec-clean-baseline-and-governance-authority-report.md
Test-Path docs/rectification/00-superspec-migration-audit-report.md
```

预期：

- `01-*` 文件应存在于整改 worktree；
- `00-*` 文件可能不存在于整改 worktree，因为它在原工作区产生且未被 Git 跟踪。

### 7.2 检查 ignore 匹配来源

执行：

```bash
git check-ignore -v docs/rectification/01-superspec-clean-baseline-and-governance-authority-report.md
git config --get core.excludesFile
```

若 `00-*` 文件存在，也对其执行：

```bash
git check-ignore -v docs/rectification/00-superspec-migration-audit-report.md
```

记录命中规则的：

- 来源文件；
- 行号；
- ignore pattern；
- 是否来自仓库 `.gitignore`、`.git/info/exclude` 或全局 ignore 文件。

---

## 8. Ignore 来源分支处理规则

### 分支 A：忽略来源为仓库受版本管理的 `.gitignore`

若 `git check-ignore -v` 显示命中的规则来源为项目根目录或项目内部受版本控制的 `.gitignore`，允许执行以下动作：

1. 读取 `.gitignore` 中与 `docs/rectification/` 命中相关的最小上下文。
2. 保留对真正临时/运行型文件的 ignore 规则。
3. 以最小改动将 `docs/rectification/` 作为治理证据目录排除于 ignore 规则之外。

#### 推荐追加注释与例外规则

若现有规则是忽略某个宽泛文档/报告路径，但能够通过 negation 恢复该目录，可在相关规则之后添加：

```gitignore
# Versioned governance migration evidence; do not ignore rectification reports.
!docs/rectification/
!docs/rectification/*.md
```

#### 特别注意

Git 对被整体忽略的父目录存在匹配限制。若命中规则直接忽略了父目录，单纯增加子文件例外未必足够。必须执行本任务第 10 节验证命令，确认报告文件最终能出现在 `git status --untracked-files=all` 中。

不得为了让报告显示而广泛解除：

```text
docs/
data/
.playwright-mcp/
output/
temp/
*.png
*.yml
```

等原本应忽略的路径。

### 分支 B：忽略来源为 `.git/info/exclude` 或全局 ignore 文件

若命中规则来源不是仓库可版本管理的 `.gitignore`，而是：

```text
.git/info/exclude
或 core.excludesFile 指向的全局文件
```

则：

- 不得修改 `.gitignore` 去抵消个人本地 ignore 配置；
- 不得修改 `.git/info/exclude` 或全局 ignore 文件；
- 不得使用 `git add -f`；
- 新增 Phase 0B 报告时仅可写入已不被忽略的目录；若 `docs/rectification/` 仍不可追踪，则停止并请求用户手动处理本地 ignore 规则后重试。

回传结论：

```text
STOPPED: Governance evidence is ignored by local/global Git exclude configuration.
User action is required to remove the local ignore rule before Phase 0B can proceed.
```

### 分支 C：`git check-ignore` 未返回规则，但文件仍不出现在 status

若报告文件存在，但 `git check-ignore -v` 未显示命中规则，执行：

```bash
git status --short --untracked-files=all --ignored docs/rectification/
git ls-files docs/rectification/
```

仅记录结果并停止，不得推断性修改任何文件。

---

## 9. 恢复 Phase 0 报告到整改 Worktree

### 9.1 为什么需要恢复

Phase 0 报告是本次迁移的审计事实基础。若只保留 Phase 0A 及之后报告，版本历史将缺少以下依据：

- 为什么创建独立整改 worktree；
- 为什么统一 Agent 入口；
- 为什么冻结 `work-items/`；
- 为什么暂缓 schema 安装。

因此，Phase 0 报告必须与 Phase 0A、Phase 0B 报告一并纳入待提交变更集合。

### 9.2 允许的恢复方式

在完成第 8 节处理、确认 `docs/rectification/` 可被 Git 识别后：

1. 检查整改 worktree 中是否已存在：

```text
docs/rectification/00-superspec-migration-audit-report.md
```

2. 若不存在，只读检查原工作区是否存在该报告：

```powershell
Test-Path E:/009workspace/claudecode/DiagnoseToolPy/docs/rectification/00-superspec-migration-audit-report.md
```

3. 若原工作区存在，允许**复制**该文件到整改 worktree 的同一路径：

```powershell
Copy-Item `
  E:/009workspace/claudecode/DiagnoseToolPy/docs/rectification/00-superspec-migration-audit-report.md `
  E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance/docs/rectification/00-superspec-migration-audit-report.md
```

4. 复制后不得修改 Phase 0 报告正文；只需在 Phase 0B 报告中记录其恢复来源。

### 9.3 停止条件

若整改 worktree 与原工作区均不存在 Phase 0 报告，停止并回传：

```text
STOPPED: Phase 0 audit report cannot be located for versioned evidence restoration.
```

不得重新推断或伪造 Phase 0 报告内容。

---

## 10. 新增 Phase 0B 执行报告

在确认：

- Phase 0A diff 合规；
- ignore 来源已经按允许分支处理；
- `docs/rectification/` 报告能够显示为待提交文件；
- Phase 0 报告已恢复至整改 worktree；

之后，新增：

```text
docs/rectification/02-superspec-governance-evidence-trackability-report.md
```

### 10.1 报告模板

```markdown
# DiagnoseToolPy SuperSpec Phase 0B 治理证据可追踪性修正报告

> 执行阶段：Phase 0B
> 执行工具：Codex
> 执行日期：<YYYY-MM-DD>
> 整改工作区路径：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`
> 整改分支：`chore/superspec-governance-migration`
> 基线 HEAD：`fcd3de0f3220635d57878d414ba05e52dd8ff0d1`

## 1. 执行摘要

- 执行结果：PASS / PARTIAL / STOPPED
- Phase 0A 判定：CONDITIONAL PASS
- 本阶段目标：修正治理报告不可追踪问题，形成 Phase 1 最终准入依据
- 是否建议进入 Phase 1：是 / 否

## 2. 启动状态核验

- 当前 branch：
- 当前 HEAD：
- 启动时可见变更：
- 是否仅包含 Phase 0A 允许变更：

## 3. Phase 0A 变更复核

| 文件 | 预期职责 | 核验结果 | 是否被本阶段再次修改 |
|---|---|---|---:|
| `AGENT.md` | 兼容入口 | | 否 |
| `AGENTS.md` | 权威入口声明 | | 否 |
| `work-items/README.md` | legacy/frozen 声明 | | 否 |

## 4. Ignore 来源核验

| 检查文件 | Ignore 来源 | 命中 pattern | 处理方式 |
|---|---|---|---|
| `docs/rectification/01-superspec-clean-baseline-and-governance-authority-report.md` | | | |
| `docs/rectification/00-superspec-migration-audit-report.md` | | | |

- 是否修改 `.gitignore`：
- `.gitignore` 修改是否仅用于纳入治理报告：
- 是否保持运行生成物继续被忽略：

## 5. 整改报告证据链恢复结果

| 报告 | 来源 | 当前是否存在于整改 worktree | Git 是否可识别为待提交资产 |
|---|---|---:|---:|
| `00-superspec-migration-audit-report.md` | Phase 0 / 原工作区恢复 | | |
| `01-superspec-clean-baseline-and-governance-authority-report.md` | Phase 0A | | |
| `02-superspec-governance-evidence-trackability-report.md` | Phase 0B | | |

## 6. 本阶段文件变更清单

### Phase 0A 保留的待提交变更

- `AGENT.md`
- `AGENTS.md`
- `work-items/README.md`

### Phase 0B 新增或修改变更

- `.gitignore`（仅在仓库 ignore 规则需要修正时）
- `docs/rectification/00-superspec-migration-audit-report.md`
- `docs/rectification/01-superspec-clean-baseline-and-governance-authority-report.md`
- `docs/rectification/02-superspec-governance-evidence-trackability-report.md`

### 明确未修改范围

- 业务代码：
- 测试代码：
- 数据与运行产物：
- OpenSpec schema/config：
- `.claude/` / `.opencode/`：

## 7. Git 验证结果

### `git status --short --branch --untracked-files=all`

```text
<粘贴输出>
```

### `git diff --stat`

```text
<粘贴输出>
```

### `git diff --name-only`

```text
<粘贴输出>
```

### 可见未跟踪文件

```text
<粘贴 `git ls-files --others --exclude-standard` 对相关路径的输出>
```

## 8. Phase 1 最终准入结论

### 结论

- ALLOW / BLOCK

### 进入 Phase 1 前用户需要执行的操作

- 是否建议用户提交 Phase 0A + Phase 0B 治理变更：
- 推荐 commit 范围：
- 推荐 commit message（仅建议，不由 Codex 执行）：

### Phase 1 推荐允许修改范围

- `openspec/schemas/superspec/`
- `openspec/config.yaml`
- `docs/rectification/03-*`

### 尚未处理但不阻断 Phase 1 的事项

- `.claude/` / `.opencode/` 重复流程资产
- `.claude/settings.local.json` 权限范围
- `docs/03-openspec/` 到 SuperSpec 工作流文档的后续迁移
```

---

## 11. 最终验证命令

完成允许的处理后，在整改 worktree 执行：

```bash
git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git status --short --ignored docs/rectification/
git diff --stat
git diff --name-only
git ls-files --others --exclude-standard docs/rectification/ work-items/README.md
git check-ignore -v docs/rectification/00-superspec-migration-audit-report.md
git check-ignore -v docs/rectification/01-superspec-clean-baseline-and-governance-authority-report.md
git check-ignore -v docs/rectification/02-superspec-governance-evidence-trackability-report.md
```

### 11.1 允许出现在最终待提交集合中的文件

最终 Git 可见变更集合只能由以下文件构成：

```text
AGENT.md
AGENTS.md
work-items/README.md
.gitignore                                          # 仅当仓库 ignore 规则被最小修正
docs/rectification/00-superspec-migration-audit-report.md
docs/rectification/01-superspec-clean-baseline-and-governance-authority-report.md
docs/rectification/02-superspec-governance-evidence-trackability-report.md
```

### 11.2 验收要求

必须满足：

- `docs/rectification/00-*`、`01-*`、`02-*` 均存在于整改 worktree；
- 三份报告均不再显示为 ignored；
- 三份报告均可通过 Git 的可见变更检查观察到；
- `AGENT.md` / `AGENTS.md` / `work-items/README.md` 与 Phase 0A 结果保持一致，本阶段未再修改；
- 不存在任何保护路径变更；
- 未安装 schema，未修改 `openspec/config.yaml`；
- 未执行 commit、push、merge、reset、clean、stash 或 add。

---

## 12. Codex 回传要求

执行结束后，必须回传：

1. Phase 0B 报告文件：
   - `docs/rectification/02-superspec-governance-evidence-trackability-report.md`
2. `docs/rectification/` 被忽略的具体原因与处理结果；
3. `.gitignore` 是否修改、修改了哪些行、为什么修改；
4. Phase 0 与 Phase 0A 报告是否均已进入整改 worktree 并可被 Git 识别；
5. `git status --short --branch --untracked-files=all` 完整输出；
6. `git diff --stat` 完整输出；
7. `git diff --name-only` 完整输出；
8. `git ls-files --others --exclude-standard docs/rectification/ work-items/README.md` 输出；
9. 最终建议用户提交的文件范围；
10. 是否允许进入 Phase 1；
11. 未修改业务代码、测试、数据、OpenSpec schema/config、工具专用资产且未进行 Git 提交/推送/暂存的明确确认。

---

## 13. 用户提交建议（Codex 仅输出，不执行）

若 Phase 0B 结果为 `PASS` 且最终文件集合合规，Codex 应向用户建议在人工审查 diff 后提交以下治理变更：

```text
AGENT.md
AGENTS.md
work-items/README.md
.gitignore                                          # 若本阶段有修改
docs/rectification/00-superspec-migration-audit-report.md
docs/rectification/01-superspec-clean-baseline-and-governance-authority-report.md
docs/rectification/02-superspec-governance-evidence-trackability-report.md
```

推荐 commit message 仅作为建议：

```text
chore(governance): establish superspec migration baseline and evidence tracking
```

---

## 14. 后续阶段门禁

只有满足以下条件，才允许开始下一阶段：

```text
Phase 1：引入并验证 danielhanold/superspec 项目级 schema 基础设施
```

门禁条件：

1. Phase 0B 报告结论为 `ALLOW`；
2. 用户已人工审核 Phase 0A + Phase 0B diff；
3. 用户已手动提交治理基线变更；
4. 整改 worktree 在提交后恢复 clean；
5. 提交后 HEAD 由用户回传，作为 Phase 1 新基线；
6. Phase 1 仅允许修改 `openspec/schemas/superspec/`、`openspec/config.yaml` 与新的整改报告，不触碰业务代码和工具目录。

---

## 15. 参考事实

- OpenSpec 支持在 `openspec/config.yaml` 中设置默认 schema、项目 context 与按 artifact 注入的规则；项目级 custom schema 应进入 `openspec/schemas/<schema-name>/` 并随代码版本管理。
- OpenSpec 的 schema 用于定义 artifact 类型及依赖关系，因此引入 SuperSpec schema 应作为后续独立、可验证的配置阶段执行，而不是混入证据链修正阶段。
- Git 的 ignore 机制用于排除有意不跟踪的未跟踪文件；项目治理迁移报告属于需要审计和复核的版本化资产，不应作为被忽略的本地产物处理。
