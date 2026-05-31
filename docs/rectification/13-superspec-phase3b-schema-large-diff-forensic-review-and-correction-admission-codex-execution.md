# DiagnoseToolPy × SuperSpec Phase 3B-R：Schema 大范围差异取证与纠偏准入判定 — Codex 执行任务书

> 任务编号：Phase 3B-R / Document No. 13  
> 执行工具：Codex（只读取证执行端）  
> 生成日期：2026-05-31  
> 目标工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 目标分支：`chore/superspec-governance-migration`  
> 本任务书管理规则：**保存在仓库外，不得复制或提交到项目仓库。**  
> 当前状态：Phase 3B 尚未通过；现有未提交 `schema.yaml` 修改和 `12-*report.md` 必须冻结，不得提交、覆盖、恢复或继续修补。

---

## 0. 可直接粘贴给 Codex 的启动 Prompt

```text
你现在负责执行 DiagnoseToolPy × danielhanold/superspec 整改工作的 Phase 3B-R：Schema 大范围差异取证与纠偏准入判定。

目标工作区：
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance

目标分支：
chore/superspec-governance-migration

请先完整读取并严格执行仓库外任务书：
<替换为本机实际路径>/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-codex-execution.md

重要结论：
1. 你上一次生成的 12-*report.md 自评为 PASS，但尚未通过 ChatGPT 审核。
2. 审核发现严重阻断：报告显示 openspec/schemas/superspec/schema.yaml 的未提交差异为 69 insertions、536 deletions。Phase 3B 的批准目标是“最小必要安全覆盖”，该规模无法在缺少详细证据时被批准。
3. 12-*report.md 还缺少任务书要求的修改前命中点、修改后安全断言实际输出、高风险残留逐项审查，以及完整可复核 diff 依据。
4. 因此，本阶段不再修改 schema。本阶段只能读取证，判断当前差异是否发生了超范围删减，并为后续“恢复基线后最小重做”或“证明确属必要变更”提供证据。

绝对禁止：
- 不得编辑、格式化、覆盖或恢复 openspec/schemas/superspec/schema.yaml；
- 不得编辑、删除或覆盖 docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md；
- 不得修改任何已有文件；
- 不得执行 git add、commit、push、pull、merge、rebase、reset、restore、checkout --、clean、stash；
- 不得执行 git worktree add/remove/prune；
- 不得执行任何 /opsx:* lifecycle 命令、SuperSpec apply/verify/finalize；
- 不得安装或运行 Superpowers；
- 不得修改业务代码、测试或工具目录。

只允许：
- 运行 git status、git diff、git show、git ls-files、git grep 等只读命令；
- 运行 Python/YAML 只读解析脚本，对 HEAD 版本与当前工作树版本进行比较；
- 在前置状态与预期一致时，仅新增：
  docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md

必须完成的取证：
A. 确认当前未提交范围仍仅为：
   M  openspec/schemas/superspec/schema.yaml
   ?? docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
   若已经出现其他修改，停止新增报告并直接回传阻断证据。
B. 对 HEAD 中 schema.yaml 与工作树 schema.yaml 做 YAML 解析和结构对比：
   - 文件总行数、SHA-256；
   - 顶层 keys；
   - artifacts 的 id 列表、总数；
   - apply/verify/finalize 相关节点是否被删除、改名、合并或大幅压缩；
   - 除 apply/verify/finalize 与顶层 description 外，是否有其他 artifact/instruction 内容被改变或删除。
C. 运行并记录：
   - git diff --stat -- openspec/schemas/superspec/schema.yaml
   - git diff --numstat -- openspec/schemas/superspec/schema.yaml
   - git diff --summary -- openspec/schemas/superspec/schema.yaml
   - git diff --unified=3 -- openspec/schemas/superspec/schema.yaml
   报告无需无脑粘贴全部数百行 diff，但必须逐 hunk 归类：目标内修改、疑似删除、与安全覆盖无关的变化。
D. 重点判定：
   - 536 行删除是否删除了原 superspec 工作流必要 artifact/instruction；
   - 是否将 upstream 可追踪结构压缩为不可维护的新 schema；
   - 是否存在“为了移除高风险语义而整体删除正常流程能力”的做法；
   - 当前变更是否满足“最小必要安全覆盖”。
E. 生成结论，只能为：
   - FORENSIC PASS / CORRECTION REQUIRED：证据表明当前大范围 diff 不满足最小修改原则，必须在后续阶段恢复到 HEAD 基线后以小范围 patch 重做；
   - FORENSIC PASS / EVIDENCE SUFFICIENT FOR REVIEW：仅当你能逐项证明所有删除均为安全覆盖所必需、非目标节点未受损且 schema 可维护时使用；不得直接写 Phase 3B PASS。
F. 最终仅回传 13-*report.md，不提交、不恢复、不修补、不进入下一阶段。
```

---

## 1. 审核结论与启动原因

Phase 3B 的目标是修改项目本地 `openspec/schemas/superspec/schema.yaml`，将 upstream canonical 自动化行为收缩为 repository-safe human-gated override。授权边界允许修改该文件，但同时明确要求：

- 仅做实现安全覆盖目标所需的最小改动；
- 不重写无关 artifacts；
- 保留 superspec workflow 结构与 upstream 来源可追踪性；
- 对高风险残留文本进行逐项审查；
- 通过精确 diff 证明修改范围合理。

Codex 回传的 `12-*report.md` 中存在以下严重审核阻断：

```text
openspec/schemas/superspec/schema.yaml | 605 ++++-----------------------------
1 file changed, 69 insertions(+), 536 deletions(-)
```

在没有结构对比、完整差异归类和非目标节点不受损证明的情况下，该修改规模不能被视为“最小安全覆盖”，也不能提交。

---

## 2. 当前阶段处置决定

### 2.1 Phase 3B 状态

```text
- Phase 3B 审核结论：不通过 / 待纠偏
- 是否允许提交 schema.yaml 与 12-*report.md：否
- 是否允许恢复或继续编辑 schema.yaml：否，需先完成取证
- Phase 3 执行就绪判定：NOT READY
- 是否允许安装或运行 Superpowers：否
- 是否允许执行真实业务 SuperSpec apply：否
- 是否允许执行 SuperSpec finalize：否
```

### 2.2 为什么先取证而不是直接重做

当前未提交差异本身是一次治理执行偏离的关键证据。如果立即 `restore` 或覆盖重写：

- 会丢失“为何 536 行被删除”的可核验证据；
- 无法判断 Codex 是删除了无关能力、误解 schema 结构，还是存在任务书未覆盖的结构性原因；
- 后续最小 patch 约束无法针对真实失败原因加强。

因此，Phase 3B-R 只做取证，不做修复。

---

## 3. 允许与禁止范围

### 3.1 前置状态预期

开始时，工作区应仍保持 Phase 3B 回传状态：

```text
 M openspec/schemas/superspec/schema.yaml
?? docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
```

如出现其他修改或未跟踪文件，停止，不新增 `13-*report.md`，仅在聊天中回传状态阻断。

### 3.2 唯一允许新增文件

仅在前置状态与预期一致后，允许新增：

```text
docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md
```

### 3.3 不得修改的文件

不得修改任何已有文件，包括但不限于：

```text
openspec/schemas/superspec/schema.yaml
openspec/config.yaml
openspec/schemas/superspec/**        # 包含 schema.yaml，均只读
openspec/specs/**
openspec/changes/**
docs/rectification/00-* ... docs/rectification/12-*
AGENT.md
AGENTS.md
docs/README.md
work-items/**
.claude/**
.opencode/**
业务代码、测试与依赖文件
```

### 3.4 禁止执行的命令/行为

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
Superpowers 安装、初始化、运行或配置变更
任何真实代码实现
```

---

## 4. 必须执行的只读取证

### 4.1 状态与基线检查

执行并记录：

```bash
git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git log --oneline --decorate -6
git ls-files -- \
  openspec/schemas/superspec/schema.yaml \
  docs/rectification/11-superspec-phase3a-repository-execution-policy-and-schema-safety-override-design-report.md
```

必须确认：

- 分支仍为 `chore/superspec-governance-migration`；
- `11-*report.md` 已进入 HEAD；
- `schema.yaml` 为已跟踪文件；
- 初始未提交范围只包含 `schema.yaml` 修改和 `12-*report.md` 未跟踪文件。

### 4.2 Diff 取证命令

执行并记录：

```bash
git diff --stat -- openspec/schemas/superspec/schema.yaml
git diff --numstat -- openspec/schemas/superspec/schema.yaml
git diff --summary -- openspec/schemas/superspec/schema.yaml
git diff --unified=3 -- openspec/schemas/superspec/schema.yaml
```

报告必须包含：

- `--stat` 与 `--numstat` 完整输出；
- `--unified=3` 的 hunk 数量；
- 对每一组 hunk 的分类表，不得只粘贴统计数字。

分类表模板：

| Hunk / 影响节点 | 变化类型 | 是否属于授权目标 | 是否必要 | 风险判定 | 证据摘要 |
|---|---|---:|---:|---|---|
| 顶层 description |  |  |  |  |  |
| artifacts apply |  |  |  |  |  |
| artifacts verify |  |  |  |  |  |
| artifacts finalize |  |  |  |  |  |
| 顶层 apply phase |  |  |  |  |  |
| 其他被改/删节点 |  |  |  |  |  |

如果有大量 hunk 无法逐项在报告中合理归类，直接判定 `CORRECTION REQUIRED`。

---

## 5. HEAD 与工作树 Schema 结构对比

### 5.1 只读文件提取方式

可使用：

```bash
git show HEAD:openspec/schemas/superspec/schema.yaml
```

将 HEAD 内容只读加载到脚本内，不得将其写回工作树。

### 5.2 必须比较的指标

使用 Python + YAML parser 或等价只读脚本，比较：

| 指标 | HEAD 版本 | 工作树版本 | 差异解释 |
|---|---:|---:|---|
| UTF-8 文本总行数 |  |  |  |
| 字节长度 |  |  |  |
| SHA-256 |  |  |  |
| YAML 顶层 keys |  |  |  |
| artifacts 总数 |  |  |  |
| artifacts id 列表 |  |  |  |
| 顶层 phase block keys |  |  |  |
| apply instruction 长度/结构 |  |  |  |
| verify instruction 长度/结构 |  |  |  |
| finalize instruction 长度/结构 |  |  |  |

### 5.3 必须验证的非目标保留性

Phase 3B 原授权目标不包含整体缩减 workflow。必须检查：

- `brainstorm`、`proposal`、`design`、`specs`、`tasks`、`plan` 等非目标 artifacts 是否保持存在；
- 它们的 instruction 是否发生改变或删除；
- schema 的 workflow dependency / requires 结构是否变化；
- 原本为 upstream 来源追踪、fallback、validation 或说明用途的内容是否被无理由移除；
- 删除是否改变了 artifact 生成合同，而不仅是消除自动 Git 行为。

只要非目标 artifact 或 workflow 合同发生未经任务书授权的实质变化，结论必须为 `CORRECTION REQUIRED`。

---

## 6. 对 `12-*report.md` 证据完备性的复核

对既有 `12-*report.md` 只读复核，回答：

| 要求 | `12-*report.md` 是否提供 | 是否足以验收 | 缺口 |
|---|---|---|---|
| 开始时工作区洁净证据 |  |  |  |
| 修改前风险关键词实际命中输出 |  |  |  |
| 修改后安全语义断言脚本与原始输出 |  |  |  |
| 高风险残留逐项解释 |  |  |  |
| 完整精确 diff / hunk 归类 |  |  |  |
| 最小必要修改证明 |  |  |  |

不得修改 `12-*report.md` 来补证据；只在新报告中记录复核结论。

---

## 7. 必须新增的取证报告

在初始未提交范围符合预期时，新增且仅新增：

```text
docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md
```

### 7.1 必需章节

```markdown
# DiagnoseToolPy SuperSpec Phase 3B-R Schema 大范围差异取证与纠偏准入判定报告

## 1. 执行摘要
## 2. Phase 3B ChatGPT 审核阻断结论承接
## 3. 当前未提交状态冻结确认
## 4. Schema Diff 统计与 Hunk 分类
## 5. HEAD 与工作树 YAML 结构对比
## 6. 非目标 Artifact 与 Workflow 合同保留性核验
## 7. 12 号报告证据完备性复核
## 8. 是否满足最小必要安全覆盖的判定
## 9. 后续纠偏建议与精确允许范围
## 10. 最终 Git 可见变更集合
## 11. 保护范围确认
## 12. 结论
```

### 7.2 结论格式

若确认差异过大、不满足最小修改原则或证据不足，必须写：

```text
- Phase 3B-R 取证执行结果：PASS（只读取证已完成）
- Phase 3B 准入结论：CORRECTION REQUIRED
- 是否允许提交 schema.yaml 与 12-*report.md：否
- 是否允许在下一阶段恢复 HEAD 基线并重新实施最小安全覆盖 patch：待 ChatGPT 人工审核
- Phase 3 执行就绪判定：NOT READY
- 是否允许安装或运行 Superpowers：否
- 是否允许执行真实业务 SuperSpec apply：否
- 是否允许执行 SuperSpec finalize：否
```

仅当可以逐项证明所有大规模删除均必要、非目标结构未损害、`12-*report.md` 证据缺口可由本取证报告完整补齐时，可写：

```text
- Phase 3B-R 取证执行结果：PASS（只读取证已完成）
- Phase 3B 准入结论：EVIDENCE SUFFICIENT FOR CHATGPT REVIEW
- 是否允许提交 schema.yaml 与 12-*report.md：待 ChatGPT 人工审核
- Phase 3 执行就绪判定：NOT READY
- 是否允许安装或运行 Superpowers：否
- 是否允许执行真实业务 SuperSpec apply：否
- 是否允许执行 SuperSpec finalize：否
```

不得直接宣告 Phase 3B 已通过或允许进入 Superpowers 验证。

---

## 8. 最终状态与回传

生成 `13-*report.md` 后仅执行并记录：

```bash
git status --short --branch --untracked-files=all
git diff --name-only
git diff --stat
```

预期状态：

```text
 M openspec/schemas/superspec/schema.yaml
?? docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
?? docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md
```

完成后仅回传：

```text
docs/rectification/13-superspec-phase3b-schema-large-diff-forensic-review-and-correction-admission-report.md
```

不得提交、恢复、修补或继续进入后续阶段。
