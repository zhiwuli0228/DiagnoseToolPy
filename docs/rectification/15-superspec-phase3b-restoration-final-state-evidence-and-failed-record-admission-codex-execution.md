# DiagnoseToolPy × SuperSpec Phase 3B-C1：恢复后最终状态补证与失败证据提交准入 — Codex 执行任务书

> 任务编号：Phase 3B-C1 / Document No. 15  
> 执行工具：Codex（只读核验与补证报告执行端）  
> 生成日期：2026-05-31  
> 目标工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 目标分支：`chore/superspec-governance-migration`  
> 本任务书管理规则：**保存在项目仓库外，不得复制或提交到项目仓库。**  
> 当前状态：Phase 3B 失败变更已声明恢复，但 `14-*report.md` 遗漏“报告生成后的最终 Git 可见集合”证据。本阶段只补证，不恢复、不修改 schema、不重新实施。

---

## 0. 可直接粘贴给 Codex 的启动 Prompt

```text
你现在负责执行 DiagnoseToolPy × danielhanold/superspec 整改工作的 Phase 3B-C1：恢复后最终状态补证与失败证据提交准入。

目标工作区：
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance

目标分支：
chore/superspec-governance-migration

请先完整读取并严格执行仓库外任务书：
<替换为本机实际路径>/15-superspec-phase3b-restoration-final-state-evidence-and-failed-record-admission-codex-execution.md

已审核结论：
1. Phase 3B 的 schema 修改已被否决：12-*report.md 的 PASS 自评无效，不得作为准入依据。
2. 13-*report.md 已证明失败差异为 69 insertions / 536 deletions，结论 `FORENSIC PASS / CORRECTION REQUIRED` 已获接受。
3. 14-*report.md 报告称已执行唯一获准的恢复命令，将 openspec/schemas/superspec/schema.yaml 恢复至 HEAD；该恢复方向正确。
4. 但 14-*report.md 未包含“创建 14 报告后的最终 Git 状态”，只记录了创建前只剩 12/13 未跟踪的状态。因此，12/13/14 目前仍不得提交；本阶段必须以只读核验补齐最终状态证据。

本阶段不得修改任何已有文件，不得再次执行 git restore，也不得重新实施 schema。

开始前必须只读核验：
- 当前分支为 chore/superspec-governance-migration；
- schema.yaml 已无任何未提交 diff；
- 当前工作区仅包含以下未跟踪文件：
  ?? docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
  ?? docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md
  ?? docs/rectification/14-superspec-phase3b-failed-schema-diff-restoration-and-evidence-closure-report.md
- 除上述三个报告外，不存在任何 tracked 修改或其他 untracked 文件；
- 12/13/14 报告均存在，且 13 中仍含 CORRECTION REQUIRED，14 中仍声明 schema 已恢复。

若以上状态不完全匹配，立即停止：不新增报告、不修改文件，只回传阻断命令输出。

若完全匹配，仅允许新增：
docs/rectification/15-superspec-phase3b-restoration-final-state-evidence-and-failed-record-admission-report.md

15 号报告必须记录：
A. 14 号报告的证据缺口：遗漏生成自身后的最终 Git 可见集合，因此需本报告补证。
B. 当前 `git status --short --branch --untracked-files=all` 的原始输出。
C. 当前 `git diff --name-only`、`git diff --stat`、`git diff -- openspec/schemas/superspec/schema.yaml` 的原始输出，证明 schema clean。
D. 当前 `git ls-files --others --exclude-standard -- docs/rectification/` 或等价输出，证明未跟踪报告集合仅为 12/13/14；创建本报告后最终集合应增加 15。
E. 明确证据解释：
   - 12 是失败实施事实报告，其 PASS 结论已被否决；
   - 13 是取证与 CORRECTION REQUIRED 依据；
   - 14 是恢复动作与恢复前后状态记录，但其最终状态缺口由 15 补齐；
   - 15 是提交准入补证依据。
F. 创建 15 号报告后再次运行并粘贴最终：
   - git status --short --branch --untracked-files=all
   - git diff --name-only
   - git diff --stat
   - git diff -- openspec/schemas/superspec/schema.yaml
   最终状态必须仅显示 12/13/14/15 为未跟踪文件，schema.yaml 不得出现。

严格禁止：
- 修改或覆盖 schema.yaml、12-*、13-*、14-* 或任何已有文件；
- git add、commit、push、pull、merge、rebase、reset、restore、checkout --、clean、stash；
- git worktree add/remove/prune；
- 任何 /opsx:* lifecycle、SuperSpec apply/verify/finalize、Superpowers 命令；
- 任何业务代码、测试、工具配置变更。

报告结论仅可写：
- Phase 3B-C1 补证执行结果：PASS 或 FAIL/BLOCKED
- Phase 3B 原实施准入结论：CORRECTION REQUIRED，失败 schema 变更不得提交
- schema.yaml 是否保持 HEAD clean：是/否
- 是否完成 12/13/14/15 失败与恢复证据集合闭合：是/否
- Phase 3 执行就绪判定：仍为 NOT READY
- 是否允许安装或运行 Superpowers：否
- 是否允许执行真实业务 SuperSpec apply/finalize：否
- 是否允许人工提交 12-* 至 15-* 报告：待 ChatGPT 人工审核
- 是否允许重新开展最小 Schema 安全覆盖实施：待 ChatGPT 人工审核

完成后只回传 15-*report.md，等待 ChatGPT 审核。不得自行提交、不得开始重做。
```

---

## 1. 本阶段启动原因

Phase 3B-C 已报告执行：

```bash
git restore --source=HEAD -- openspec/schemas/superspec/schema.yaml
```

并声明恢复后 `schema.yaml` 不再有 diff。这满足恢复动作的核心方向。

但是，Phase 3B-C 任务书要求在新增 `14-*report.md` 后记录最终 Git 可见集合，预期为：

```text
?? docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
?? docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md
?? docs/rectification/14-superspec-phase3b-failed-schema-diff-restoration-and-evidence-closure-report.md
```

实际 `14-*report.md` 只记录了创建自身前的状态：

```text
?? docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
?? docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md
```

因此，不能直接批准提交失败/恢复证据链。Phase 3B-C1 仅用于补齐这一最终状态缺口。

---

## 2. 本阶段执行性质

### 2.1 只读核验为主

本阶段不再修改或恢复任何既有文件，仅验证：

- 失败的 `schema.yaml` 修改是否确实已消失；
- `12-*`、`13-*`、`14-*` 是否为当前唯一未跟踪资产；
- 是否存在未经授权的新修改或文件；
- 失败与恢复证据链能否进入人工提交审核。

### 2.2 唯一允许新增文件

前置检查通过后，仅允许新增：

```text
docs/rectification/15-superspec-phase3b-restoration-final-state-evidence-and-failed-record-admission-report.md
```

---

## 3. 前置状态门禁

### 3.1 必须执行的只读命令

```bash
git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git diff --name-only
git diff --stat
git diff -- openspec/schemas/superspec/schema.yaml
git ls-files --others --exclude-standard -- docs/rectification/
```

同时只读检查：

```text
docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md
docs/rectification/14-superspec-phase3b-failed-schema-diff-restoration-and-evidence-closure-report.md
```

### 3.2 必须满足的状态

```text
## chore/superspec-governance-migration...origin/chore/superspec-governance-migration
?? docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
?? docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md
?? docs/rectification/14-superspec-phase3b-failed-schema-diff-restoration-and-evidence-closure-report.md
```

并且：

```text
git diff --name-only
(empty output)

git diff --stat
(empty output)

git diff -- openspec/schemas/superspec/schema.yaml
(empty output)
```

### 3.3 前置状态不满足时

如出现任一以下情况：

- `schema.yaml` 仍有 diff；
- 有其他 tracked 修改；
- 有 12/13/14 之外的未跟踪资产；
- 三份报告任一缺失；
- `13-*` 不含 `CORRECTION REQUIRED` 或 `14-*` 不含恢复成功声明；

则：

- 不得新增 `15-*report.md`；
- 不得执行任何写操作；
- 仅回传阻断证据。

---

## 4. 允许与禁止范围

### 4.1 唯一允许产物

```text
?? docs/rectification/15-superspec-phase3b-restoration-final-state-evidence-and-failed-record-admission-report.md
```

### 4.2 禁止修改范围

不得修改所有已有文件，包括：

```text
openspec/config.yaml
openspec/schemas/superspec/**
openspec/specs/**
openspec/changes/**
docs/rectification/00-* ... docs/rectification/14-*
AGENT.md
AGENTS.md
docs/README.md
work-items/**
.claude/**
.opencode/**
业务代码、测试、依赖及锁文件
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
git restore
git checkout --
git clean
git stash
git worktree add/remove/prune
任何 /opsx:* lifecycle 命令
SuperSpec apply / verify / finalize
Superpowers 安装、运行或配置变更
任何真实业务代码实现
```

---

## 5. 必须新增的报告

新增：

```text
docs/rectification/15-superspec-phase3b-restoration-final-state-evidence-and-failed-record-admission-report.md
```

### 5.1 必需章节

```markdown
# DiagnoseToolPy SuperSpec Phase 3B-C1 恢复后最终状态补证与失败证据提交准入报告

## 1. 执行摘要
## 2. Phase 3B / 3B-R / 3B-C 审核结论承接
## 3. 14 号报告证据缺口与本阶段补证目标
## 4. 创建本报告前的最终恢复状态核验
## 5. Schema HEAD Clean 与失败变更消失证明
## 6. 12/13/14/15 证据链解释
## 7. 创建本报告后的最终 Git 可见集合
## 8. 保护范围确认
## 9. 后续最小 Schema 覆盖重做准入建议
## 10. 结论
```

### 5.2 创建本报告后的最终状态证据

创建报告后执行并粘贴：

```bash
git status --short --branch --untracked-files=all
git diff --name-only
git diff --stat
git diff -- openspec/schemas/superspec/schema.yaml
git ls-files --others --exclude-standard -- docs/rectification/
```

预期状态：

```text
## chore/superspec-governance-migration...origin/chore/superspec-governance-migration
?? docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
?? docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md
?? docs/rectification/14-superspec-phase3b-failed-schema-diff-restoration-and-evidence-closure-report.md
?? docs/rectification/15-superspec-phase3b-restoration-final-state-evidence-and-failed-record-admission-report.md
```

默认 `git diff` 相关三项均应为空，因为当前只能存在未跟踪报告。

### 5.3 报告结论格式

全部通过时写：

```text
- Phase 3B-C1 补证执行结果：PASS（恢复后最终状态证据已闭合）
- Phase 3B 原实施准入结论：CORRECTION REQUIRED，失败 schema 变更不得提交
- schema.yaml 是否保持 HEAD clean：是
- 是否完成 12/13/14/15 失败与恢复证据集合闭合：是
- Phase 3 执行就绪判定：仍为 NOT READY
- 是否允许安装或运行 Superpowers：否
- 是否允许执行真实业务 SuperSpec apply/finalize：否
- 是否允许人工提交 12-* 至 15-* 报告：待 ChatGPT 人工审核
- 是否允许重新开展最小 Schema 安全覆盖实施：待 ChatGPT 人工审核
```

失败时写：

```text
- Phase 3B-C1 补证执行结果：FAIL / BLOCKED
- Phase 3B 原实施准入结论：CORRECTION REQUIRED
- 是否允许提交 12-* 至 15-* 相关资产：否
- Phase 3 执行就绪判定：NOT READY
- 阻断原因：<精确证据>
```

---

## 6. 回传要求

完成后仅回传：

```text
docs/rectification/15-superspec-phase3b-restoration-final-state-evidence-and-failed-record-admission-report.md
```

不得提交、不得重新修改 schema、不得开始下一轮实施。
