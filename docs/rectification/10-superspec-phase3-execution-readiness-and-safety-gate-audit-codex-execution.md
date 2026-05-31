# DiagnoseToolPy × SuperSpec Phase 3：执行就绪与安全门禁审计 — Codex 执行任务书

> 任务编号：Phase 3 / Document No. 10  
> 执行工具：Codex（治理审计执行端，不是默认业务代码实现端）  
> 生成日期：2026-05-31  
> 目标工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 目标分支：`chore/superspec-governance-migration`  
> 本任务书管理规则：**保存在项目仓库外，不得复制或提交至项目仓库。**  
> 前置条件：**用户已人工提交 Phase 2 授权证据集合，且工作区无未提交变更。**

---

## 0. 可直接粘贴给 Codex 的启动 Prompt

```text
你现在负责执行 DiagnoseToolPy × danielhanold/superspec 整改工作的 Phase 3：执行就绪与安全门禁审计。

目标工作区：
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance

目标分支：
chore/superspec-governance-migration

请先完整读取并严格执行仓库外任务书：
<替换为本机实际路径>/10-superspec-phase3-execution-readiness-and-safety-gate-audit-codex-execution.md

重要前提：
1. Phase 2D 已经通过 ChatGPT 人工审核，但必须由用户人工完成 Phase 2 授权文件提交后，本任务才能开始。
2. 若开始时 git status 显示工作区不干净，或 05-* 至 09-* 报告 / openspec/config.yaml 未进入当前 HEAD，则停止本任务；不要修改任何文件，只向我回传阻断原因和只读命令输出。
3. 本阶段不是业务实现阶段，也不是工具安装阶段。本阶段只允许做执行就绪与安全门禁审计。
4. 不得执行 SuperSpec apply、SuperSpec finalize、任何 /opsx:* lifecycle 命令、Superpowers 安装或运行。
5. 不得修改 openspec/config.yaml、schema、living specs、业务代码、测试、AGENTS.md / AGENT.md、.claude/、.opencode/ 或任何既有文件。
6. 若前置检查通过，仅允许新增：
   docs/rectification/10-superspec-phase3-execution-readiness-and-safety-gate-audit-report.md

本阶段需要审计五类 Phase 3 前置条件：
A. 实际业务实现工具决策：不得将当前治理报告执行工具 Codex 自动等同为业务实现工具。基于当前协作基线，核验并记录“ChatGPT/Codex 负责分析与设计文档，Claude Code 为业务代码实现主端，opencode 为兼容/必要时替代端”的适配影响与待批准决策。
B. Superpowers availability：仅检查现有可见状态、schema 依赖与缺口，不安装、不运行。若缺少可验证的可用性证据，结论必须为 NOT READY，并提出后续独立安装/验证阶段，不得绕过。
C. Worktree behavior：使用只读 git 命令核验当前 worktree 状态、分支隔离前提，以及 superspec schema 中 apply/finalize 对 worktree 的行为要求；不得创建、删除或清理 worktree。
D. Review discipline：形成真实业务 change 在 proposal/spec/design/tasks/plan/apply/verify/finalize 各关键点需要人工批准的准入矩阵，确保 apply 前和 finalize 前都存在明确的人审阻断。
E. Git-safety prerequisites：核验未来 merge、push、PR、worktree cleanup 的安全前置条件，列出哪些仍未批准；不得执行任何 Git 写操作。

最终新增 10-*report.md。报告结论只能是：
- READY FOR CHATGPT REVIEW：所有五类条件均已有充分只读证据且没有待处理阻断；或
- NOT READY：存在任一工具安装、工作流适配、worktree、review 或 Git safety 缺口。

即使报告为 READY FOR CHATGPT REVIEW，也不得自行解除门禁、进入业务实现、执行 apply/finalize、提交或推送。最终只回传 10-*report.md 给用户供 ChatGPT 审核。
```

---

## 1. 任务背景

Phase 2 系列已完成 `openspec/config.yaml` 的 schema 接入、项目 context / artifact rules 注入以及执行门禁语义纠偏。Phase 2D 最终将下列门禁固定在配置中：

- 在 Phase 3 审批实现工具、Superpowers 可用性、worktree 行为、review discipline 与 Git-safety prerequisites 前，不得通过 SuperSpec `apply` 开始真实业务实现。
- 在 Phase 3 审批 merge、push、worktree cleanup 与 pull-request safety prerequisites 前，不得通过 SuperSpec `finalize` 执行 Git/PR closeout。

Phase 3 的目标不是执行 apply/finalize，而是通过只读审计，判断这些前置条件是否已经具备，或明确后续仍必须补齐的独立阶段。

---

## 2. Phase 3 总体判定原则

### 2.1 不允许预设“已经可用”

SuperSpec schema 已进入项目，不等于以下能力已经可安全执行：

- Superpowers 已安装且与实际实现端兼容；
- `apply` 所声明的 worktree + subagent-driven-development 能在当前工作流中稳定运行；
- `finalize` 所声明的 merge / push / PR closeout 与用户人工提交治理原则兼容；
- Codex 作为整改报告执行端可以直接承担业务代码实现。

任一证据不足，必须记录为缺口或阻断，不得以推测替代验证。

### 2.2 工具职责边界

当前评估基线如下，必须在报告中进行适配审查，而非自行改写：

| 职责 | 当前基线工具 |
|---|---|
| 需求分析、方案设计、执行任务书输出 | ChatGPT / Codex |
| 治理整改任务书的受控执行与报告生成 | Codex |
| 未来业务代码实现主端 | Claude Code |
| 设计兼容及必要时替代实现端 | opencode |

如实际仓库证据与上述基线存在冲突，报告应列出冲突并判定是否构成阻断；本阶段不得修改工具目录解决冲突。

---

## 3. 前置门禁：Phase 2 必须已由用户人工提交

### 3.1 只读检查命令

进入目标工作区后执行：

```bash
git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git log --oneline --decorate -5
git ls-files -- \
  openspec/config.yaml \
  docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md \
  docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md \
  docs/rectification/07-superspec-config-gate-syntax-fix-report.md \
  docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md \
  docs/rectification/09-superspec-phase2-final-gate-correction-and-admission-closure-report.md
```

### 3.2 必须满足

- 当前分支为 `chore/superspec-governance-migration`。
- 工作区在开始时无修改或未跟踪文件。
- `openspec/config.yaml` 以及 `05-*` 至 `09-*` 报告均已进入当前 Git 跟踪集合。
- 当前 `openspec/config.yaml` 中两条 Phase 3 门禁仍与 Phase 2D 批准文本一致。

### 3.3 不满足时的行为

若任一前置条件不满足：

- **立即停止**；
- 不得创建 `10-*report.md`，避免在未提交基线上新增脏状态；
- 不得编辑或修复任何仓库文件；
- 只在聊天回传中提供只读命令输出与阻断原因，等待用户处理。

---

## 4. 允许与禁止范围

### 4.1 前置检查通过后唯一允许新增的文件

```text
docs/rectification/10-superspec-phase3-execution-readiness-and-safety-gate-audit-report.md
```

### 4.2 禁止修改范围

不得修改任何已有文件，尤其包括：

```text
openspec/config.yaml
openspec/schemas/**
openspec/specs/**
openspec/changes/**
docs/rectification/00-*.md ... docs/rectification/09-*.md
AGENT.md
AGENTS.md
work-items/**
docs/ai-harness/**
.claude/**
.opencode/**
业务源代码目录
测试目录
依赖/锁定文件
.gitignore
```

### 4.3 禁止操作

```text
git add
git commit
git push
git pull
git merge
git rebase
git reset
git clean
git stash
git worktree add
git worktree remove
git worktree prune
任何 /opsx:* 命令
任何 SuperSpec apply / verify / finalize 生命周期执行
任何 Superpowers 安装、初始化、运行或配置注入
任何 Claude Code / opencode 工具配置修改
任何真实业务实现或测试代码修改
```

---

## 5. 审计项 A：业务实现工具与 SuperSpec 适配决策

### 5.1 审计问题

报告必须逐项回答：

1. 当前仓库的治理整改执行端与未来业务代码实现端分别是谁？
2. `superspec` schema 中对实现阶段执行环境、skill、subagent 或 worktree 的依赖是什么？
3. 这些依赖是否天然兼容 Claude Code 作为业务代码实现主端？
4. 若需要兼容 opencode，哪些能力无法直接假设存在？
5. Codex 是否仅继续承担受控审计/报告执行端，还是已有充分依据批准其成为业务实现端？未获得用户明确批准时，不得将其升级为实现端。

### 5.2 最低证据

允许读取：

```text
openspec/config.yaml
openspec/schemas/superspec/**
AGENT.md
AGENTS.md
docs/rectification/00-*.md ... docs/rectification/09-*.md
```

可使用只读文本检索命令定位 `apply`、`finalize`、`superpowers`、`subagent`、`worktree`、`Claude`、`Codex`、`opencode` 等关键字。

### 5.3 输出要求

报告形成一张决策表：

| 决策点 | 当前证据 | 判定 | 仍需批准或补齐事项 |
|---|---|---|---|
| 治理执行端 |  |  |  |
| 业务实现主端 |  |  |  |
| opencode 兼容策略 |  |  |  |
| schema 与实际实现端适配 |  |  |  |

若业务实现端与 schema 所依赖的能力尚未验证，Phase 3 总结论不得为可直接执行真实业务 change。

---

## 6. 审计项 B：Superpowers Availability

### 6.1 审计边界

本阶段只检查“是否存在已验证可用的证据”，不得安装或运行 Superpowers，不得写入 `.claude/` / `.opencode/`。

### 6.2 必须核验

- `openspec/schemas/superspec/**` 中对 Superpowers 或 skills 的依赖描述；
- 当前仓库是否已有被跟踪的、经批准的工具接入资产；
- 现有 `docs/rectification/**` 是否已提供可用性验证证据；
- 实际业务实现主端 Claude Code 与兼容端 opencode 是否均已有明确的 Superpowers 适配结论。

### 6.3 判定规则

| 状态 | 判定 |
|---|---|
| 有可追踪证据证明所需能力已接入、已适配、已通过安全验证 | 可进入 ChatGPT 审核 |
| 只有 schema 声明依赖，但无安装/适配/验证证据 | `NOT READY`，需新增独立接入验证阶段 |
| 需要安装、初始化或运行工具才能确认 | `NOT READY`，不得在本阶段顺手执行 |

---

## 7. 审计项 C：Worktree Behavior

### 7.1 允许的只读命令

```bash
git worktree list --porcelain
git branch --show-current
git rev-parse --show-toplevel
git rev-parse HEAD
git status --short --branch --untracked-files=all
```

同时只读检查 schema 中关于 apply / finalize / worktree 的描述。

### 7.2 必须输出

报告必须明确：

- 当前整改 worktree 的身份与分支；
- schema 对未来业务 change 创建/使用/合并 worktree 的预期行为；
- 用户人工审批/提交原则是否与 schema 的自动 closeout 行为存在冲突；
- 在真实 business apply 前，需要哪种隔离策略、回退策略与人审点。

若 schema 的自动 worktree / merge 行为尚不能与当前治理原则兼容，判定为阻断。

---

## 8. 审计项 D：Review Discipline

报告必须为未来第一个真实业务 change 提供准入矩阵，至少包含：

| 流程阶段 | 允许产生的产物 | 必须人工审核的内容 | 未批准时禁止动作 |
|---|---|---|---|
| brainstorm / proposal |  |  |  |
| specs / design |  |  |  |
| tasks / plan |  |  |  |
| apply 前 |  |  |  |
| apply 执行期间 |  |  |  |
| verify |  |  |  |
| finalize 前 |  |  |  |
| finalize / Git closeout |  |  |  |

矩阵必须确保：

- 未审核 `tasks/plan` 前不得开始业务实现；
- apply 前必须有人审确认范围、工具、worktree 与回退策略；
- verify 的通过不自动等于允许 finalize；
- merge / push / PR closeout 仍需单独人审批准。

---

## 9. 审计项 E：Git-Safety Prerequisites

### 9.1 需要核验的问题

报告必须回答：

- 未来真实业务 change 从哪一类分支开始；
- SuperSpec `apply` 预期创建何种 worktree / branch；
- `finalize` 是否可能直接 merge / push / 更新或创建远程分支 / PR；
- 与“不让执行工具自行 commit / push”的既有治理原则是否冲突；
- 若存在冲突，未来需要修改 schema、配置规则、执行方式，还是禁止使用 canonical finalize。

### 9.2 安全决策表

必须输出：

| Git 行为 | Schema 当前行为/预期 | 当前项目允许性 | Phase 3 判定 | 后续动作 |
|---|---|---|---|---|
| 创建实现 worktree |  |  |  |  |
| 实现分支 commit |  |  |  |  |
| merge |  |  |  |  |
| push |  |  |  |  |
| PR 创建/更新 |  |  |  |  |
| worktree cleanup |  |  |  |  |

发现 `finalize` 会自动执行与既有人工提交原则冲突的 Git 写操作时，应明确记录为门禁阻断，不得在报告中模糊处理。

---

## 10. 必须新增的报告文件

前置检查通过后，新增且仅新增：

```text
docs/rectification/10-superspec-phase3-execution-readiness-and-safety-gate-audit-report.md
```

### 10.1 报告必需章节

```markdown
# DiagnoseToolPy SuperSpec Phase 3 执行就绪与安全门禁审计报告

## 1. 执行摘要
## 2. Phase 2 提交基线与工作区洁净性核验
## 3. 审计范围、允许读取路径与禁止操作确认
## 4. 业务实现工具与 SuperSpec 适配决策
## 5. Superpowers Availability 审计
## 6. Worktree Behavior 审计
## 7. Review Discipline 准入矩阵
## 8. Git-Safety Prerequisites 审计
## 9. 发现的阻断项与后续整改建议
## 10. 最终 Git 可见变更集合
## 11. 保护范围确认
## 12. 结论
```

### 10.2 最终 Git 状态要求

生成报告后执行并粘贴：

```bash
git status --short --branch --untracked-files=all
git diff --name-only
git diff --stat
```

预期结果：

```text
?? docs/rectification/10-superspec-phase3-execution-readiness-and-safety-gate-audit-report.md
```

其中 `git diff --name-only` 与 `git diff --stat` 可能为空，因为未跟踪的新报告不会出现在默认 diff 中；必须在报告中对此作出说明，不得误判为未生成报告。

---

## 11. Phase 3 报告结论格式

### 11.1 存在任一未验证或冲突项时

必须使用：

```text
- Phase 3 审计执行结果：PASS（审计任务本身完成）
- 执行就绪判定：NOT READY
- 是否允许执行真实业务 SuperSpec apply：否
- 是否允许执行 SuperSpec finalize：否
- 是否允许进入后续整改阶段：待 ChatGPT 人工审核
```

### 11.2 仅当五类门禁均有充分可追踪证据时

可使用：

```text
- Phase 3 审计执行结果：PASS（审计任务本身完成）
- 执行就绪判定：READY FOR CHATGPT REVIEW
- 是否允许执行真实业务 SuperSpec apply：待 ChatGPT 人工审核
- 是否允许执行 SuperSpec finalize：待 ChatGPT 人工审核
- 是否允许进入后续整改阶段：待 ChatGPT 人工审核
```

禁止 Codex 直接写“允许执行 apply/finalize”或开始真实业务实现。

---

## 12. 回传要求

完成后，仅回传：

```text
docs/rectification/10-superspec-phase3-execution-readiness-and-safety-gate-audit-report.md
```

不得代替用户提交该报告，也不得继续执行任何后续阶段。
