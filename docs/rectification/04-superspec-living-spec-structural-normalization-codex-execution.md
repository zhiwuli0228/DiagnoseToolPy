# DiagnoseToolPy 全面适配 SuperSpec：Phase 1A 存量 Living Specs 结构兼容修复执行任务书

> **交付对象**：Codex  
> **执行阶段**：Phase 1A — Living Spec Structural Compatibility Normalization  
> **前置阶段**：Phase 1 项目级 SuperSpec schema 引入与最小激活已执行，但验证为 `PARTIAL`  
> **执行工作区**：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> **执行分支**：`chore/superspec-governance-migration`  
> **Phase 1 起始 HEAD**：`365c9a6e1c0f1df675a325a4127ade9c8aba4222`  
> **上游 SuperSpec Commit**：`e1c8f417ee3601208416d988ba3b37d83ddb63f2`  
> **Schema Version**：`4`  
> **本阶段性质**：在尚未提交的 Phase 1 变更集合上修复存量 living specs 的结构兼容性；不得修改业务代码；不得进入项目 context/rules 注入阶段

---

## 1. 当前结论与执行策略

### 1.1 Phase 1 当前状态

Phase 1 已完成以下工作：

```text
- 官方 `danielhanold/superspec` schema version 4 已复制至：
  openspec/schemas/superspec/

- `openspec/config.yaml` 已从：
  schema: spec-driven

  最小切换为：
  schema: superspec

- `openspec schemas` 已能识别：
  superspec (project)
```

但 Phase 1 未通过最终门禁：

```text
openspec validate --all --json
→ 5 passed, 6 failed
```

失败 living specs：

```text
openspec/specs/basic-case-retrieval/spec.md
openspec/specs/casebase-file-storage/spec.md
openspec/specs/docker-deployment/spec.md
openspec/specs/evidence-report-generation/spec.md
openspec/specs/manual-case-creation/spec.md
openspec/specs/react-frontend-shell/spec.md
```

Codex 回传的失败原因：

```text
缺少 `## Purpose` 或 `## Requirements` 章节。
```

### 1.2 正确处理方式

当前不得：

```text
- 提交 Phase 1 的半完成状态；
- 回退已复制的 schema；
- 将 `openspec/config.yaml` 切回 `spec-driven` 以绕开验证；
- 进入 Phase 2 配置 context / rules；
- 通过修改 schema template 降低校验标准；
- 修改业务代码来“匹配”文档。
```

正确处理方式是：

```text
保留 Phase 1 待提交变更
→ 仅对 6 个失败 living specs 做结构归一化
→ 确保原有行为合同语义不变
→ 再次运行 openspec validate --all --json
→ 若全部通过，将 Phase 1 + Phase 1A 合并为同一次人工提交
```

---

## 2. 判定依据

### 2.1 Living specs 的职责

OpenSpec 的 `openspec/specs/` 是当前系统行为的 source of truth。它描述已经成立的系统能力，不是一次 change 的临时产物。

Living specs 的标准结构应具备：

```markdown
# <Capability Name>

## Purpose

<该 capability 的目的与边界。>

## Requirements

### Requirement: <Requirement Name>

系统 SHALL/MUST ...

#### Scenario: <Scenario Name>

- WHEN ...
- THEN ...
```

### 2.2 SuperSpec 对校验的要求

`danielhanold/superspec` v4 的 `verify` artifact 明确要求执行：

```bash
openspec validate --all --json
```

并确认每个项目 item 返回有效结果；任何结构校验失败都必须先修复 underlying artifact，不能绕过后继续 finalize / archive。

因此，本阶段的目标不是新增业务能力，而是让现有行为合同满足未来 SuperSpec 验证链路所依赖的结构门禁。

### 2.3 本阶段的语义保护原则

本阶段修改的是 **spec 文档结构**，不得改变 **系统承诺的行为含义**。

严格原则：

```text
- 可以新增 `## Purpose` 标题和从既有内容提炼出的简短目的陈述；
- 可以新增 `## Requirements` 容器标题；
- 可以移动既有 requirement/scenario 内容到正确章节下；
- 可以将明显已有的行为表述格式化为 SHALL/MUST 规范句，仅当语义完全等价；
- 不得新增产品能力；
- 不得删除既有能力；
- 不得扩大输入、输出、错误处理、部署或 UI 行为；
- 不得根据代码推断并写入新合同；
- 不得修改通过校验的 5 个 living specs 以“统一风格”；
- 不得修改 archived changes 或生成新的 change。
```

---

## 3. 本阶段目标

本阶段必须完成：

1. 验证当前 worktree 仍保持 Phase 1 回传所描述的待提交变更集合。
2. 读取 `openspec validate --all --json` 的完整当前失败结果。
3. 读取 6 个失败 living specs 的原始内容，并读取通过验证的 living specs 作为格式参考。
4. 对每个失败 spec 判断：
   - 是否仅缺少章节结构；
   - 是否具备足够现有内容进行无语义变化的结构修复；
   - 是否存在无法安全归一化的行为歧义。
5. 仅修改可以安全归一化的失败 living specs。
6. 再次执行 `openspec validate --all --json`。
7. 生成 Phase 1A 执行报告，记录每个 spec 的结构变化与语义保护结论。
8. 若全部 specs 通过验证，输出允许用户将 Phase 1 + Phase 1A 一并提交的结论。

---

## 4. 严格允许范围

### 4.1 允许读取的项目路径

允许读取：

```text
openspec/config.yaml
openspec/schemas/superspec/**
openspec/specs/**
openspec/changes/archive/**             # 仅用于确认现有 spec 来源；不得修改
docs/rectification/00-*
docs/rectification/01-*
docs/rectification/02-*
docs/rectification/03-*
AGENTS.md                               # 仅核对保护约束
docs/README.md                          # 仅核对文档路由
docs/03-openspec/spec-rule.md           # 若存在，仅作为旧规范参考
```

### 4.2 允许修改的既有项目文件

仅允许修改以下 6 个已验证失败的 living specs：

```text
openspec/specs/basic-case-retrieval/spec.md
openspec/specs/casebase-file-storage/spec.md
openspec/specs/docker-deployment/spec.md
openspec/specs/evidence-report-generation/spec.md
openspec/specs/manual-case-creation/spec.md
openspec/specs/react-frontend-shell/spec.md
```

### 4.3 允许新增的文件

仅允许新增：

```text
docs/rectification/04-living-spec-structural-normalization-for-superspec-report.md
```

### 4.4 本阶段允许保留但不得再次修改的 Phase 1 待提交变更

以下文件/目录已由 Phase 1 产生，本阶段允许继续存在于 Git 变更集合中，但不得修改其内容：

```text
openspec/config.yaml
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

> `openspec/config.yaml` 在 Phase 1 已经变更为 `schema: superspec`。本阶段必须保留该变更，不得二次编辑、补充 `context` 或 `rules`。

---

## 5. 严格禁止范围

### 5.1 禁止修改的路径

严禁新增、修改、移动、删除或格式化：

```text
.gitignore
AGENT.md
AGENTS.md
work-items/
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
docs/rectification/00-*
docs/rectification/01-*
docs/rectification/02-*
docs/rectification/03-*
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
openspec/changes/
openspec/schemas/superspec/**
```

除第 4.2 节列出的 6 个失败 specs 外，严禁修改其他 living specs，包括当前已通过验证的：

```text
openspec/specs/project-skeleton/spec.md
openspec/specs/server-directory-scan/spec.md
openspec/specs/log-reader-and-multiline/spec.md
openspec/specs/header-parser-and-classifier/spec.md
openspec/specs/settings-config-api/spec.md
openspec/specs/settings-page-ui/spec.md
```

> 实际通过项以当前 `openspec validate --all --json` 输出为准。若通过项名称与上表不同，不得擅自修改；只在报告中记录实际列表。

### 5.2 禁止执行的 Git 操作

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

### 5.3 禁止执行的 OpenSpec / Agent 操作

严禁：

```bash
openspec init
openspec update
openspec config set
openspec config profile
openspec schema init
openspec schema fork
任何 /opsx:* 或 opsx-* lifecycle 命令
任何 Superpowers skill 或安装命令
```

本阶段只允许执行第 10 节明确列出的 OpenSpec 校验与只读查询命令。

---

## 6. 启动门禁：验证当前仍为 Phase 1 待修复状态

在整改 worktree 中执行：

```powershell
Set-Location E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance

git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git diff --name-only
git diff -- openspec/config.yaml
openspec --version
openspec schemas
openspec validate --all --json
```

### 6.1 必须满足

```text
当前分支：chore/superspec-governance-migration
当前 HEAD：365c9a6e1c0f1df675a325a4127ade9c8aba4222
OpenSpec 版本：1.3.1，或与 Phase 1 相同
默认 schema：openspec/config.yaml 中仅由 Phase 1 修改为 `schema: superspec`
项目 schema：openspec schemas 可识别 `superspec (project)`
当前验证失败项：与 Phase 1 报告中的 6 个 living specs 一致
```

启动时允许存在的 Phase 1 待提交变更必须仅为：

```text
M  openspec/config.yaml
?? docs/rectification/03-superspec-schema-installation-and-minimal-activation-report.md
?? openspec/schemas/superspec/**
```

### 6.2 必须停止的条件

若出现以下任一情况，停止执行，不做 spec 修改：

| 情况 | 停止原因 |
|---|---|
| 当前 HEAD 不等于 Phase 1 起始 HEAD | Phase 1 待提交状态可能已被提交或改写 |
| 当前 schema 不再是 `superspec` | 当前问题上下文已变化 |
| Phase 1 schema 文件缺失或内容出现额外变更 | 不能建立稳定兼容修复基线 |
| `openspec validate --all --json` 的失败集合不再是报告中的 6 项 | 需要重新分析失败范围 |
| 除 Phase 1 允许集合外出现其他变更 | 发生范围外修改 |

停止回传：

```text
STOPPED: Phase 1 pending-change baseline no longer matches the approved structural-remediation starting state.
No living spec files were modified.
```

---

## 7. 修复前内容核验

### 7.1 读取失败 spec 原文

读取并在报告中摘要记录六个失败文件的原始结构：

```powershell
Get-Content openspec/specs/basic-case-retrieval/spec.md
Get-Content openspec/specs/casebase-file-storage/spec.md
Get-Content openspec/specs/docker-deployment/spec.md
Get-Content openspec/specs/evidence-report-generation/spec.md
Get-Content openspec/specs/manual-case-creation/spec.md
Get-Content openspec/specs/react-frontend-shell/spec.md
```

对每个文件记录：

| 检查项 | 记录内容 |
|---|---|
| 当前顶级标题 | 原文标题 |
| 是否已有 Purpose 类文字但标题错误 | 是/否，位置 |
| 是否已有 Requirements 类内容但标题错误或缺失 | 是/否，位置 |
| 是否已有 `### Requirement:` | 数量 |
| 是否已有 `#### Scenario:` | 数量 |
| 是否已有 SHALL/MUST 行为陈述 | 是/否 |
| 是否可仅靠结构归一化修复 | 是/否 |

### 7.2 读取通过的 spec 作为本项目格式参考

从当前验证通过项中选择至少两个最贴近失败能力的 living specs 读取，只用于观察结构格式，不得修改，例如：

```powershell
Get-Content openspec/specs/server-directory-scan/spec.md
Get-Content openspec/specs/log-reader-and-multiline/spec.md
```

若上述文件并非验证通过项，则改为读取 `openspec validate --all --json` 中实际通过的两个 spec。

### 7.3 无法安全修复时必须停止

若任意失败 spec 满足以下任一情况：

```text
- 文件基本为空；
- 只有任务/实现描述，没有可识别的行为合同；
- 原文彼此矛盾；
- 为增加 `## Purpose` 或 `## Requirements` 必须发明新的产品行为；
- 现有 requirement/scenario 无法判断归属；
- 修复将不可避免地改变用户可见行为、错误处理或部署契约；
```

则：

- 不修改任何 living spec；
- 输出停止报告，列出歧义；
- 等待设计端提供行为合同决策。

停止结论：

```text
BLOCKED: One or more living specs cannot be structurally normalized without inventing or changing behavioral contracts.
```

---

## 8. 结构归一化规则

仅当第 7 节确认六个 spec 均可安全归一化时，执行修改。

### 8.1 标准目标结构

每个修改后的 living spec 必须符合：

```markdown
# <Capability Title>

## Purpose

<一段简短文字：该 capability 解决什么问题、服务什么已存在能力。必须来自原有内容的等价概括。>

## Requirements

### Requirement: <Existing Requirement Name>

<原有或语义等价的规范性行为陈述，使用 SHALL 或 MUST。>

#### Scenario: <Existing Scenario Name>

- WHEN <existing condition>
- THEN <existing expected outcome>
```

### 8.2 允许的结构修复类型

| 修复类型 | 是否允许 | 要求 |
|---|---:|---|
| 增加 `## Purpose` 标题 | 是 | 内容只能等价总结已有能力 |
| 增加 `## Requirements` 标题 | 是 | 作为原 requirement 集合容器 |
| 将已有 requirements 移动到 `## Requirements` 下 | 是 | 文本与含义不改变 |
| 将已有 Purpose 文案移动至标准位置 | 是 | 文本可仅做格式性整理 |
| 统一 Requirement / Scenario 标题层级 | 是 | 不更改行为语义 |
| 将已有明确规范句从普通文字改为 SHALL/MUST | 谨慎允许 | 仅当义务强度本来已明确，不得升级可选行为为强制行为 |
| 新增行为 requirement | 否 | 超出结构迁移 |
| 新增未在原文表达的场景 | 否 | 超出结构迁移 |
| 删除 requirement/scenario | 否 | 改变行为合同 |
| 合并或拆分导致语义变化 | 否 | 超出结构迁移 |
| 根据代码、README 或猜测补充行为 | 否 | 应另建 change |

### 8.3 Purpose 的写法约束

如果原文件没有显式 Purpose 段，但从文件标题与已有 requirements 可以无歧义地归纳目的，允许新增一段**不引入新要求**的 Purpose。

例：

```markdown
## Purpose

This specification defines the existing behavior for retrieving stored diagnostic cases using the project's supported retrieval mechanism.
```

不允许写入：

```markdown
## Purpose

This specification introduces semantic vector search, reranking, and LLM-based recommendations.
```

除非原 spec 已明确承诺上述行为。

### 8.4 Requirements 的写法约束

若已有 requirements/scenarios 内容完整，仅需增加：

```markdown
## Requirements
```

并调整标题层级。

若原文件存在行为描述但没有标准 Requirement 标题，只有在该描述本身已经清晰表达现有合同义务时，才可用等价标题包裹它。

---

## 9. 文件级执行要求

必须对每个文件形成“修改前 → 修改后 → 语义不变依据”的记录。

### 9.1 `basic-case-retrieval`

```text
允许动作：
- 增加缺失标准章节；
- 规范已有检索行为 requirement/scenario 的章节结构。

禁止动作：
- 引入新的向量检索、rerank、embedding、LLM 诊断行为；
- 改变现有检索结果或排序承诺；
- 改变存储/索引职责边界。
```

### 9.2 `casebase-file-storage`

```text
允许动作：
- 规范已有文件存储行为的 Purpose / Requirements 层级。

禁止动作：
- 引入数据库；
- 引入新的目录布局或持久化格式；
- 改变文件作为 durable source of truth 的既有含义。
```

### 9.3 `docker-deployment`

```text
允许动作：
- 规范现有容器部署行为结构。

禁止动作：
- 增加新的部署目标、镜像发布流程、权限要求或基础设施依赖；
- 改变网络、挂载或运行约束。
```

### 9.4 `evidence-report-generation`

```text
允许动作：
- 规范已有证据报告生成行为结构。

禁止动作：
- 新增报告格式、AI 总结、上传能力或导出承诺；
- 改变证据包字段或生命周期。
```

### 9.5 `manual-case-creation`

```text
允许动作：
- 规范人工创建案例的既有行为结构。

禁止动作：
- 扩大编辑、审批、版本管理或权限行为；
- 修改 casebase 持久化契约。
```

### 9.6 `react-frontend-shell`

```text
允许动作：
- 规范既有前端壳能力的行为结构。

禁止动作：
- 新增页面、交互、路由、视觉要求或 E2E 测试行为；
- 将后续 AI 诊断 UI 设计写入现有合同。
```

---

## 10. 允许执行的验证命令

### 10.1 修复前基线验证

```powershell
openspec validate --all --json
```

必须将完整输出保存到 Phase 1A 报告摘要中，至少记录：

- passed 数量；
- failed 数量；
- 失败 capability；
- 每个失败的结构问题。

### 10.2 修复后验证

完成 6 个文件结构修复后执行：

```powershell
openspec validate --all --json
openspec validate --all
openspec schemas
git status --short --branch --untracked-files=all
git diff --stat
git diff --name-only
git diff -- openspec/config.yaml
git diff -- openspec/specs/basic-case-retrieval/spec.md
git diff -- openspec/specs/casebase-file-storage/spec.md
git diff -- openspec/specs/docker-deployment/spec.md
git diff -- openspec/specs/evidence-report-generation/spec.md
git diff -- openspec/specs/manual-case-creation/spec.md
git diff -- openspec/specs/react-frontend-shell/spec.md
git ls-files --others --exclude-standard openspec/schemas/superspec docs/rectification/
```

### 10.3 必须达到的验证结果

| 验证项 | 必须结果 |
|---|---|
| `openspec schemas` | 继续识别 `superspec (project)` |
| `openspec validate --all --json` | 所有 items `valid: true`；0 failed |
| `openspec validate --all` | 全部通过 |
| `openspec/config.yaml` | 仍只有 Phase 1 的 schema 值变化 |
| schema 文件 | 仍为 Phase 1 上游复制资产，未被修改 |
| 6 个 failed specs | 仅结构与等价表述修复 |
| 其他 specs | 无修改 |
| 业务路径 | 无修改 |
| 工具资产 | 无修改 |

### 10.4 验证失败处理

若修复后仍有校验失败：

- 不得继续修改更多未授权文件；
- 不得通过编辑 schema 降低门禁；
- 不得提交；
- 在报告中标记 `PARTIAL / BLOCKED`；
- 回传失败内容和已修改 specs 的 diff，由设计端继续决策。

---

## 11. 新增 Phase 1A 报告

必须新增：

```text
docs/rectification/04-living-spec-structural-normalization-for-superspec-report.md
```

### 11.1 报告模板

```markdown
# DiagnoseToolPy SuperSpec Phase 1A 存量 Living Specs 结构兼容修复报告

> 执行阶段：Phase 1A
> 执行工具：Codex
> 执行日期：<YYYY-MM-DD>
> 整改工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`
> 整改分支：`chore/superspec-governance-migration`
> Phase 1 起始 HEAD：`365c9a6e1c0f1df675a325a4127ade9c8aba4222`
> 上游 SuperSpec Commit：`e1c8f417ee3601208416d988ba3b37d83ddb63f2`
> Schema Version：`4`

## 1. 执行摘要

- 执行结果：PASS / PARTIAL / BLOCKED / STOPPED
- Phase 1 原结论：PARTIAL
- 本阶段目标：修正切换 SuperSpec 后暴露的现有 living specs 结构校验失败
- 是否改变系统行为合同：否 / 是（若为是则必须 BLOCK）
- 是否建议提交 Phase 1 + Phase 1A 统一变更：是 / 否
- 是否允许进入 Phase 2：是 / 否

## 2. 启动状态验证

| 检查项 | 结果 | 说明 |
|---|---|---|
| 当前 branch | | |
| 当前 HEAD | | |
| 默认 schema 为 `superspec` | | |
| `superspec (project)` 可识别 | | |
| Phase 1 待提交变更集合符合预期 | | |
| 修复前 validate 失败集合与 Phase 1 一致 | | |

## 3. 修复前验证失败结果

### `openspec validate --all --json` 摘要

- Passed：
- Failed：

| Capability | 错误信息 | 是否仅为结构问题 | 是否可安全修复 |
|---|---|---:|---:|
| `basic-case-retrieval` | | | |
| `casebase-file-storage` | | | |
| `docker-deployment` | | | |
| `evidence-report-generation` | | | |
| `manual-case-creation` | | | |
| `react-frontend-shell` | | | |

## 4. 通过项格式参考

| 参考 spec | 被参考的结构要点 | 是否修改 |
|---|---|---:|
| `<path>` | `## Purpose` / `## Requirements` / requirement/scenario 层级 | 否 |
| `<path>` | `## Purpose` / `## Requirements` / requirement/scenario 层级 | 否 |

## 5. 文件级结构迁移记录

### 5.1 `basic-case-retrieval`

- 原始结构摘要：
- 修改内容：
- 是否新增 `## Purpose`：
- 是否新增/调整 `## Requirements`：
- Requirement / Scenario 数量变化：
- 语义未变化依据：
- 明确未新增的能力：

### 5.2 `casebase-file-storage`

- 原始结构摘要：
- 修改内容：
- 是否新增 `## Purpose`：
- 是否新增/调整 `## Requirements`：
- Requirement / Scenario 数量变化：
- 语义未变化依据：
- 明确未新增的能力：

### 5.3 `docker-deployment`

- 原始结构摘要：
- 修改内容：
- 是否新增 `## Purpose`：
- 是否新增/调整 `## Requirements`：
- Requirement / Scenario 数量变化：
- 语义未变化依据：
- 明确未新增的能力：

### 5.4 `evidence-report-generation`

- 原始结构摘要：
- 修改内容：
- 是否新增 `## Purpose`：
- 是否新增/调整 `## Requirements`：
- Requirement / Scenario 数量变化：
- 语义未变化依据：
- 明确未新增的能力：

### 5.5 `manual-case-creation`

- 原始结构摘要：
- 修改内容：
- 是否新增 `## Purpose`：
- 是否新增/调整 `## Requirements`：
- Requirement / Scenario 数量变化：
- 语义未变化依据：
- 明确未新增的能力：

### 5.6 `react-frontend-shell`

- 原始结构摘要：
- 修改内容：
- 是否新增 `## Purpose`：
- 是否新增/调整 `## Requirements`：
- Requirement / Scenario 数量变化：
- 语义未变化依据：
- 明确未新增的能力：

## 6. 修复后验证结果

### `openspec validate --all --json`

```text
<粘贴输出摘要或关键输出>
```

### `openspec validate --all`

```text
<粘贴输出>
```

### `openspec schemas`

```text
<粘贴输出>
```

| 验证项 | PASS / FAIL | 说明 |
|---|---|---|
| 0 个结构校验失败 | | |
| `superspec (project)` 仍可识别 | | |
| schema/config 未被本阶段额外改写 | | |
| living spec 修改仅发生在授权 6 项 | | |
| 无业务或工具资产修改 | | |

## 7. 完整待提交集合

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

### 未跟踪 Schema/报告文件

```text
<粘贴输出>
```

## 8. 保护范围确认

- [ ] 未修改 `diagnose_tool/`
- [ ] 未修改 `frontend/`
- [ ] 未修改 `tests/`
- [ ] 未修改 `config/`
- [ ] 未修改 `data/`
- [ ] 未修改 `.claude/`
- [ ] 未修改 `.opencode/`
- [ ] 未修改 `AGENT.md` / `AGENTS.md` / `work-items/`
- [ ] 未修改 `openspec/changes/`
- [ ] 未修改 `openspec/schemas/superspec/**`
- [ ] 未修改除授权 6 项以外的 `openspec/specs/**`
- [ ] 未追加 `openspec/config.yaml` 的 `context` 或 `rules`
- [ ] 未执行 lifecycle 命令、Superpowers 安装或业务实现
- [ ] 未执行 commit / push / merge / reset / clean / stash / git add

## 9. 提交与 Phase 2 准入建议

### 当前结论

- 是否建议用户提交 Phase 1 + Phase 1A：ALLOW / BLOCK
- 是否允许进入 Phase 2：ALLOW / BLOCK

### 若 ALLOW，建议提交范围

```text
openspec/config.yaml
openspec/schemas/superspec/**
openspec/specs/basic-case-retrieval/spec.md
openspec/specs/casebase-file-storage/spec.md
openspec/specs/docker-deployment/spec.md
openspec/specs/evidence-report-generation/spec.md
openspec/specs/manual-case-creation/spec.md
openspec/specs/react-frontend-shell/spec.md
docs/rectification/03-superspec-schema-installation-and-minimal-activation-report.md
docs/rectification/04-living-spec-structural-normalization-for-superspec-report.md
```

### 建议 commit message

```text
chore(openspec): install superspec schema and normalize living specs
```

### Phase 2 预期范围

```text
- 为 openspec/config.yaml 注入精简项目 context；
- 为 SuperSpec artifact 类型注入项目级规则；
- 明确 config 注入规则与 docs/AGENTS.md 的引用关系；
- 不修改上游 schema templates；
- 不修改业务代码。
```
```

---

## 12. 最终待提交文件集合门禁

### 12.1 若本阶段成功，允许存在的最终变更

最终 Git 可见变更只允许由以下内容组成：

```text
M  openspec/config.yaml

M  openspec/specs/basic-case-retrieval/spec.md
M  openspec/specs/casebase-file-storage/spec.md
M  openspec/specs/docker-deployment/spec.md
M  openspec/specs/evidence-report-generation/spec.md
M  openspec/specs/manual-case-creation/spec.md
M  openspec/specs/react-frontend-shell/spec.md

?? openspec/schemas/superspec/**
?? docs/rectification/03-superspec-schema-installation-and-minimal-activation-report.md
?? docs/rectification/04-living-spec-structural-normalization-for-superspec-report.md
```

### 12.2 严禁出现的最终变更

不得出现：

```text
AGENT.md
AGENTS.md
.gitignore
work-items/
docs/rectification/00-*
docs/rectification/01-*
docs/rectification/02-*
openspec/changes/**
openspec/schemas/superspec/** 的 modified 状态
任何业务、测试、数据、工具专用或开发文档路径
```

> `openspec/schemas/superspec/**` 应保持为本轮新增未跟踪文件；若某 schema 文件相对于复制状态被项目定制编辑，必须标记为越界。

---

## 13. Codex 回传要求

执行结束后，必须回传：

1. `docs/rectification/04-living-spec-structural-normalization-for-superspec-report.md`；
2. 启动时 `openspec validate --all --json` 的失败摘要；
3. 六个 living specs 的修复前结构判断；
4. 六个 living specs 的文件级 diff 摘要，尤其是 Purpose/Requirements 与 requirement/scenario 数量是否变化；
5. 明确的“未改变行为合同”确认，或发现无法确认时的阻塞说明；
6. 修复后 `openspec validate --all --json` 与 `openspec validate --all` 输出；
7. `openspec schemas` 输出；
8. 最终 `git status --short --branch --untracked-files=all`；
9. `git diff --stat`；
10. `git diff --name-only`；
11. 新增未跟踪 schema / 报告文件展开列表；
12. 是否允许用户提交 Phase 1 + Phase 1A；
13. 是否允许进入 Phase 2；
14. 未修改禁止路径、未执行禁止命令的明确确认。

---

## 14. 用户后续提交规则

Codex 不得提交本阶段变更。

只有当 Codex 报告同时满足：

```text
- openspec validate --all --json：0 failed；
- 六个 living specs 仅做结构兼容修复，未改变行为合同；
- 最终变更集合完全位于允许范围；
- Phase 1A 报告结论为 ALLOW；
```

用户才可人工审查并提交 Phase 1 + Phase 1A 的统一变更。

推荐人工提交命令（仅供用户执行，Codex 不得执行）：

```bash
git add openspec/config.yaml openspec/schemas/superspec/ openspec/specs/ docs/rectification/03-superspec-schema-installation-and-minimal-activation-report.md docs/rectification/04-living-spec-structural-normalization-for-superspec-report.md
git commit -m "chore(openspec): install superspec schema and normalize living specs"
```

提交完成后，用户应回传新的 HEAD 及 clean status，作为 Phase 2 的输入基线。

---

## 15. 后续阶段预告

Phase 1A 通过并提交后，下一阶段将进入：

```text
Phase 2：DiagnoseToolPy 项目 Context 与 SuperSpec Artifact Rules 注入
```

Phase 2 将处理：

```text
openspec/config.yaml:
- 精简 project context
- brainstorm / proposal / design / specs / tasks / plan / apply / verify / finalize 规则

治理目标：
- 让规则不再只存在于 docs/AGENTS.md 中等待 Agent 主动读取；
- 避免把大量 docs 内容全量塞入上下文；
- 建立 capability → authoritative docs 的路由策略。
```

Phase 2 仍不修改业务代码，也不修改上游 SuperSpec schema templates。
