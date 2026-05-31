# DiagnoseToolPy × SuperSpec Phase 3B-C：失败 Schema 差异恢复与证据链闭合 — Codex 执行任务书

> 任务编号：Phase 3B-C / Document No. 14  
> 执行工具：Codex（受控恢复与证据执行端）  
> 生成日期：2026-05-31  
> 目标工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 目标分支：`chore/superspec-governance-migration`  
> 本任务书管理规则：**保存在仓库外，不得复制或提交到项目仓库。**  
> 特别授权：本阶段在完成恢复前取证后，**仅授权恢复失败的 `schema.yaml` 未提交修改至当前 HEAD 基线**；不授权重新实施 schema 安全覆盖。

---

## 0. 可直接粘贴给 Codex 的启动 Prompt

```text
你现在负责执行 DiagnoseToolPy × danielhanold/superspec 整改工作的 Phase 3B-C：失败 Schema 差异恢复与证据链闭合。

目标工作区：
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance

目标分支：
chore/superspec-governance-migration

请先完整读取并严格执行仓库外任务书：
<替换为本机实际路径>/14-superspec-phase3b-failed-schema-diff-restoration-and-evidence-closure-codex-execution.md

已审核结论：
1. 12-*report.md 自评 PASS 已被否决，不得作为准入依据。
2. 13-*report.md 的核心取证结论已被 ChatGPT 接受：当前 schema.yaml 差异为 69 insertions / 536 deletions，虽然修改集中在 description、apply、verify、finalize 相关节点，但属于目标范围内的过度删减，不满足“最小必要安全覆盖”。
3. 当前禁止提交失败的 schema.yaml 修改；下一次真正实施安全覆盖必须在恢复到 HEAD 基线、提交失败证据链之后另行开始。
4. 13-*report.md 未附生成自身后的最终 Git 状态与保护范围确认。本阶段报告必须补齐该证据闭环，但不得编辑 13-*report.md。

本阶段目标：
- 冻结并核验现有失败变更和 12/13 报告状态；
- 在恢复前再次记录 schema.yaml 的大范围 diff 证据；
- 使用唯一获准的恢复命令，将 openspec/schemas/superspec/schema.yaml 恢复至当前 HEAD 基线；
- 新增 14-*report.md，记录恢复前后状态、恢复命令、失败结论承接、未来最小重做准入要求；
- 不重新修改 schema，不开始 Phase 3B 的第二次实施。

开始前预期状态必须仅为：
 M openspec/schemas/superspec/schema.yaml
?? docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
?? docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md

若出现其他修改/未跟踪文件，停止：不要 restore，不要新增报告，只回传阻断状态。

恢复前必须只读记录：
- git branch --show-current
- git rev-parse HEAD
- git status --short --branch --untracked-files=all
- git diff --stat -- openspec/schemas/superspec/schema.yaml
- git diff --numstat -- openspec/schemas/superspec/schema.yaml
- git diff --name-only
- 确认 12-* 与 13-* 报告存在且保持未跟踪
- 确认 13-* 的 `FORENSIC PASS / CORRECTION REQUIRED` 结论存在

在上述前置状态严格匹配且证据记录完成后，本阶段唯一允许对既有文件执行的写操作是：

git restore --source=HEAD -- openspec/schemas/superspec/schema.yaml

恢复后必须确认：
- git diff -- openspec/schemas/superspec/schema.yaml 为空；
- git diff --name-only 为空；
- schema.yaml 不再出现在 git status 修改集合中；
- 12-* 与 13-* 报告仍存在且未被修改；
- 当前仅允许新增 14-* 报告。

新增且仅新增：
docs/rectification/14-superspec-phase3b-failed-schema-diff-restoration-and-evidence-closure-report.md

报告结论必须为：
- Phase 3B-C 恢复执行结果：PASS 或 FAIL
- Phase 3B 原实施准入结论：CORRECTION REQUIRED，失败 schema 变更不得提交
- 是否已恢复 schema.yaml 至 HEAD 基线：是/否
- Phase 3 执行就绪判定：仍为 NOT READY
- 是否允许安装或运行 Superpowers：否
- 是否允许执行真实业务 SuperSpec apply/finalize：否
- 是否允许人工提交 12-*、13-*、14-* 失败/恢复证据报告：待 ChatGPT 人工审核
- 是否允许重新开展最小 Schema 安全覆盖实施：待 ChatGPT 人工审核

不得执行 git add、commit、push、pull、merge、rebase、reset、clean、stash、worktree add/remove/prune；不得修改任何历史报告、配置、schema 其他文件、业务代码或工具目录；不得运行任何 /opsx:*、SuperSpec lifecycle 或 Superpowers 命令。

最终只回传 14-*report.md 给用户，等待 ChatGPT 审核。
```

---

## 1. 本阶段审核依据与决定

### 1.1 已接受的事实

Phase 3B-R 取证报告已经证明：

- 当前 `schema.yaml` 工作树版本相对于 `HEAD` 为 `69 insertions / 536 deletions`；
- HEAD 为 776 行，工作树版本为 309 行；
- artifacts id 仍保留 9 项；
- 改动主要集中于顶层 `description`、`apply`、`verify`、`finalize` 与顶层 `apply:` phase block；
- 非目标 artifact 未发现直接改动；
- 但 canonical apply/finalize 的大量说明与执行结构被整块删除，无法证明属于最小必要安全覆盖；
- 结论为 `FORENSIC PASS / CORRECTION REQUIRED`。

### 1.2 本阶段不做什么

本阶段不是第二次 schema 实施，不允许尝试：

- 在失败 diff 上继续打补丁；
- 手工缩减 diff；
- 重新编写 `apply/verify/finalize`；
- 引入 templates 或修改 `config.yaml`；
- 运行验证以假装原失败实施通过；
- 安装/验证 Superpowers。

### 1.3 为什么允许恢复

失败 diff 的取证证据已由 `12-*` 与 `13-*` 报告保留。继续将失败 `schema.yaml` 修改悬挂在工作树中，会阻塞后续治理工作，也增加误提交风险。因此本阶段特别授权将**唯一失败既有修改文件**恢复至 `HEAD`，并以 `14-*report.md` 闭合恢复证据。

---

## 2. 开始前状态门禁

### 2.1 执行只读检查

进入目标工作区后执行：

```bash
git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git diff --stat -- openspec/schemas/superspec/schema.yaml
git diff --numstat -- openspec/schemas/superspec/schema.yaml
git diff --name-only
```

只读确认文件存在：

```text
docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md
```

并确认 `13-*report.md` 中含有：

```text
FORENSIC PASS / CORRECTION REQUIRED
```

### 2.2 必须匹配的开始状态

```text
## chore/superspec-governance-migration...origin/chore/superspec-governance-migration
 M openspec/schemas/superspec/schema.yaml
?? docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
?? docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md
```

且：

```text
openspec/schemas/superspec/schema.yaml | 605 ++++-----------------------------
1 file changed, 69 insertions(+), 536 deletions(-)
```

若状态不匹配：

- 不得执行恢复；
- 不得新增 `14-*report.md`；
- 仅向用户回传阻断原因与只读输出。

---

## 3. 特别授权的唯一恢复操作

仅在第 2 节前置状态完全满足并已记录后，执行：

```bash
git restore --source=HEAD -- openspec/schemas/superspec/schema.yaml
```

### 3.1 该授权的边界

本命令仅用于撤销 Phase 3B 未通过的 `schema.yaml` 未提交内容，恢复到当前已提交的安全基线。

不得使用：

```bash
git restore .
git restore --staged ...
git checkout -- ...
git reset ...
git clean ...
```

不得恢复或删除：

```text
docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md
```

上述两份报告是失败执行及取证证据，必须保留。

---

## 4. 恢复后验证

执行并记录：

```bash
git status --short --branch --untracked-files=all
git diff --name-only
git diff --stat
git diff -- openspec/schemas/superspec/schema.yaml
```

恢复后、创建 14 报告前，预期为：

```text
## chore/superspec-governance-migration...origin/chore/superspec-governance-migration
?? docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
?? docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md
```

且：

```text
git diff --name-only
(empty output)

git diff --stat
(empty output)

git diff -- openspec/schemas/superspec/schema.yaml
(empty output)
```

若 `schema.yaml` 仍有 diff，或者其他既有文件发生修改，报告必须判为 `FAIL`，且不得进一步操作。

---

## 5. 唯一允许新增的报告

恢复验证通过后，新增且仅新增：

```text
docs/rectification/14-superspec-phase3b-failed-schema-diff-restoration-and-evidence-closure-report.md
```

### 5.1 必需章节

```markdown
# DiagnoseToolPy SuperSpec Phase 3B-C 失败 Schema 差异恢复与证据链闭合报告

## 1. 执行摘要
## 2. Phase 3B 与 Phase 3B-R 审核结论承接
## 3. 恢复前冻结状态与失败 Diff 证据
## 4. 获准恢复操作及精确命令
## 5. 恢复后 Schema 基线一致性验证
## 6. 失败证据报告保留状态
## 7. 最终 Git 可见变更集合
## 8. 后续最小重做准入约束
## 9. 保护范围确认
## 10. 结论
```

### 5.2 报告必须记录的内容

#### 恢复前

记录：

- 当前分支与 HEAD；
- `schema.yaml` 的 `69 insertions / 536 deletions` 统计；
- 12、13 报告仍未跟踪且存在；
- `13-*` 结论为 `CORRECTION REQUIRED`。

#### 恢复操作

明确写明唯一执行的恢复命令：

```bash
git restore --source=HEAD -- openspec/schemas/superspec/schema.yaml
```

#### 恢复后

证明：

- `schema.yaml` diff 为空；
- 没有其他已跟踪文件发生变化；
- 12 与 13 报告仍被保留；
- 新增 14 报告后最终状态应仅为：

```text
?? docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
?? docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md
?? docs/rectification/14-superspec-phase3b-failed-schema-diff-restoration-and-evidence-closure-report.md
```

### 5.3 后续最小重做约束

报告必须提出下一轮 Phase 3B 重做时至少遵循：

1. 从已恢复的 HEAD schema 基线开始；
2. 修改前生成风险命中点清单；
3. 以小范围 hunk patch 修改，禁止整块替换数百行指令；
4. 原始 canonical 行为如需禁用，应保留为明确标记的非执行参考或仅替换直接可执行语句，不整体抹除可追踪说明；
5. 修改后提供安全断言原始输出及残留高风险关键词逐项解释；
6. 若 diff 再次明显扩大，必须停止并先请求扩大授权，而不是自判 PASS。

---

## 6. 禁止范围

除第 3 节唯一授权的 restore 和新增 `14-*report.md` 外，不得执行任何写操作。

### 6.1 禁止修改

```text
openspec/config.yaml
openspec/schemas/superspec/schema.yaml          # restore 后不得再编辑
openspec/schemas/superspec/**                   # 其他文件始终不得编辑
openspec/specs/**
openspec/changes/**
docs/rectification/00-* ... docs/rectification/13-*  # 12/13 只保留，不编辑
AGENT.md
AGENTS.md
docs/README.md
work-items/**
.claude/**
.opencode/**
业务代码、测试、依赖与锁文件
```

### 6.2 禁止命令或动作

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
git worktree add/remove/prune
任何 /opsx:* lifecycle 命令
SuperSpec apply / verify / finalize
Superpowers 安装、运行或配置
任何真实业务代码实现
```

---

## 7. 结论格式与回传

### 7.1 恢复成功时

```text
- Phase 3B-C 恢复执行结果：PASS（失败 schema 差异已恢复，证据链已闭合）
- Phase 3B 原实施准入结论：CORRECTION REQUIRED，失败 schema 变更不得提交
- 是否已恢复 schema.yaml 至 HEAD 基线：是
- Phase 3 执行就绪判定：仍为 NOT READY
- 是否允许安装或运行 Superpowers：否
- 是否允许执行真实业务 SuperSpec apply：否
- 是否允许执行 SuperSpec finalize：否
- 是否允许人工提交 12-*、13-*、14-* 失败/恢复证据报告：待 ChatGPT 人工审核
- 是否允许重新开展最小 Schema 安全覆盖实施：待 ChatGPT 人工审核
```

### 7.2 恢复失败或状态不符合时

```text
- Phase 3B-C 恢复执行结果：FAIL / BLOCKED
- Phase 3B 原实施准入结论：CORRECTION REQUIRED
- 是否允许提交任何 Phase 3B 相关未提交资产：否
- Phase 3 执行就绪判定：NOT READY
- 阻断原因：<精确输出与证据>
```

### 7.3 回传要求

成功生成报告后，只回传：

```text
docs/rectification/14-superspec-phase3b-failed-schema-diff-restoration-and-evidence-closure-report.md
```

不得自行提交报告，不得重新开始 schema 实施。
