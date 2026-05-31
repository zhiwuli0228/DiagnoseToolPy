# DiagnoseToolPy SuperSpec Phase 3A 仓库级执行策略与 Schema 安全覆盖设计审计报告

> 执行阶段：Phase 3A  
> 执行工具：Codex（治理审计与设计报告执行端）  
> 执行日期：2026-05-31  
> 整改工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 整改分支：`chore/superspec-governance-migration`  
> Phase 3 基线 HEAD：`53ea31d172218c240d2685b921763577ea963704`  
> 本阶段性质：仅做仓库级执行策略与 schema 安全覆盖设计审计，不安装工具、不执行 apply/finalize、不修改 schema 或业务代码

## 1. 执行摘要

- Phase 3A 设计审计执行结果：`PASS（设计审计报告已完成）`
- Phase 3 执行就绪判定：仍为 `NOT READY`
- 推荐适配路线：**方案 A**
- 是否允许安装或运行 Superpowers：`否`
- 是否允许执行真实业务 SuperSpec apply：`否`
- 是否允许执行 SuperSpec finalize：`否`
- 是否允许进入下一项 schema/rule 整改实施阶段：`待 ChatGPT 人工审核`

结论摘要：

- `superspec` canonical `apply/finalize` 的自动化语义仍与本项目的人工 Git 安全原则冲突。
- 当前最安全、最可实施的路线是保留 upstream 来源与版本追踪，但在项目本地 schema 中实施安全覆盖，先把高风险自动行为改成带人工门禁的受控行为。
- Superpowers 不应在本阶段被安装或运行；应在安全覆盖设计落地之后，再做独立、只读、隔离式验证。

## 2. Phase 3 NOT READY 结论承接与本阶段边界

Phase 3 审计结论已经明确：审计任务完成，但执行就绪仍为 `NOT READY`。根因不是单纯缺少安装命令，而是 upstream `superspec` canonical 行为与本项目当前治理基线存在未消解冲突：

- `apply` 依赖 `superpowers:*` skills、`git worktrees` 与 `subagent-driven-development`。
- `finalize` 会自动执行 merge、push、PR comment 与 worktree cleanup。
- 本项目当前仍要求真实业务实现、人审边界和 Git 写操作必须先得到明确批准。

本阶段不改变上述判定，只给出下一阶段的安全覆盖设计蓝图。

## 3. Phase 2/3 基线提交与工作区洁净性核验

### 3.1 只读核验结果

```text
git branch --show-current
chore/superspec-governance-migration

git rev-parse HEAD
53ea31d172218c240d2685b921763577ea963704

git status --short --branch --untracked-files=all
## chore/superspec-governance-migration...origin/chore/superspec-governance-migration
```

### 3.2 当前跟踪集合

```text
git ls-files -- openspec/config.yaml docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md docs/rectification/07-superspec-config-gate-syntax-fix-report.md docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md docs/rectification/09-superspec-phase2-final-gate-correction-and-admission-closure-report.md docs/rectification/10-superspec-phase3-execution-readiness-and-safety-gate-audit-report.md
openspec/config.yaml
docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
docs/rectification/07-superspec-config-gate-syntax-fix-report.md
docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md
docs/rectification/09-superspec-phase2-final-gate-correction-and-admission-closure-report.md
docs/rectification/10-superspec-phase3-execution-readiness-and-safety-gate-audit-report.md
```

### 3.3 结论

- 当前分支正确。
- 工作区开始时干净。
- `openspec/config.yaml` 与 `05-*` 至 `10-*` 报告均已进入当前 HEAD。
- `openspec/config.yaml` 中的 Phase 3 阻断文本仍然存在。

## 4. 当前工具职责基线与仓库级 Execution Policy

### 4.1 工具职责基线

| 工作 | 责任工具 | 说明 |
|---|---|---|
| 需求分析、方案设计、执行文档输出 | ChatGPT / Codex | 负责分析、设计、审计与受控报告输出 |
| 治理整改执行与证据生成 | Codex | 仅在受控范围内执行治理任务，不自动升格为业务实现端 |
| 未来真实业务代码实现主端 | Claude Code | 作为后续业务实现主端，需要单独批准其接入路径 |
| 设计阶段兼容 / 备用实现端 | opencode | 只保留兼容与必要时替代的设计位，不默认启用 |

### 4.2 仓库级 Execution Policy

1. 设计阶段由 ChatGPT / Codex 负责，输出 proposal/spec/design/tasks/plan 等治理文档。
2. 真实业务实现由用户批准的实现端执行，当前推荐主端为 Claude Code。
3. opencode 仅作为设计阶段兼容或必要时替代端，不应默认获得高风险自动 closeout 权限。
4. Codex 在本仓库仅适合承担治理审计、设计审计与执行证据闭合，不应自动成为业务实现主端。
5. apply 前、verify 后、finalize 前都必须有明确的人审门禁；未批准时不得进入下一步。

## 5. SuperSpec Schema 高风险行为精确定位

### 5.1 `openspec/config.yaml` 中当前阻断文本

当前 `openspec/config.yaml` 仍保留 Phase 3 阻断文本：

- `rules.apply` 末项：`Do not execute real business implementation through SuperSpec apply until Phase 3 approves the implementation tool, Superpowers availability, worktree behavior, review discipline, and Git-safety prerequisites for this repository.`
- `rules.finalize` 末项：`Do not execute Git/PR closeout through SuperSpec finalize until Phase 3 approves repository-specific merge, push, worktree cleanup, and pull-request safety prerequisites.`

### 5.2 高风险节点定位

`openspec/schemas/superspec/schema.yaml` 中与高风险行为相关的节点如下：

| 文件 / 节点 | 关键行为摘要 | 风险 |
|---|---|---|
| `schema.yaml` 顶层描述（约 5-18 行） | 明确 `brainstorm → proposal → specs → tasks → plan → apply → verify → finalize`，并说明 `apply` 依赖 worktrees + subagent-driven-development，`finalize` 会直接执行 git-side closeout | canonical 流程默认包含高风险自动化 |
| `artifacts[id=brainstorm]` / `artifacts[id=plan]` | 明确要求使用 `superpowers:brainstorming`、`superpowers:writing-plans` | 依赖 Superpowers，当前无可验证可用证据 |
| `artifacts[id=apply]` | 说明 `/opsx:apply` 是生成 `apply.md` 的入口，且为实现阶段 receipt；顶层 `apply:` phase block 在底部定义真正的执行逻辑 | 容易把 receipt 与真实实现混为一体 |
| `apply` 顶层 phase block（约 638-768 行） | 说明 create worktree、subagent-driven-development、TDD、requesting-code-review、executing-plans fallback、verify 后再继续 | 会把治理流程推向真实实现自动化 |
| `artifacts[id=verify]` | `PASS → /opsx:continue` 直接进入 finalize，且 finalize 写出 git-side closeout | verify 通过不应自动等价为可 closeout |
| `artifacts[id=finalize]` | 明确 merge worktree、push feature branch、创建/更新 PR、comment、cleanup、删除 worktree branch、甚至 `git add` / `git commit` finalize receipt | 与当前人工 Git 安全原则直接冲突 |
| `finalize` escape hatch | 提供 manual finishing-a-development-branch 路径 | 说明 canonical 自动化并非唯一安全路径，但默认仍偏自动 |

### 5.3 适配判定

- `apply` 的现状已把 worktree、subagent、TDD、review 与 receipt 混合到同一 canonical 路径里。
- `finalize` 的现状会自动执行 merge/push/PR/comment/cleanup，且附带可选 escape hatch。
- 本项目当前不允许把这些自动行为直接放入真实业务 change 的默认执行路径。

## 6. Apply / Verify / Finalize 人审门禁模型

| 流程阶段 | 允许产生的产物 | 必须人工审核的内容 | 未批准时禁止动作 |
|---|---|---|---|
| brainstorm / proposal | 问题、目标、范围、能力列表 | 范围是否准确、是否引入新能力、是否触及治理边界 | 不得进入 specs / design |
| specs / design | 需求、场景、技术设计、风险 | 需求是否可测试、设计是否遵守文件系统为真源 / 无强制数据库 | 不得进入 tasks / plan |
| tasks / plan | 任务拆解、微步骤、验证点 | 任务是否足够细、是否可追踪、是否与批准范围一致 | 不得进入 apply |
| apply 前 | worktree 策略、工具选择、回退策略 | 实现工具是否批准、worktree 行为是否批准 | 不得开始真实业务实现 |
| apply 执行期间 | 代码 / 文档变更、测试记录、receipt | 是否仍在批准范围内、是否遵守 TDD / review 纪律 | 不得扩范围、不准跳过验证 |
| verify | 结构验证、完成度、证据检查 | 是否全部通过、是否存在漂移或未闭合项 | verify 不通过不得 finalize |
| finalize 前 | closeout 准备、PR / merge / push 计划 | merge / push / cleanup / PR 安全是否批准 | 不得执行 Git closeout |
| finalize / Git closeout | finalize.md、Git / PR 关闭动作 | 是否满足仓库级安全前置条件 | 不得自动 merge / push / cleanup |

### 6.1 明确门禁

- `apply` 前必须有 Gate B 的人审批准。
- `verify` 的通过不自动等于允许 finalize。
- `finalize` 前必须有独立 Gate D 的人审批准。

## 7. 适配路线比较与推荐决定

### 7.1 路线比较

| 路线 | 含义 | 优点 | 风险 |
|---|---|---|---|
| 方案 A | 建立项目级安全覆盖版 schema，把 `apply/finalize` 改成受控/人审门禁路径 | 与当前治理原则最一致，能保留 upstream 来源追踪，同时消除默认高风险自动化 | 需要后续一次 schema 实施改动 |
| 方案 B | 保留 upstream canonical 自动化语义，等后续独立验证后再启用 | 最少改 schema 表面行为 | 与当前人工 Git 安全原则冲突最大，且会持续保持 NOT READY |
| 方案 C | 双 schema / 双 profile，安全模式与自动模式并存 | 灵活，便于未来 A/B 切换 | 复杂度高，容易增加误启用和选择错误的风险 |

### 7.2 推荐决定

- **推荐路线：方案 A**
- 原因：它能在不放弃 upstream 来源的前提下，把当前默认执行语义收缩为本项目可接受的人审安全模式；这是在不解除现有门禁的情况下，最直接、最可控的路径。

## 8. Superpowers 后续接入与验证顺序建议

### 8.1 推荐顺序

1. 先完成 schema 安全覆盖，使 `apply/finalize` 不再默认触发高风险工具与 Git closeout。
2. 再做 Superpowers 的只读 / 隔离能力探测，确认哪些 skills 真正可用。
3. 最后才考虑在隔离环境中验证 `apply` / `finalize` 相关能力是否可控。

### 8.2 原因

- 先验证工具而不先改 schema，容易把 upstream canonical 自动化误当成已批准的真实流程。
- 先做 schema 安全覆盖，可以保证后续任何工具验证都在受控、可回退、可审计的语境下进行。

## 9. 下一阶段实际整改变更蓝图

### 9.1 阶段建议

- 建议阶段名称：`Phase 3B：项目级安全覆盖 Schema 实施`

### 9.2 允许修改文件

- `openspec/schemas/superspec/schema.yaml`
- `openspec/schemas/superspec/templates/apply.md`
- `openspec/schemas/superspec/templates/finalize.md`
- 如有必要，再次同步 `openspec/config.yaml` 的 policy 文字，但仅限与 schema 语义一致的最小修订

### 9.3 目标节点与拟改变的行为

| 文件 / 节点 | 拟改行为 | 目的 |
|---|---|---|
| `schema.yaml` 顶层 description | 补充“本项目安全覆盖模式”的说明 | 明确 canonical 自动化并非默认启用 |
| `artifacts[id=apply].instruction` | 增加明确的人审 Gate B，禁止在 Phase 3 批准前启动真实业务实现；移除或弱化对自动 subagent 执行的默认承诺 | 阻断未经批准的实现启动 |
| `artifacts[id=verify].instruction` | 明确 verify 只验证证据与一致性，不自动授权 finalize；将“PASS → /opsx:continue”改为“PASS 后待人审”或增加人工审批门槛 | 防止 verify 直接通向自动 closeout |
| `artifacts[id=finalize].instruction` | 默认改为人工 closeout receipt / 建议命令，不自动 merge / push / comment / cleanup；若保留自动路径，则必须附加独立批准开关 | 消除默认 Git 写操作风险 |
| `apply` 顶层 phase block | 保留 receipt / plan 语义，但把真实实现执行置于批准后才可进入的受控流程 | 让 apply 成为人审门禁而不是自动执行门 |
| `finalize` 顶层 phase block | 改为收尾证据与人工 closeout 建议，或仅在明确批准后启用自动 closeout | 防止自动 merge / push / cleanup |

### 9.4 禁止修改范围

- 不修改业务代码
- 不修改测试代码
- 不修改 `.claude/`、`.opencode/`
- 不修改 `AGENTS.md` / `AGENT.md`
- 不修改 `openspec/specs/**`
- 不修改 `openspec/changes/**`
- 不修改历史整改报告内容

### 9.5 验证方式

- YAML parser 硬断言：`apply` / `finalize` 节点仍存在、且其语义已切换为安全覆盖模式
- `openspec validate --all --json` / `--all`：确认 schema 结构未破坏
- `git diff --name-only`：仅应出现蓝图允许的文件
- 文本断言：确认不再保留默认自动 merge / push / cleanup 的未加门禁语义

### 9.6 失败回退

- 若 schema 结构验证失败，立即停止，不扩范围修其他文件。
- 若文本断言失败，回到本阶段记录阻断，不进入业务实现。

## 10. 最终 Git 可见变更集合

```text
## chore/superspec-governance-migration...origin/chore/superspec-governance-migration
?? docs/rectification/11-superspec-phase3a-repository-execution-policy-and-schema-safety-override-design-report.md
```

```text
(empty output)
```

```text
(empty output)
```

说明：

- `git diff --name-only` 为空，因为新增报告尚未进入 Git 跟踪。
- `git diff --stat` 为空，因为默认 diff 不包含未跟踪文件。
- 唯一新增的可见文件是 11 号设计审计报告。

## 11. 保护范围确认

- [x] 未修改 `openspec/config.yaml`
- [x] 未修改 `openspec/schemas/superspec/schema.yaml`
- [x] 未修改 `openspec/schemas/superspec/templates/**`
- [x] 未修改 `openspec/specs/**`
- [x] 未修改 `openspec/changes/**`
- [x] 未修改业务代码
- [x] 未修改测试代码
- [x] 未修改 `AGENTS.md`
- [x] 未修改 `AGENT.md`
- [x] 未修改 `.claude/`
- [x] 未修改 `.opencode/`
- [x] 未执行 `SuperSpec apply`
- [x] 未执行 `SuperSpec finalize`
- [x] 未执行任何 `/opsx:*` lifecycle 命令
- [x] 未执行任何 Git 写操作

## 12. 结论

- Phase 3A 设计审计执行结果：`PASS（设计审计报告已完成）`
- Phase 3 执行就绪判定：仍为 `NOT READY`
- 推荐适配路线：**方案 A**，因为它保留 upstream 来源追踪，同时把默认高风险自动化收缩为本项目可接受的人审安全模式。
- 是否允许安装或运行 Superpowers：`否`
- 是否允许执行真实业务 SuperSpec apply：`否`
- 是否允许执行 SuperSpec finalize：`否`
- 是否允许进入下一项 schema/rule 整改实施阶段：`待 ChatGPT 人工审核`
