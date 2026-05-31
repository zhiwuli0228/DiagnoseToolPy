# DiagnoseToolPy × SuperSpec Phase 3A：仓库级执行策略与 Schema 安全覆盖设计审计 — Codex 执行任务书

> 任务编号：Phase 3A / Document No. 11  
> 执行工具：Codex（治理审计与设计报告执行端）  
> 生成日期：2026-05-31  
> 目标工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 目标分支：`chore/superspec-governance-migration`  
> 本任务书管理规则：**保存在项目仓库外，不得复制或提交到项目仓库。**  
> 前置条件：**用户已人工提交 `10-superspec-phase3-execution-readiness-and-safety-gate-audit-report.md`，且目标工作区无未提交变更。**

---

## 0. 可直接粘贴给 Codex 的启动 Prompt

```text
你现在负责执行 DiagnoseToolPy × danielhanold/superspec 整改工作的 Phase 3A：仓库级执行策略与 Schema 安全覆盖设计审计。

目标工作区：
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance

目标分支：
chore/superspec-governance-migration

请先完整读取并严格执行仓库外任务书：
<替换为本机实际路径>/11-superspec-phase3a-repository-execution-policy-and-schema-safety-override-design-codex-execution.md

本阶段前提与背景：
1. Phase 3 审计已经完成，其报告结论为：审计任务 PASS，但执行就绪状态 NOT READY。
2. Phase 3 的主要阻断不是简单缺少安装命令，而是 upstream superspec schema 的 canonical apply/finalize 行为与本项目治理原则存在尚未解决的冲突：
   - apply 依赖 Superpowers、worktree、subagent-driven-development 等能力；
   - finalize 可能自动 merge、push、PR closeout 与 worktree cleanup；
   - 本项目当前仍要求 Git 写操作、人审边界和真实业务实现端必须先被明确批准。
3. 当前工具职责基线已经由用户确定，必须作为设计输入而不是待 Codex 随意改写的假设：
   - ChatGPT 与 Codex：需求分析、方案设计、执行文档输出；Codex 还可在受控范围内执行治理报告任务；
   - Claude Code：未来业务代码实现主端；
   - opencode：设计阶段需兼容的必要时替代实现端。
4. 本阶段不安装或运行 Superpowers，不运行 SuperSpec apply/finalize，不修改任何 schema、config、规则、工具目录或业务代码。
5. 本阶段的唯一产物是在 docs/rectification/ 新增一份设计审计报告，为下一阶段真正修改 schema / rules 提供精确变更蓝图。

开始前必须只读检查：
- 当前分支必须为 chore/superspec-governance-migration；
- 工作区必须干净；
- openspec/config.yaml 及 docs/rectification/05-* 至 10-* 均必须已进入当前 HEAD；
- config.yaml 的 apply/finalize Phase 3 阻断文本必须仍存在。
若任一检查失败，停止，不新增文件、不修改文件，只回传阻断证据。

本阶段需要完成：
A. 精读 openspec/schemas/superspec/** 与 openspec/config.yaml，定位 upstream schema 中所有会触发或描述实现工具、Superpowers、worktree、自动 commit/merge/push/PR/cleanup 的具体 artifact/template/instruction 节点。
B. 基于用户既定工具职责与人工 Git 安全原则，给出仓库级 execution policy：
   - 谁负责设计；
   - 谁负责真实代码实现；
   - 何时可使用 Claude Code，何时只保留 opencode 兼容；
   - Codex 是否只能执行治理报告/审计任务；
   - 所有 apply 前、verify 后、finalize 前的人审门禁。
C. 对 canonical upstream superspec 流程作适配判定：必须在以下方向中选定并论证一个推荐方案，而不能只写“待确认”：
   - 方案 A：创建本项目安全覆盖版 schema / 修改项目本地 superspec schema，使 apply/finalize 不再未经人审自动执行高风险工具与 Git closeout；
   - 方案 B：保留 upstream canonical 行为，仅在后续独立隔离验证并明确批准其自动化能力后才启用；
   - 或明确说明为什么需要第三种更合适的项目级适配方案。
D. 输出下一阶段可直接实施的变更蓝图：必须精确到允许修改文件、目标节点、拟改变的行为、验证方法与禁止范围；但本阶段不得实际修改这些文件。
E. 输出对 Superpowers 的后续策略：是先适配 schema 再验证工具，还是先做只读/隔离能力探测；必须解释该顺序如何避免将不安全 canonical 行为带入真实业务 change。

如果前置检查通过，只允许新增：
docs/rectification/11-superspec-phase3a-repository-execution-policy-and-schema-safety-override-design-report.md

报告结论必须写为：
- Phase 3A 设计审计执行结果：PASS（若报告完整生成）
- Phase 3 执行就绪判定：仍为 NOT READY
- 推荐适配路线：<明确方案及一句话原因>
- 是否允许安装或运行 Superpowers：否
- 是否允许执行真实业务 SuperSpec apply：否
- 是否允许执行 SuperSpec finalize：否
- 是否允许进入下一项 schema/rule 整改实施阶段：待 ChatGPT 人工审核

执行完成后不要提交、不要安装工具、不要进入任何业务实现，仅回传 11-*report.md 给用户供 ChatGPT 审核。
```

---

## 1. 本阶段目的

Phase 3 已证明当前尚不可执行真实业务 `SuperSpec apply` 或 `SuperSpec finalize`。其核心原因并非仅仅缺少工具安装，而是 **上游 SuperSpec canonical 执行行为与本项目批准中的工具职责、人审边界、Git 安全原则尚未对齐**。

本阶段只进行设计审计，形成下一次安全整改的精确蓝图，回答以下问题：

1. 本项目是否应直接采用 upstream `superspec` 的 canonical `apply/finalize` 行为？
2. 若不能直接采用，项目本地 schema 或规则需要覆盖哪些行为？
3. Claude Code 作为业务实现主端、opencode 作为兼容端时，Superpowers 依赖应如何处理？
4. 哪些人审门禁必须固化在 schema / artifact instruction / config rules 中？
5. 后续应先修改执行策略，还是先安装/验证 Superpowers？

---

## 2. 已确定且不得擅自改写的基线决策

### 2.1 工具职责基线

| 职责 | 已确定工具策略 |
|---|---|
| 需求分析、方案设计、设计文档与整改任务书输出 | ChatGPT / Codex |
| 受控治理整改、只读审计与执行报告产出 | Codex |
| 未来真实业务代码实现主端 | Claude Code |
| 设计阶段必须兼容、必要时可替代实现的工具 | opencode |

Codex 不得在本报告中自行宣告成为真实业务实现主端。若后续建议 Codex 参与代码实现，只能列为需用户另行审批的备选项。

### 2.2 当前安全基线

- 在 Phase 3 执行条件明确批准前，不得通过 SuperSpec `apply` 执行真实业务实现。
- 在 Phase 3 Git closeout 条件明确批准前，不得通过 SuperSpec `finalize` 执行 merge、push、PR closeout 或 worktree cleanup。
- 目前不允许工具擅自执行 Git 写操作。
- 目前不允许在治理阶段修改业务代码。
- `08-*` 的错误准入结论已失效；`09-*` 为 Phase 2 最终准入依据；`10-*` 为 Phase 3 `NOT READY` 证据。

---

## 3. 前置检查门禁

### 3.1 只读命令

在目标 worktree 执行并记录关键输出：

```bash
git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git log --oneline --decorate -6
git ls-files -- \
  openspec/config.yaml \
  docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md \
  docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md \
  docs/rectification/07-superspec-config-gate-syntax-fix-report.md \
  docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md \
  docs/rectification/09-superspec-phase2-final-gate-correction-and-admission-closure-report.md \
  docs/rectification/10-superspec-phase3-execution-readiness-and-safety-gate-audit-report.md
```

用只读检索或 parser 确认 `openspec/config.yaml` 仍含有：

```text
Do not execute real business implementation through SuperSpec apply until Phase 3 approves
Do not execute Git/PR closeout through SuperSpec finalize until Phase 3 approves
```

### 3.2 开始条件

必须满足：

- 分支为 `chore/superspec-governance-migration`；
- 开始时工作区干净；
- `openspec/config.yaml` 与 `05-*` 至 `10-*` 报告均已被当前 HEAD 跟踪；
- Phase 2D 两条门禁仍存在且未弱化。

### 3.3 前置失败处理

若不满足任一条件：

- 立即停止；
- 不新增 `11-*report.md`；
- 不修改任何仓库文件；
- 只回传失败检查证据与阻断原因。

---

## 4. 允许读取范围与唯一允许产物

### 4.1 允许只读分析范围

```text
openspec/config.yaml
openspec/schemas/superspec/**
AGENT.md
AGENTS.md
docs/README.md
docs/rectification/00-*.md ... docs/rectification/10-*.md
.git/worktrees 或 git worktree 只读命令可见信息
```

可使用只读检索定位：

```text
Superpowers
superpowers:
worktree
subagent
TDD
review
apply
verify
finalize
commit
merge
push
pull request
PR
cleanup
Claude
Codex
opencode
```

### 4.2 前置通过后唯一允许新增文件

```text
docs/rectification/11-superspec-phase3a-repository-execution-policy-and-schema-safety-override-design-report.md
```

### 4.3 禁止修改与禁止执行

不得修改任何已有文件；不得执行：

```text
git add / commit / push / pull / merge / rebase / reset / clean / stash
git worktree add / remove / prune
openspec 或 /opsx:* 的 lifecycle 命令
SuperSpec apply / verify / finalize
Superpowers 安装、初始化、启用或运行
Claude Code / opencode 配置变更
任何业务代码或测试变更
```

---

## 5. 必须审计的 Schema 行为定位

报告必须列出项目本地 `openspec/schemas/superspec/**` 中与以下能力有关的**具体文件、artifact/phase 节点、关键行为摘要及风险**：

| 类别 | 必须定位的行为 |
|---|---|
| 实现工具依赖 | Superpowers skills、subagent-driven-development、executing-plans、TDD、code review 等 |
| `apply` 行为 | 是否创建/要求 worktree，是否引导开始真实业务实现，是否隐含 commit 行为 |
| `verify` 行为 | 是否会错误地将验证通过自动解释为可 closeout |
| `finalize` 行为 | merge、push、PR 创建/更新、comment、cleanup、自动 closeout |
| 人审机制 | schema 是否已有显式 approval checkpoint；缺失在哪里 |
| fallback 行为 | 无 subagent / 无 Superpowers / 使用非 Claude 工具时的路径 |

每一项必须区分：

- 上游 schema 当前实际陈述的行为；
- 本项目是否批准该行为；
- 该行为应保留、覆盖、禁用还是延迟验证。

---

## 6. 仓库级 Execution Policy 设计

报告必须形成一个明确的执行策略，不允许只罗列缺口。

### 6.1 工具角色矩阵

至少填写：

| 工作阶段 | 责任工具 | 可执行动作 | 禁止动作 | 人工批准点 |
|---|---|---|---|---|
| 需求/治理分析 | ChatGPT / Codex |  |  |  |
| proposal/spec/design | ChatGPT / Codex |  |  |  |
| tasks/plan | ChatGPT / Codex |  |  |  |
| 真实代码实现 | Claude Code 主端；opencode 兼容端 |  |  |  |
| verify |  |  |  |  |
| Git closeout |  |  |  |  |

### 6.2 人审门禁模型

必须定义至少以下审批点，并说明下一阶段应如何使其可执行或可追踪：

| 门禁 | 必须审批内容 | 不通过时必须阻断的动作 |
|---|---|---|
| Gate A：允许生成实施计划 | scope、设计、验收标准 | 生成真实实现任务/实现 |
| Gate B：允许进入 apply / 实现 | 实现工具、允许路径、worktree 策略、测试策略、回退策略 | 真实代码变更 |
| Gate C：允许完成 verify 结论 | 测试证据、范围漂移、风险关闭 | closeout |
| Gate D：允许 Git closeout | merge、push、PR、cleanup 策略与目标分支 | finalize 或任何 Git 写动作 |

### 6.3 `finalize` 处理原则

必须明确建议本项目采取哪一种行为：

- **人工 closeout 模式**：`finalize` 仅产出 closeout receipt / 建议命令，不自动 merge、push、PR 或 cleanup；真正 Git 操作由用户人工执行。
- **受控自动 closeout 模式**：仅在额外批准、隔离验证、权限与回退策略完备后才允许，且需列出批准条件。
- 其他模式：必须给出比上述两种更安全且可实施的理由。

在当前已知治理原则下，若建议保持 upstream 自动 closeout，必须充分说明为何不与人工 Git 安全原则冲突；否则应推荐覆盖该行为。

---

## 7. 必须选择的适配路线

报告不得仅写“待后续决定”。必须在证据基础上给出一条推荐路线。

### 可选路线 A：项目级安全覆盖 Schema

核心含义：

- 保留 upstream schema 来源与版本追踪；
- 在项目本地 schema 中覆盖与本项目冲突的 `apply/finalize` instruction；
- `apply` 仅在人审 Gate B 批准后允许交由指定实现端执行；
- `finalize` 默认变更为人工 closeout receipt，不自动执行 Git/PR 写操作；
- Superpowers 只在适配路径与实现端支持性明确后进入独立验证阶段。

### 可选路线 B：保留 upstream canonical 自动化语义

核心含义：

- 不改 schema 行为；
- 后续必须独立验证全部 Superpowers、worktree 与自动 Git closeout 能力；
- 需要用户明确放弃或调整当前“Git 写操作人工批准”治理原则。

### 可选路线 C：项目级双配置/双 schema 路线

核心含义：

- 设计安全人工模式与未来可选自动化模式两套 schema/profile；
- 当前只启用安全人工模式；
- 自动模式只有在独立验证及审批后才可启用。

报告必须对 A/B/C 进行简短比较，并选定一个推荐方案。推荐方案必须服务于当前工具职责与安全基线。

---

## 8. 下一阶段变更蓝图要求

报告必须给出下一项实际整改任务的精确蓝图，但本阶段不得实施修改。蓝图至少包括：

| 项目 | 必须写明内容 |
|---|---|
| 阶段建议编号与名称 | 例如 Phase 3B：项目级安全执行 Schema 覆盖实施 |
| 允许修改文件 | 必须精确到具体文件或模板路径 |
| 每个文件的目标改动 | 需要覆盖的节点、指令或 rule |
| 禁止修改范围 | schema 外的业务代码/工具目录等 |
| 期望行为 | apply/finalize、人审、Git closeout 的新行为 |
| 验证方式 | YAML/parser、OpenSpec validate、关键文本断言、git diff 边界 |
| 失败回退 | 若验证失败如何停止与报告，不扩大修改范围 |

若需要先独立验证 Superpowers 而不是先适配 schema，必须明确为什么这不会造成不安全自动行为被误启用。

---

## 9. 必须新增的报告文件

前置检查通过后，新增且仅新增：

```text
docs/rectification/11-superspec-phase3a-repository-execution-policy-and-schema-safety-override-design-report.md
```

### 9.1 必需章节

```markdown
# DiagnoseToolPy SuperSpec Phase 3A 仓库级执行策略与 Schema 安全覆盖设计审计报告

## 1. 执行摘要
## 2. Phase 3 NOT READY 结论承接与本阶段边界
## 3. Phase 2/3 基线提交与工作区洁净性核验
## 4. 当前工具职责基线与仓库级 Execution Policy
## 5. SuperSpec Schema 高风险行为精确定位
## 6. Apply / Verify / Finalize 人审门禁模型
## 7. 适配路线比较与推荐决定
## 8. Superpowers 后续接入与验证顺序建议
## 9. 下一阶段实际整改变更蓝图
## 10. 最终 Git 可见变更集合
## 11. 保护范围确认
## 12. 结论
```

### 9.2 结论格式

报告必须使用：

```text
- Phase 3A 设计审计执行结果：PASS（设计审计报告已完成）
- Phase 3 执行就绪判定：仍为 NOT READY
- 推荐适配路线：<A / B / C 或明确的第三方案，并给出一句话理由>
- 是否允许安装或运行 Superpowers：否
- 是否允许执行真实业务 SuperSpec apply：否
- 是否允许执行 SuperSpec finalize：否
- 是否允许进入下一项 schema/rule 整改实施阶段：待 ChatGPT 人工审核
```

---

## 10. 完成后的 Git 状态与回传

生成报告后执行并写入报告：

```bash
git status --short --branch --untracked-files=all
git diff --name-only
git diff --stat
```

预期仅出现：

```text
?? docs/rectification/11-superspec-phase3a-repository-execution-policy-and-schema-safety-override-design-report.md
```

说明 `git diff --name-only` / `git diff --stat` 对未跟踪报告为空的原因。

完成后只回传：

```text
docs/rectification/11-superspec-phase3a-repository-execution-policy-and-schema-safety-override-design-report.md
```

不得提交、不得修改 schema、不得进入后续实施。
