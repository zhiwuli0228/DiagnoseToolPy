# DiagnoseToolPy × SuperSpec Phase 3B-D：最小化 Schema 安全覆盖重新实施 — Codex 执行任务书

> 任务编号：Phase 3B-D / Document No. 16  
> 执行工具：Codex（受控治理整改执行端）  
> 生成日期：2026-05-31  
> 目标工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 目标分支：`chore/superspec-governance-migration`  
> 本任务书管理规则：**保存在项目仓库外，不得复制或提交到项目仓库。**  
> 严格前置条件：**用户已人工提交 `12-*`、`13-*`、`14-*`、`15-*` 失败/取证/恢复/补证报告，且工作区完全洁净。**

---

## 0. 可直接粘贴给 Codex 的启动 Prompt

```text
你现在负责执行 DiagnoseToolPy × danielhanold/superspec 整改工作的 Phase 3B-D：最小化 Schema 安全覆盖重新实施。

目标工作区：
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance

目标分支：
chore/superspec-governance-migration

请先完整读取并严格执行仓库外任务书：
<替换为本机实际路径>/16-superspec-phase3b-minimal-safe-schema-override-reimplementation-codex-execution.md

必须理解并遵守的历史结论：
1. Phase 3B 第一次实施已失败：schema.yaml 被改为 69 insertions / 536 deletions，虽然变更集中在目标节点，但属于过度删减，不满足“最小必要安全覆盖”。
2. 12-* 是失败实施事实报告，其 PASS 自评已被否决；13-* 是 CORRECTION REQUIRED 取证报告；14-* 记录恢复；15-* 补齐最终状态证据。
3. 用户必须先人工提交 12-* 至 15-* 报告并确认工作区 clean，本阶段才能开始。
4. 本阶段重新实施必须从已提交的原始 HEAD schema 基线开始，不得沿用失败 diff，不得整块删除 canonical workflow 内容。

本阶段默认唯一允许修改的既有文件：
openspec/schemas/superspec/schema.yaml

唯一允许新增：
docs/rectification/16-superspec-phase3b-minimal-safe-schema-override-reimplementation-report.md

禁止修改：
openspec/config.yaml；openspec/schemas/superspec/schema.yaml 以外的 schema 文件；openspec/specs/**；openspec/changes/**；docs/rectification/00-* 至 15-*；AGENTS.md；AGENT.md；docs/README.md；work-items/**；.claude/**；.opencode/**；业务代码；测试；依赖或锁文件。

禁止执行：
git add/commit/push/pull/merge/rebase/reset/restore/checkout --/clean/stash；
git worktree add/remove/prune；
任何 /opsx:* lifecycle 命令；
SuperSpec apply/verify/finalize；
任何 Superpowers 安装、运行或配置注入；
任何 Claude Code/opencode 配置修改或真实业务实现。

开始前只读门禁：
- 当前分支必须为 chore/superspec-governance-migration；
- 工作区必须完全 clean；
- openspec/config.yaml 与 docs/rectification/05-* 至 15-* 均被当前 HEAD 跟踪；
- schema.yaml 必须与 HEAD 一致，无 diff；
- config.yaml 中 Phase 3 apply/finalize 阻断门禁仍存在。

实施策略：只允许“插入安全覆盖声明 + 对直接跳转/自动执行语句做局部替换”，禁止整段删减。
A. 在 schema 顶层 description 中以最小增补方式声明 repository-safe human-gated override；保留 upstream canonical 行为说明作为来源参考，并明确其自动执行能力在本项目中未获启用。
B. 对 apply 相关 description/instruction/顶层 apply phase 仅增加 Gate B 前置阻断：未获人工批准前不得运行 Superpowers、创建实现 worktree、调度 subagent 或修改业务代码；apply receipt 不等于授权。不得删除原有 canonical 实施流程大段内容；保留内容必须被明确标为“仅在未来独立批准后才可启用的非默认参考流程”。
C. 对 verify 仅局部替换或增补：PASS 只表示验证证据通过，不授权 finalize；原有通向 finalize 的直接跳转必须改为等待 Gate D 人工批准。
D. 对 finalize 仅通过安全覆盖声明和必要的直接命令禁用语义，使默认行为变为 closeout receipt / recommendation；保留上游 merge/push/PR/cleanup 流程时，必须明确标记为 NON-EXECUTABLE UPSTREAM REFERENCE，当前不得执行。不得删除整段上游参考逻辑。
E. 若无法在保留结构的前提下完成安全覆盖，停止，输出 BLOCKED 报告，不扩大修改范围。

硬性 diff 边界：
- 非目标 artifacts（brainstorm/proposal/design/specs/tasks/plan）的 YAML 解析内容必须与 HEAD 完全一致；
- artifact id 列表、requires/dependency 关系除 apply/verify/finalize 必要文本局部调整外不得改变；
- 不允许删除完整段落级的 upstream canonical workflow；
- `git diff --numstat -- schema.yaml` 的删除行数不得超过 30 行；
- 如删除行数超过 30 或总变更显示明显重写，阶段不得自评 PASS，必须停止并报告 BLOCKED，不得继续修补。

修改后必须提供：
1. HEAD 与工作树 YAML 结构对比：artifact id、非目标 artifact 内容哈希一致性、apply/verify/finalize 被改变字段列表。
2. 关键安全文本实际命中输出：Gate B、approved implementation tool、Gate D、Verification PASS does not authorize finalize、closeout receipt、NON-EXECUTABLE UPSTREAM REFERENCE，以及禁止自动 Git 行为的文本。
3. 风险残留逐项审查：schema 中仍命中的 superpowers、worktree、subagent、git add/commit/merge/push、PR、cleanup、/opsx:continue 分别位于何处，是否已被非执行参考或人工门禁包围。
4. `git diff --stat`、`git diff --numstat`、`git diff --unified=3` 的 hunk 分类。
5. `openspec schemas`、`openspec validate --all --json`、`openspec validate --all` 的验证输出。

报告结论即使 PASS 也必须保持：
- Phase 3 执行就绪判定：仍为 NOT READY
- 不允许安装或运行 Superpowers
- 不允许执行真实业务 SuperSpec apply/finalize
- 是否允许提交 schema 与 16 报告：待 ChatGPT 人工审核
- 是否允许进入后续隔离验证阶段：待 ChatGPT 人工审核

最终只回传 16-*report.md，禁止提交或继续推进。
```

---

## 1. 本阶段批准依据

### 1.1 已获审核确认的证据链

此前阶段形成如下状态：

| 报告 | 作用 | 审核效力 |
|---|---|---|
| `12-*` | 记录第一次 Phase 3B 实施事实 | 其 `PASS` 自评被否决，保留为失败事实 |
| `13-*` | 对 `69 insertions / 536 deletions` 进行取证 | `CORRECTION REQUIRED` 已被接受 |
| `14-*` | 记录授权恢复 `schema.yaml` 至 HEAD | 恢复方向接受，但其最终状态证据缺口由 15 补齐 |
| `15-*` | 补齐恢复后的最终状态 | 证明 `schema.yaml` clean，仅 12–15 为未跟踪证据 |

### 1.2 本阶段进入前必须人工完成的动作

在开始本任务前，用户必须已人工提交 `12-*` 至 `15-*` 报告。禁止 Codex 自行提交。

提交后工作区必须 clean，确保重做从已经恢复的 HEAD 基线开始，而不是从失败 diff 上继续修改。

---

## 2. 修改范围与安全边界

### 2.1 允许修改范围

前置检查通过后，仅允许：

```text
M  openspec/schemas/superspec/schema.yaml
?? docs/rectification/16-superspec-phase3b-minimal-safe-schema-override-reimplementation-report.md
```

### 2.2 禁止修改范围

```text
openspec/config.yaml
openspec/schemas/superspec/**          # schema.yaml 除外
openspec/specs/**
openspec/changes/**
docs/rectification/00-* ... docs/rectification/15-*
AGENT.md
AGENTS.md
docs/README.md
work-items/**
.claude/**
.opencode/**
业务代码目录
测试目录
依赖、锁文件、.gitignore
```

### 2.3 禁止命令与行为

```text
git add / commit / push / pull / merge / rebase / reset / restore / checkout -- / clean / stash
git worktree add / remove / prune
任何 /opsx:* lifecycle 命令
SuperSpec apply / verify / finalize
Superpowers 安装、初始化、运行或配置注入
Claude Code / opencode 配置修改
真实业务实现或测试改动
```

---

## 3. 开始前只读门禁

执行并记录：

```bash
git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git log --oneline --decorate -8
git ls-files -- \
  openspec/config.yaml \
  openspec/schemas/superspec/schema.yaml \
  docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md \
  docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md \
  docs/rectification/07-superspec-config-gate-syntax-fix-report.md \
  docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md \
  docs/rectification/09-superspec-phase2-final-gate-correction-and-admission-closure-report.md \
  docs/rectification/10-superspec-phase3-execution-readiness-and-safety-gate-audit-report.md \
  docs/rectification/11-superspec-phase3a-repository-execution-policy-and-schema-safety-override-design-report.md \
  docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md \
  docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md \
  docs/rectification/14-superspec-phase3b-failed-schema-diff-restoration-and-evidence-closure-report.md \
  docs/rectification/15-superspec-phase3b-restoration-final-state-evidence-and-failed-record-admission-report.md
git diff -- openspec/schemas/superspec/schema.yaml
```

同时只读确认 `openspec/config.yaml` 中仍包含 Phase 2D 的两条阻断语义。

必须满足：

| 条件 | 通过标准 |
|---|---|
| 分支 | `chore/superspec-governance-migration` |
| 工作区 | 开始时完全 clean |
| 证据链 | `05-*` 至 `15-*` 均进入 HEAD |
| Schema 基线 | `schema.yaml` 开始时与 HEAD 一致 |
| Config 门禁 | Phase 3 阻断文本仍存在 |

若不满足，不新增报告，不做修改，仅回传阻断证据。

---

## 4. 修改前证据快照

在修改 schema 前，必须以脚本或等价只读方式提取并在 `16-*report.md` 中记录：

1. HEAD `schema.yaml` 的 SHA-256、行数、字节数；
2. YAML 顶层 keys；
3. artifacts id 列表与总数；
4. 对以下节点的定位与字段摘要：
   - 顶层 `description`
   - artifact `apply`
   - artifact `verify`
   - artifact `finalize`
   - 顶层 `apply` phase block
5. 风险关键词的修改前命中摘要：

```text
superpowers:
using-git-worktrees
subagent-driven-development
test-driven-development
requesting-code-review
executing-plans
finishing-a-development-branch
git add
git commit
merge
push
pull request
PR
cleanup
/opsx:continue
```

禁止仅写“已定位”，必须提供实际节点/行号或脚本输出摘要。

---

## 5. 最小补丁实施原则

### 5.1 顶层 description

允许：

- 在现有描述基础上新增项目安全覆盖说明；
- 将“canonical automatic execution”明确限定为 upstream reference / not enabled by default in this repository。

不得：

- 删除整段 upstream 流程来源说明；
- 以短描述整体替换原描述而丢失追踪内容。

### 5.2 `apply`

需要表达：

```text
Gate B
approved implementation tool
未批准前不得运行 Superpowers
未批准前不得创建 implementation worktree
未批准前不得启动 subagent-driven-development
未批准前不得修改业务代码或测试
apply receipt 不等于授权
```

实施约束：

- 优先插入 gate 前言及 override clause；
- 原 canonical apply 逻辑如保留，必须明确写为仅在未来独立批准并完成能力验证后才可执行；
- 不得整体删除原 apply phase 说明。

### 5.3 `verify`

需要表达：

```text
Verification PASS does not authorize finalize or Git closeout.
Gate D approval is required before any closeout.
```

实施约束：

- 局部替换任何默认 `PASS → /opsx:continue → finalize` 的无门禁路径；
- 不删除 verify 的验证职责和证据要求。

### 5.4 `finalize`

默认行为必须改为：

```text
manual closeout receipt / recommendation only
```

并明确：

```text
Do not execute git add/commit/merge/push.
Do not create/update/comment on a pull request.
Do not clean up/remove worktrees or delete branches.
```

实施约束：

- upstream canonical 自动 closeout 流程允许保留为明确标记的：
  `NON-EXECUTABLE UPSTREAM REFERENCE — DO NOT FOLLOW IN THIS REPOSITORY-SAFE MODE`
- 任何仍保留的命令步骤必须落在上述非执行参考声明下，不能仍作为默认执行指令。
- 禁止直接删除整个 canonical closeout 长段落以缩减风险。

---

## 6. 硬性 Diff 与结构边界

### 6.1 非目标节点保持一致

修改后必须以 YAML parser 比较 HEAD 与工作树，并证明：

- artifacts id 列表完全一致；
- `brainstorm`、`proposal`、`design`、`specs`、`tasks`、`plan` 的解析内容完全一致；
- 改变的节点仅为：
  - 顶层 `description`
  - artifact `apply`
  - artifact `verify`
  - artifact `finalize`
  - 顶层 `apply` phase block 中必要的 instruction 文本
- dependencies / requires 结构未因本阶段被擅自改变。

### 6.2 Diff 数量红线

执行：

```bash
git diff --stat -- openspec/schemas/superspec/schema.yaml
git diff --numstat -- openspec/schemas/superspec/schema.yaml
git diff --unified=3 -- openspec/schemas/superspec/schema.yaml
```

硬性要求：

| 指标 | 门槛 |
|---|---|
| 删除行数 | `<= 30` |
| 整段 canonical workflow 删除 | 禁止 |
| 非目标 artifact 内容变化 | `0` |
| 未授权文件变化 | `0` |

若删除超过 30 行或发生整段重写：

- 不得自评 `PASS`；
- 不得继续反复编辑来掩盖 diff；
- 生成 `16-*report.md`，结论为 `FAIL / BLOCKED`，如实记录差异；
- 等待 ChatGPT 判断是否再次恢复或调整授权。

---

## 7. 安全语义断言与残留审查

### 7.1 必须断言的安全语义

在修改后，对实际可执行 instruction 文本进行只读断言，报告原始输出。需覆盖：

```text
repository-safe human-gated override
Gate B
approved implementation tool
Gate D
Verification PASS does not authorize finalize
closeout receipt
NON-EXECUTABLE UPSTREAM REFERENCE
Do not execute git add
Do not execute git commit
Do not execute git merge
Do not execute git push
Do not create, update, or comment on a pull request
Do not clean up or remove a worktree
```

文字可以与 schema 实际语法需要相适配，但每一语义均必须有可复核命中证据。

### 7.2 残留风险审查

对修改后 schema 中的以下命中项逐条列出位置与上下文判定：

```text
superpowers:
worktree
subagent
git add
git commit
merge
push
pull request
PR
cleanup
/opsx:continue
```

每个命中必须被归类为：

| 类别 | 含义 |
|---|---|
| 禁止性安全规则 | 明确要求不得执行 |
| 非执行 upstream 参考 | 明确标记为 reference only / do not follow |
| 经 Gate B 或 Gate D 条件约束的未来路径 | 尚未默认启用 |
| 未受控可执行残留 | 阻断，阶段必须 FAIL |

只要存在“未受控可执行残留”，不得通过。

---

## 8. OpenSpec 验证与最终状态

### 8.1 验证命令

```bash
openspec schemas
openspec validate --all --json
openspec validate --all
```

通过标准：

```text
superspec (project)
11 passed, 0 failed
```

### 8.2 最终 Git 状态

创建报告后执行并记录：

```bash
git status --short --branch --untracked-files=all
git diff --name-only
git diff --stat
git diff --numstat -- openspec/schemas/superspec/schema.yaml
```

通过时最终范围必须仅为：

```text
 M openspec/schemas/superspec/schema.yaml
?? docs/rectification/16-superspec-phase3b-minimal-safe-schema-override-reimplementation-report.md
```

---

## 9. 必须新增的执行报告

新增且仅新增：

```text
docs/rectification/16-superspec-phase3b-minimal-safe-schema-override-reimplementation-report.md
```

### 9.1 必需章节

```markdown
# DiagnoseToolPy SuperSpec Phase 3B-D 最小化 Schema 安全覆盖重新实施报告

## 1. 执行摘要
## 2. Phase 3B 失败、恢复与重做准入依据
## 3. 开始前基线提交与工作区洁净性核验
## 4. 修改前 Schema 风险命中与结构快照
## 5. 最小安全覆盖实施内容
## 6. Diff 统计、Hunk 分类与数量红线核验
## 7. HEAD 与工作树结构保持性验证
## 8. 安全语义断言原始输出
## 9. 高风险关键词残留逐项审查
## 10. OpenSpec 验证结果
## 11. 最终 Git 可见变更集合
## 12. 保护范围确认
## 13. 结论
```

### 9.2 结论格式

全部满足时，只能写：

```text
- Phase 3B-D 实施结果：PASS（最小安全覆盖 patch 已实施并通过证据核验）
- Phase 3 执行就绪判定：仍为 NOT READY
- 是否允许安装或运行 Superpowers：否
- 是否允许执行真实业务 SuperSpec apply：否
- 是否允许执行 SuperSpec finalize：否
- 是否允许提交 schema.yaml 与 16-*report.md：待 ChatGPT 人工审核
- 是否允许进入后续隔离能力验证阶段：待 ChatGPT 人工审核
```

任一红线失败时写：

```text
- Phase 3B-D 实施结果：FAIL / BLOCKED
- Phase 3 执行就绪判定：NOT READY
- 是否允许提交本次 schema 变更：否
- 是否允许执行任何 SuperSpec / Superpowers 行为：否
- 阻断原因：<精确 diff 或断言证据>
```

---

## 10. 完成后回传要求

只回传：

```text
docs/rectification/16-superspec-phase3b-minimal-safe-schema-override-reimplementation-report.md
```

不得提交、不得继续验证工具、不得开始业务实现。
