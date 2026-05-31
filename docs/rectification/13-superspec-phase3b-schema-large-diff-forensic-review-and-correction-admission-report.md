# DiagnoseToolPy SuperSpec Phase 3B Schema Large Diff Forensic Review and Correction Admission Report

> 执行阶段：Phase 3B-R  
> 执行工具：Codex  
> 整改工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 整改分支：`chore/superspec-governance-migration`  
> 审计对象：`openspec/schemas/superspec/schema.yaml`  
> 取证目标：判断当前大范围差异是否满足“最小必要安全覆盖”

## 1. 执行摘要

- 取证结论：`FORENSIC PASS / CORRECTION REQUIRED`
- 是否满足最小必要安全覆盖：`否`
- 是否允许直接批准当前 12 号 schema 变更：`否`
- 是否建议恢复到 HEAD 基线后重做：`是`

当前 `schema.yaml` 的工作树版本相对 HEAD 产生了大范围重写：`69 insertions`、`536 deletions`，总差异为 605 行。按本阶段要求，这一规模必须证明“每一处删除都为安全覆盖所必需”，否则不能进入准入批准。

本次取证未修改任何既有文件，仅读取 `git status`、`git diff`、`git show`、YAML 解析结果与工作树内容。

## 2. 前置状态核验

### 2.1 当前未提交集合

```text
## chore/superspec-governance-migration...origin/chore/superspec-governance-migration
 M openspec/schemas/superspec/schema.yaml
?? docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
```

结论：

- 未提交范围仍仅为 `openspec/schemas/superspec/schema.yaml`
- `12-*` 报告仍为未跟踪文件
- 未发现其他工作树修改

### 2.2 跟踪状态

```text
100644 dace86869c0d03c43846c4208d59bd0eb765cb21 0	openspec/schemas/superspec/schema.yaml
```

说明：

- HEAD 中的 `schema.yaml` blob 可追踪
- 当前工作树版本与该 blob 明显不同

## 3. 版本对比基础事实

### 3.1 文件统计

- HEAD 行数：`776`
- 工作树行数：`309`
- HEAD SHA-256：`4e995dea77481c31f1cdec34f3e855951d8f7fbdda7f0529e0e30750721b9a2b`
- 工作树 SHA-256：`06445b490f2892ce4950a9fdecac6d8041e330949ba0442dc465e0ff48f132c7`

### 3.2 顶层 keys

HEAD 与工作树一致：

```text
['name', 'version', 'description', 'artifacts', 'apply']
```

### 3.3 artifacts 列表

HEAD 与工作树的 artifact id 列表一致，均为 9 项：

```text
['brainstorm', 'proposal', 'design', 'specs', 'tasks', 'plan', 'apply', 'verify', 'finalize']
```

结论：

- artifact 名称未删除、未改名、未合并
- 但 artifact 内容发生了大规模重写

## 4. 结构对比结论

### 4.1 被修改的 artifact

仅以下 artifact 的字段发生变化：

- `apply`
- `verify`
- `finalize`

另有顶层 `description` 发生变化。

### 4.2 未受影响的 artifact

以下 artifact 的结构与内容未见差异：

- `brainstorm`
- `proposal`
- `design`
- `specs`
- `tasks`
- `plan`

这表明本次 diff 不是全文件随机漂移，而是集中修改安全门禁与执行语义相关节点。

## 5. diff 证据

### 5.1 `git diff --stat`

```text
 openspec/schemas/superspec/schema.yaml | 605 ++++-----------------------------
 1 file changed, 69 insertions(+), 536 deletions(-)
```

### 5.2 `git diff --numstat`

```text
69	536	openspec/schemas/superspec/schema.yaml
```

### 5.3 `git diff --summary`

```text
warning: in the working copy of 'openspec/schemas/superspec/schema.yaml', LF will be replaced by CRLF the next time Git touches it
```

说明：

- summary 输出未显示新增/删除文件，仅有换行符警告
- 说明风险集中于内容重写，而不是文件集扩散

### 5.4 关键 hunks

`git diff --unified=3` 一共 5 个 hunk：

```text
@@ -1,34 +1,19 @@
@@ -183,18 +168,18 @@ artifacts:
@@ -245,13 +230,12 @@ artifacts:
@@ -268,370 +252,19 @@ artifacts:
@@ -639,138 +272,38 @@ apply:
```

#### Hunk 1: 顶层 description

目标内修改：

- 将顶层说明改为 repository-safe human-gated override 语义
- 明确 `apply` 不自动授权真实实现
- 明确 `verify PASS` 不自动授权 `finalize`
- 明确 `finalize` 默认是人工 closeout receipt

判定：

- 属于目标范围内修改
- 但其文字覆盖力度很高，替换了原先对 canonical workflow 的完整说明

#### Hunk 2: `apply` artifact

目标内修改：

- 将 `apply` description 改为人审门禁收据
- 用更强的 Gate B 阻断替换原先“由 `/opsx:apply` 生成”的 canonical 说明

判定：

- 属于目标范围内修改
- 内容是必要的安全覆盖方向

#### Hunk 3: `verify` artifact

目标内修改：

- 将 PASS 的后续语义从 `/opsx:continue → finalize` 改为“停在人工批准边界”
- 明确需要独立 Gate D 批准

判定：

- 属于目标范围内修改
- 语义安全收口合理

#### Hunk 4: `finalize` artifact

目标内修改：

- 将 `finalize` description 改为人工 closeout receipt
- 删除了 canonical 作用链中的 merge / push / PR comment / cleanup / escape hatch / borrowed logic 大段说明

疑似删除：

- canonical git-side closeout 说明
- feature branch / worktree / PR 预审前提
- 具体 closeout 执行步骤 1-12
- PR comment subroutine
- borrowed logic 与重建方法
- escape hatch manual skill invocation

判定：

- 删除规模极大
- 虽然目标是禁止自动 closeout，但本次直接把整段 canonical 行为说明几乎全部抹去，未提供逐项保留或替代对照
- 对“最小必要安全覆盖”而言，证据不足

#### Hunk 5: 顶层 `apply:` phase block

目标内修改：

- 删除 canonical apply 工作流的大段内容
- 将 apply 语义收敛为 Gate B 收据、验证边界和禁止自动 closeout

疑似删除：

- pre-flight commit/change artifacts to feature branch
- `superpowers:using-git-worktrees`
- `superpowers:subagent-driven-development`
- TDD / code-review 传递链
- 2b fallback 说明
- worktree / branch / merge / push / archive 的 canonical 流程

判定：

- 该块删除了大量原始执行流说明
- 即便其中若干语义与当前安全覆盖冲突，仍缺少“为何必须整块删除而不能最小替换”的证据

## 6. 逐项安全审查

### 6.1 是否删除了原 superspec 工作流必要 artifact/instruction

结论：`是，删除了大量必要执行流说明，但未删除 artifact 名称本身。`

解释：

- `apply` / `verify` / `finalize` 三个 artifact 仍保留
- 但是 canonical 执行步骤、worktree / subagent / PR closeout / cleanup 逻辑被大面积移除
- 这意味着 upstream 可追踪的行为说明被大幅压缩

### 6.2 是否将 upstream 可追踪结构压缩为不可维护的新 schema

结论：`有这个风险，且当前证据不足以排除。`

原因：

- 从 776 行压缩到 309 行，删除幅度过大
- finalize 相关原始结构几乎被全替换
- apply 相关 canonical 工作流也被整块重写
- 当前没有逐条保留对照表证明每一处删除都不可替代

### 6.3 是否存在“为了移除高风险语义而整体删除正常流程能力”的做法

结论：`存在明显迹象。`

表现：

- canonical finalize 自动 closeout 流程被整个移除
- canonical apply 的 worktree / subagent / TDD / review 流程被整个移除
- 虽然这些能力对本项目当前安全模式不应自动执行，但它们被从 schema 语义中整体抹除，而不是保留为受控、可追踪的非默认路径

### 6.4 是否满足“最小必要安全覆盖”

结论：`否。`

理由：

- 缺少修改前命中点与修改后安全断言的完整对照
- 缺少逐项残留风险清单
- 缺少可复核的删减必要性说明
- 当前 diff 规模过大，无法在审计层面证明是最小 patch

## 7. 与安全覆盖无关的变化判定

结论：`无明显无关扩散，但存在过度删减。`

说明：

- 变更主要集中在顶层 description、apply/verify/finalize 三个安全相关节点
- 未见其他 artifact 被改写
- 因此不是“波及其它模块”的问题
- 但仍是“安全目标范围内过度大改”的问题

## 8. 需要补充的证据

本阶段若要进入批准判断，至少还需要：

1. 修改前命中点列表
2. 修改后安全断言的原始输出
3. 高风险残留项逐条审查
4. 完整可复核 diff 依据
5. 对 536 行删除的逐段必要性说明

缺少上述材料时，不应批准当前 12 号变更。

## 9. 结论

- 取证结论：`FORENSIC PASS / CORRECTION REQUIRED`
- 对当前 schema 大范围差异的准入判定：`不通过`
- 对后续动作建议：`恢复到 HEAD 基线后，以最小 patch 重做，并补齐证据链`

本报告仅用于阻断当前大范围差异的直接批准，不修改任何文件，不进入下一阶段。
