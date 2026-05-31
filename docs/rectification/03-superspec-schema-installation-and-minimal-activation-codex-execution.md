# DiagnoseToolPy 全面适配 SuperSpec：Phase 1 项目级 Schema 引入与最小激活执行任务书

> **交付对象**：Codex  
> **执行阶段**：Phase 1 — Project-Level SuperSpec Schema Installation & Minimal Activation  
> **前置阶段**：Phase 0、Phase 0A、Phase 0B 已完成并经人工提交  
> **执行工作区**：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> **执行分支**：`chore/superspec-governance-migration`  
> **目标集成**：`danielhanold/superspec`，Schema Version 4  
> **本阶段性质**：仅引入并验证项目级 SuperSpec schema；不得修改业务实现或工具专用资产

---

## 1. 执行前必须由用户完成的操作

Phase 0B 当前仍是待提交变更。执行本任务前，用户必须先在整改 worktree 中人工审查并提交以下既有治理变更：

```text
.gitignore
AGENT.md
AGENTS.md
work-items/README.md
docs/rectification/00-superspec-migration-audit-report.md
docs/rectification/01-superspec-clean-baseline-and-governance-authority-report.md
docs/rectification/02-superspec-governance-evidence-trackability-report.md
```

建议的人工提交信息：

```text
chore(governance): establish superspec migration baseline and evidence tracking
```

> Codex 不得替用户执行上述提交。本任务开始时只负责验证提交已发生、整改 worktree 已恢复干净状态。

---

## 2. 本阶段目标

本阶段只完成以下事项：

1. 确认 Phase 0A/0B 治理资产已经提交，整改 worktree 处于干净状态。
2. 核验本地 OpenSpec CLI 是否存在、当前项目是否仍处于 `spec-driven` 默认 schema。
3. 从 `danielhanold/superspec` 官方仓库获取 **当前 Schema Version 4** 的项目级 schema 资产，并记录获取时对应的上游 commit SHA。
4. 将上游 schema 目录原样复制到本项目：

   ```text
   openspec/schemas/superspec/
   ```

5. 以最小方式将项目默认 schema 从：

   ```yaml
   schema: spec-driven
   ```

   切换为：

   ```yaml
   schema: superspec
   ```

6. 使用 OpenSpec CLI 验证 `superspec` schema 可被识别、现有 living specs / archived changes 不因默认 schema 切换而结构失效。
7. 新增 Phase 1 执行报告，供人工审查与提交。

---

## 3. 重要边界：本阶段仅“引入 schema”，不完成全量适配

### 3.1 本阶段要完成的能力

本阶段建立的是项目级 SuperSpec workflow 基础设施：

```text
openspec/config.yaml
openspec/schemas/superspec/
```

`danielhanold/superspec` 当前 README 将其描述为 OpenSpec custom schema，使用 OpenSpec 作为 orchestrator，并将 Superpowers 的 brainstorming、plan-writing、TDD、subagent dispatch 与 code review 串入变更链路。当前 schema version 为 4，其 artifact 链为：

```text
brainstorm
→ proposal
→ [design optional]
→ specs
→ tasks
→ plan
→ apply
→ verify
→ finalize
```

其中：

- `apply` 依赖 `plan`，并产生 `apply.md`；
- `verify` 依赖 `apply`；
- `finalize` 依赖 `verify`；
- v4 的 `finalize` 会在真实业务 change 中执行 Git closeout、push 以及 PR comment 相关逻辑。

### 3.2 本阶段明确不完成的能力

本阶段不得顺便执行：

```text
- 不初始化或更新 Claude Code / OpenCode / Codex 的 OpenSpec 命令或 skills
- 不安装 Superpowers
- 不修改 OpenSpec 全局配置或全局 workflows
- 不向 openspec/config.yaml 注入 project context / artifact rules
- 不重组 docs/03-openspec/ 或 docs/02-harness/
- 不创建真实业务 change
- 不运行 /opsx:new、/opsx:continue、/opsx:apply、/opsx:verify、/opsx:archive
- 不测试 Superspec 的 worktree / finalize / push 执行能力
```

上述内容分别在后续阶段处理：

```text
Phase 2：项目 context 与 artifact rules 注入
Phase 3：工具端 commands / skills / Superpowers 执行前提治理
Phase 4：以非业务演练 change 验证 artifact DAG
Phase 5：以真实业务 change 验证完整流程
```

---

## 4. 官方依据与采用策略

### 4.1 上游项目依据

采用对象：

```text
Repository: danielhanold/superspec
Integration type: OpenSpec custom schema + Superpowers execution discipline
Current documented schema version: 4
```

上游官方安装说明的核心动作是：

```text
1. 将 openspec/schemas/superspec/ 复制到项目内；
2. 将 openspec/config.yaml 的 schema 设置为 superspec；
3. 执行 openspec schemas 与 openspec validate 验证安装。
```

### 4.2 与上游说明相比，本项目采用的安全调整

上游示例使用：

```bash
echo "schema: superspec" > openspec/config.yaml
```

本项目禁止直接覆盖配置文件。原因是后续 `openspec/config.yaml` 将承载项目 context 与 artifact rules，且即使当前仅有模板注释，也应避免不必要删除。

本阶段必须采用：

```text
只替换 schema 字段值，不覆盖其他已有内容。
```

### 4.3 为什么暂不执行官方全局配置与 harness 初始化命令

上游 README 包含 OpenSpec 全局 profile/workflows 设置以及 `openspec init --tools ... --profile custom` 的步骤。当前项目已经存在 `.claude/` 与 `.opencode/` 工具资产，并在 Phase 0 识别为待治理问题。如果本阶段执行 `openspec init` 或 `openspec update`，可能导致工具目录被重写，破坏“schema 引入”和“工具端适配”之间的审计隔离。

因此：

```text
本阶段只复制项目级 schema，并最小切换项目 config；
全局配置、工具命令与 Superpowers 安装全部延期。
```

---

## 5. 严格允许范围

### 5.1 允许读取的项目路径

```text
.gitignore
AGENT.md
AGENTS.md
docs/README.md
docs/rectification/
work-items/README.md
openspec/config.yaml
openspec/specs/
openspec/changes/
openspec/schemas/                     # 若尚不存在，只用于存在性检查
.claude/                              # 仅查看存在性，不读取/修改内容
.opencode/                            # 仅查看存在性，不读取/修改内容
```

### 5.2 允许联网读取的上游范围

允许从以下官方上游仓库获取 schema 资产与元数据：

```text
https://github.com/danielhanold/superspec.git
```

仅允许复制该仓库中的：

```text
openspec/schemas/superspec/
```

允许读取但不得复制到本项目的上游内容：

```text
README.md
LICENSE
docs/project-layout.md
docs/workflow.md
docs/workflow-details.md
```

读取目的仅为验证版本、来源、布局和许可信息。

### 5.3 允许新增或修改的本项目路径

```text
openspec/config.yaml
openspec/schemas/superspec/**
docs/rectification/03-superspec-schema-installation-and-minimal-activation-report.md
```

### 5.4 允许使用的临时目录

允许在系统临时目录或整改 worktree 之外创建并删除本任务专用下载目录：

```text
E:/009workspace/claudecode/_tmp/superspec-upstream-phase1/
```

要求：

- 创建前若该目录已存在，必须停止，不得覆盖或删除；
- 该临时目录不得位于 `DiagnoseToolPy-superspec-governance` 仓库内；
- 只能删除本任务本次创建的临时目录；
- 删除前必须已经记录上游 commit SHA 与复制清单。

---

## 6. 严格禁止范围

### 6.1 禁止修改的项目路径

严禁新增、修改、移动、删除或格式化：

```text
AGENT.md
AGENTS.md
work-items/
.gitignore
CLAUDE.md
README.md
README_ZH.md
.claude/
.opencode/
.github/
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
openspec/specs/
openspec/changes/
```

### 6.2 禁止执行的 Git 写操作

严禁：

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
```

允许的例外仅为：

```text
在仓库外的临时目录中执行 git clone，用于获取上游 schema；
在该临时 clone 中执行 git rev-parse HEAD，用于记录来源 commit。
```

### 6.3 禁止执行的 OpenSpec / Agent lifecycle 操作

严禁：

```bash
openspec init
openspec update
openspec config set
openspec config profile
openspec schema init
openspec schema fork
任何 /opsx:* 或 opsx-* workflow 命令
任何 Superpowers skill 或安装命令
```

本阶段仅允许的 OpenSpec 命令见第 12 节。

---

## 7. 启动门禁：验证 Phase 0B 已被用户提交

### Step 1：进入整改 worktree 并检查身份

```powershell
Set-Location E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance

git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git worktree list
```

### 必须满足

```text
当前分支：chore/superspec-governance-migration
当前 HEAD：不得仍为 fcd3de0f3220635d57878d414ba05e52dd8ff0d1
工作区：无任何 modified / deleted / renamed / untracked 文件
```

> HEAD 必须发生变化，是因为 Phase 0A + Phase 0B 的治理基线应已经由用户提交。新的 HEAD 需要在 Phase 1 报告中记录，作为后续基线。

### 停止条件

若任一不满足，立即停止，不做任何文件修改或上游下载，回传：

```text
STOPPED: Phase 0A/0B governance changes have not been committed into a clean new baseline.
Expected:
- branch chore/superspec-governance-migration
- HEAD different from fcd3de0f3220635d57878d414ba05e52dd8ff0d1
- clean working tree
No Phase 1 changes were made.
```

---

## 8. 本地 OpenSpec 前置能力只读检查

### Step 2：检查现有配置与 CLI 能力

仅在 Step 1 通过后执行：

```powershell
Get-Content openspec/config.yaml
Test-Path openspec/schemas
Get-ChildItem openspec/specs -Directory | Select-Object -ExpandProperty Name
Get-ChildItem openspec/changes -Force

openspec --version
openspec schemas
openspec validate
```

### 预期状态

进入本阶段前应满足：

```text
openspec/config.yaml 当前仍包含：schema: spec-driven
openspec/schemas/superspec/ 当前不存在
openspec/specs/ 已存在 living specs
openspec/changes/ 不存在 active change（允许存在 archive）
OpenSpec CLI 可执行
openspec validate 在引入前能够成功，或其失败明确与既有状态有关并被报告记录
```

### 停止条件

出现以下任一情况，停止执行，不复制 schema、不修改配置：

| 情况 | 处理 |
|---|---|
| `openspec/config.yaml` 已不是 `schema: spec-driven` | 停止，报告配置已被其他流程修改 |
| `openspec/schemas/superspec/` 已存在 | 停止，报告存在未审查 schema 资产 |
| 存在 active change | 停止，报告 change 路径 |
| OpenSpec CLI 不可执行 | 停止，报告安装缺失；不得自行安装 |
| 引入前 `openspec validate` 失败且失败涉及 existing specs/changes | 停止，先修复既有 OpenSpec 基线 |

> 若 `openspec validate` 因 CLI 版本参数差异而不能按无参数运行，允许只读执行 `openspec validate --help`，记录可用验证命令并停止，由设计端决定后续调整；不得自行猜测执行破坏性命令。

---

## 9. 获取上游 SuperSpec Schema

### Step 3：创建临时拉取目录

首先验证临时目录不存在：

```powershell
$UpstreamTmp = "E:/009workspace/claudecode/_tmp/superspec-upstream-phase1"
Test-Path $UpstreamTmp
```

若返回 `True`，停止：

```text
STOPPED: The designated upstream temporary directory already exists.
No overwrite or cleanup was performed.
```

若返回 `False`，创建父目录并拉取官方仓库：

```powershell
New-Item -ItemType Directory -Force -Path "E:/009workspace/claudecode/_tmp" | Out-Null
git clone --depth 1 --filter=blob:none --sparse https://github.com/danielhanold/superspec.git $UpstreamTmp
Set-Location $UpstreamTmp
git sparse-checkout set openspec/schemas/superspec
git rev-parse HEAD
```

将 `git rev-parse HEAD` 的结果记录为：

```text
UPSTREAM_SUPERSPEC_COMMIT=<sha>
```

### Step 4：验证上游内容

在上游临时目录中执行只读验证：

```powershell
Get-ChildItem -Recurse openspec/schemas/superspec | Select-Object -ExpandProperty FullName
Get-Content openspec/schemas/superspec/schema.yaml -TotalCount 30
Select-String -Path openspec/schemas/superspec/schema.yaml -Pattern "name:|version:|brainstorm|proposal|plan|apply|verify|finalize"
```

必须确认：

```text
- schema 路径存在；
- schema.yaml 存在；
- schema 声明 name 为 SuperSpec；
- schema 声明 version 为 4；
- artifact 链包含 brainstorm、proposal、specs、tasks、plan、apply、verify、finalize；
- 不存在明显下载失败或空目录情况。
```

### 停止条件

若上游 `schema.yaml` 不再是 version 4，或 artifact 链与本任务假设不一致：

```text
STOPPED: Upstream danielhanold/superspec schema differs from the reviewed version-4 baseline.
UPSTREAM_SUPERSPEC_COMMIT=<sha>
No schema files were copied into the project.
```

不得自行适配新版本。

---

## 10. 复制 Schema 到项目

### Step 5：复制前再次确认项目目标路径不存在

```powershell
Set-Location E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance
Test-Path openspec/schemas/superspec
```

若返回 `True`，停止，不得覆盖。

若返回 `False`，执行：

```powershell
New-Item -ItemType Directory -Force -Path openspec/schemas/superspec | Out-Null
Copy-Item -Recurse -Force `
  "E:/009workspace/claudecode/_tmp/superspec-upstream-phase1/openspec/schemas/superspec/*" `
  "openspec/schemas/superspec/"
```

### 复制规则

- 必须复制上游 `openspec/schemas/superspec/` 的完整内容；
- 不得选择性遗漏模板、README 或 INTEGRATION 文档；
- 不得改写 copied schema 或 templates 以适配本项目；
- 本项目专用约束应在后续通过 `openspec/config.yaml` 的 `context` / `rules` 处理，不应修改上游 schema 资产。

### Step 6：记录复制文件清单

```powershell
Get-ChildItem -Recurse openspec/schemas/superspec | Select-Object -ExpandProperty FullName
```

将结果完整记录进 Phase 1 报告。

---

## 11. 最小激活：修改 `openspec/config.yaml`

### Step 7：修改前读取并保存 diff 基线

```powershell
Get-Content openspec/config.yaml
```

### Step 8：仅修改 schema 字段

将配置中的：

```yaml
schema: spec-driven
```

替换为：

```yaml
schema: superspec
```

约束：

- 只允许修改这一行；
- 保留文件中其余注释、空行或模板内容；
- 本阶段不得新增 `context:`；
- 本阶段不得新增 `rules:`；
- 本阶段不得删除已有内容。

修改后执行：

```powershell
git diff -- openspec/config.yaml
```

确认 diff 仅为 schema 值变化。

### 停止条件

若配置文件存在除 `schema: spec-driven` 外的有效项目自定义内容，且 Codex 无法在仅替换 schema 字段的前提下安全完成修改，应停止并报告，不得覆盖文件。

---

## 12. Schema 识别与结构验证

### Step 9：允许执行的验证命令

在整改 worktree 根目录执行：

```powershell
openspec schemas
openspec validate
git status --short --branch --untracked-files=all
git diff --stat
git diff --name-only
```

若 `openspec validate` 的本地 CLI 需要特定参数，先执行：

```powershell
openspec validate --help
```

仅选择帮助信息明确表示为“验证当前项目全部已存在资产且不创建/修改文件”的等价验证命令；执行命令与理由必须写入报告。

### 验证要求

必须确认：

| 验证项 | 必须结果 |
|---|---|
| `openspec schemas` | 可识别项目级 `superspec` schema |
| 默认 config | `schema: superspec` |
| `openspec validate` | 通过，或明确记录非本阶段引入且阻塞激活的错误 |
| Schema 文件 | 完整复制且未本地改写 |
| 现有 `openspec/specs/` | 未被修改 |
| 现有 `openspec/changes/` | 未被修改 |
| 业务目录 | 未被修改 |

### 失败处理

若复制 schema 或切换 config 后验证失败：

- 不得自行删除、reset 或 restore 修改；
- 不得试图编辑 schema templates 修复；
- 在 Phase 1 报告中记为 `PARTIAL / BLOCKED`；
- 回传完整失败命令和错误输出，等待设计端判断。

---

## 13. 新增 Phase 1 执行报告

必须新增：

```text
docs/rectification/03-superspec-schema-installation-and-minimal-activation-report.md
```

### 报告模板

```markdown
# DiagnoseToolPy SuperSpec Phase 1 项目级 Schema 引入与最小激活报告

> 执行阶段：Phase 1
> 执行工具：Codex
> 执行日期：<YYYY-MM-DD>
> 整改工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`
> 整改分支：`chore/superspec-governance-migration`
> Phase 1 起始 HEAD：`<用户提交 Phase 0A/0B 后的新 HEAD>`
> 上游来源：`danielhanold/superspec`
> 上游 schema version：`4`
> 上游 commit：`<UPSTREAM_SUPERSPEC_COMMIT>`

## 1. 执行摘要

- 执行结果：PASS / PARTIAL / STOPPED
- 是否安装项目级 schema：
- 是否切换默认 schema：
- 是否建议进入 Phase 2：

## 2. 启动门禁验证

| 检查项 | 结果 | 证据摘要 |
|---|---|---|
| 当前 branch 为整改分支 | | |
| 起始 HEAD 已包含 Phase 0A/0B 提交 | | |
| 起始工作树 clean | | |
| `openspec/config.yaml` 原值为 `spec-driven` | | |
| `openspec/schemas/superspec/` 原本不存在 | | |
| 无 active OpenSpec change | | |
| 引入前 OpenSpec validate 基线 | | |

## 3. OpenSpec CLI 基线

- `openspec --version` 输出：
- `openspec schemas` 引入前输出摘要：
- `openspec validate` 引入前输出摘要：
- 若命令参数发生差异，说明处理方式：

## 4. 上游 Schema 来源核验

| 项目 | 结果 |
|---|---|
| 上游仓库 | `danielhanold/superspec` |
| Clone 目录 | `E:/009workspace/claudecode/_tmp/superspec-upstream-phase1` |
| 上游 commit SHA | |
| schema name | |
| schema version | |
| artifact 链核验 | |
| 是否与预期 v4 一致 | |

## 5. 引入的 Schema 文件清单

```text
<完整列出 openspec/schemas/superspec/ 下复制的文件>
```

确认：

- 文件从上游原样复制；
- 未进行项目定制改写；
- 定制化 context / rules 延期至 Phase 2。

## 6. `openspec/config.yaml` 最小修改

### 修改前

```yaml
<粘贴相关片段>
```

### 修改后

```yaml
<粘贴相关片段>
```

### Diff 结论

- 是否仅替换 `schema: spec-driven` → `schema: superspec`：
- 是否新增 context / rules：否
- 是否删除其他内容：否

## 7. 引入后验证结果

### `openspec schemas`

```text
<粘贴输出>
```

### `openspec validate` 或等价只读验证命令

```text
<粘贴输出>
```

### 验证结论

| 验证项 | PASS / FAIL | 说明 |
|---|---|---|
| 项目级 `superspec` schema 可识别 | | |
| 已有 living specs 保持有效 | | |
| 已归档 changes 保持有效 | | |
| schema/config 之外无项目文件被修改 | | |

## 8. 最终 Git 可见变更集合

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

### 新增未跟踪 Schema/报告文件

```text
<粘贴 git ls-files --others --exclude-standard openspec/schemas/superspec docs/rectification/03-* 输出>
```

## 9. 保护范围确认

- [ ] 未修改 `diagnose_tool/`
- [ ] 未修改 `frontend/`
- [ ] 未修改 `tests/`
- [ ] 未修改 `config/`
- [ ] 未修改 `data/`
- [ ] 未修改 `.claude/`
- [ ] 未修改 `.opencode/`
- [ ] 未修改 `AGENT.md` / `AGENTS.md` / `work-items/`
- [ ] 未修改 `openspec/specs/` 或 `openspec/changes/`
- [ ] 未执行 OpenSpec lifecycle 命令
- [ ] 未安装 Superpowers
- [ ] 未执行 commit / push / merge / reset / clean / stash / git add

## 10. Phase 2 准入结论

### 结论

- ALLOW / BLOCK

### Phase 2 预期内容

若允许进入 Phase 2，下一阶段仅处理：

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
```

---

## 14. 最终变更集合验收

### 14.1 本阶段结束时允许出现的文件变化

由于 Phase 0A/0B 已在启动前提交，Phase 1 结束时 Git 可见变更只允许包含：

```text
M  openspec/config.yaml
?? openspec/schemas/superspec/**
?? docs/rectification/03-superspec-schema-installation-and-minimal-activation-report.md
```

不得再次出现：

```text
AGENT.md
AGENTS.md
.gitignore
work-items/
docs/rectification/00-*
docs/rectification/01-*
docs/rectification/02-*
任何业务路径
任何工具专用目录
```

### 14.2 最终检查命令

执行：

```powershell
git status --short --branch --untracked-files=all
git diff --stat
git diff --name-only
git ls-files --others --exclude-standard openspec/schemas/superspec docs/rectification/
git diff -- openspec/config.yaml
```

### 必须停止并报告的情况

若最终集合出现任何不在允许列表中的路径：

```text
BLOCKED: Phase 1 produced out-of-scope changes.
Unexpected paths:
- <path>
No cleanup/reset was performed; manual review is required.
```

---

## 15. Codex 回传要求

执行完成后，必须回传：

1. `docs/rectification/03-superspec-schema-installation-and-minimal-activation-report.md`；
2. Phase 1 启动时的新基线 HEAD；
3. OpenSpec CLI 版本与引入前验证结果；
4. 上游 SuperSpec commit SHA 与 schema version 核验结果；
5. 复制到 `openspec/schemas/superspec/` 的完整文件清单；
6. `openspec/config.yaml` 的精确 diff；
7. `openspec schemas` 与 `openspec validate` 的执行结果；
8. `git status --short --branch --untracked-files=all`；
9. `git diff --stat`；
10. `git diff --name-only`；
11. 新增未跟踪 schema / 报告文件的展开列表；
12. 是否允许进入 Phase 2；
13. 未修改禁止路径、未执行禁止命令的确认。

---

## 16. 提交策略

Codex 不得提交本阶段变更。

若 Phase 1 回传结论为 `PASS`，由用户在人工审查以下文件后提交：

```text
openspec/config.yaml
openspec/schemas/superspec/**
docs/rectification/03-superspec-schema-installation-and-minimal-activation-report.md
```

建议提交信息：

```text
chore(openspec): install superspec schema v4
```

提交后，用户需将新的 HEAD 回传，作为 Phase 2 任务书的基线。

---

## 17. 参考来源

本任务书以以下上游文档为设计依据：

1. `danielhanold/superspec` README：该项目为 OpenSpec 与 Superpowers 的 custom schema 集成；当前文档声明 schema version 4；官方安装步骤包含复制 `openspec/schemas/superspec/`、设置默认 schema、执行 `openspec schemas` 与 `openspec validate`。
2. `danielhanold/superspec` `openspec/schemas/superspec/schema.yaml`：v4 artifact 链、apply/verify/finalize 依赖与执行语义。
3. `Fission-AI/OpenSpec` 官方 customization 文档：项目级 custom schemas 应位于 `openspec/schemas/`；`openspec/config.yaml` 用于设置默认 schema，并可在后续阶段注入 context/rules。

本阶段遵循“上游 schema 原样引入、本项目约束通过后续配置注入”的策略，避免产生无法跟踪的 schema fork。
