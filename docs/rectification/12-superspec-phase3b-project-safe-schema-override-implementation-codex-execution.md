# DiagnoseToolPy × SuperSpec Phase 3B：项目级安全覆盖 Schema 实施 — Codex 执行任务书

> 任务编号：Phase 3B / Document No. 12  
> 执行工具：Codex（受控治理整改执行端）  
> 生成日期：2026-05-31  
> 目标工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 目标分支：`chore/superspec-governance-migration`  
> 本任务书管理规则：**保存在项目仓库外，不得复制或提交到项目仓库。**  
> 前置条件：**用户已人工提交 `11-superspec-phase3a-repository-execution-policy-and-schema-safety-override-design-report.md`，且目标工作区无未提交变更。**

---

## 0. 可直接粘贴给 Codex 的启动 Prompt

```text
你现在负责执行 DiagnoseToolPy × danielhanold/superspec 整改工作的 Phase 3B：项目级安全覆盖 Schema 实施。

目标工作区：
E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance

目标分支：
chore/superspec-governance-migration

请先完整读取并严格执行仓库外任务书：
<替换为本机实际路径>/12-superspec-phase3b-project-safe-schema-override-implementation-codex-execution.md

执行背景：
1. Phase 3 审计结论为 NOT READY，禁止真实业务 SuperSpec apply/finalize。
2. Phase 3A 设计审计已选择“方案 A：项目级安全覆盖 Schema”为推荐路线；该路线经 ChatGPT 审核批准进入受控实施。
3. 本阶段只把 superspec schema 的高风险默认执行语义改为本项目的人审安全模式，不安装或运行 Superpowers，不执行业务实现，不执行 apply/finalize。
4. Phase 3A 报告中虽然提及 templates/apply.md 与 templates/finalize.md，但报告未证明这些模板实际存在或承载关键执行逻辑。因此本阶段默认只授权修改已定位的：
   openspec/schemas/superspec/schema.yaml
   若在只读检查中发现安全覆盖无法仅通过该文件完整实现，必须停止修改并回传证据，不得自行扩大到其他 schema/template/config 文件。

开始前必须确认：
- 当前分支为 chore/superspec-governance-migration；
- 工作区干净；
- openspec/config.yaml 与 docs/rectification/05-* 至 11-* 已被当前 HEAD 跟踪；
- config.yaml 中两条 Phase 3 禁止 apply/finalize 的门禁仍存在且未弱化。

本阶段允许变化仅限：
M  openspec/schemas/superspec/schema.yaml
?? docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md

不得修改：
- openspec/config.yaml
- 除 schema.yaml 外的 openspec/schemas/**
- openspec/specs/**、openspec/changes/**
- AGENTS.md、AGENT.md、docs/README.md、work-items/**
- .claude/**、.opencode/**
- 业务代码、测试、依赖文件
- docs/rectification/00-* 至 11-* 既有报告

不得执行：
git add/commit/push/pull/merge/rebase/reset/clean/stash；
git worktree add/remove/prune；
任何 /opsx:* lifecycle 命令；
SuperSpec apply/verify/finalize；
任何 Superpowers 安装、运行或配置注入；
任何 Claude Code/opencode 工具配置修改或真实业务实现。

目标修改要求：
A. 保留 superspec 项目 schema 与 upstream 基线来源可追踪性；在 schema description 或安全覆盖相关说明中明确该项目启用了 repository-safe human-gated override，不再默认采用自动 Git closeout。
B. 修改 apply 相关 instruction/phase 语义，使其明确：
   - 真实实现只能在 Gate B 经人工批准后由批准的实现端启动；
   - 当前批准前不得运行 Superpowers、创建实现 worktree、启动 subagent-driven-development 或更改业务代码；
   - apply receipt 不得被解释为自动授权实现或 Git 行为。
C. 修改 verify 相关 instruction/phase 语义，使其明确：
   - verify 仅确认证据、一致性与范围；
   - PASS 不自动授权 finalize；
   - PASS 后必须等待独立 Gate D 人工批准 closeout。
D. 修改 finalize 相关 instruction/phase 语义，使其默认成为人工 closeout receipt / 建议步骤记录阶段：
   - 不自动执行 git add、commit、merge、push、PR 创建或更新、PR comment、worktree cleanup 或 branch 删除；
   - 仅记录经人工批准后由用户实际执行或明确授权执行的 closeout 结果；
   - 任何未来自动 closeout 模式必须由独立阶段另行批准，不得在本阶段启用。
E. 对 schema 中仍保留的 fallback / escape hatch / skill 文本做一致性审查：不得存在未加人审限制、仍会默认引导自动 merge/push/cleanup 的指令。仅对 schema.yaml 内必要段落做最小修改，不重写无关 artifacts。

修改后必须：
1. 对 schema.yaml 做关键词与结构检查，证明 apply/verify/finalize 的安全覆盖语义已存在，且默认自动 Git closeout 指令不再作为可直接执行路径。
2. 执行：
   openspec schemas
   openspec validate --all --json
   openspec validate --all
3. 使用 git diff 精确审查，仅 schema.yaml 与新增 12 报告可见。
4. 新增且仅新增：
   docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md

报告结论必须保持：
- Phase 3B 实施结果：PASS 或 FAIL
- Phase 3 执行就绪判定：仍为 NOT READY
- 是否允许安装或运行 Superpowers：否
- 是否允许执行真实业务 SuperSpec apply：否
- 是否允许执行 SuperSpec finalize：否
- 是否允许进入后续隔离能力验证阶段：待 ChatGPT 人工审核

不要提交任何文件，不要继续后续阶段。最终仅回传 12-*report.md 供 ChatGPT 审核。
```

---

## 1. 审核依据与本阶段定位

Phase 3A 报告已完成设计审计，并推荐：

> **方案 A：项目级安全覆盖 Schema。**

该方案的理由成立：项目既需要保留 `danielhanold/superspec` 的来源和 workflow 结构，又不能直接承接 canonical `apply/finalize` 的高风险自动行为，尤其是：

- Superpowers / subagent / worktree 未经批准即进入真实实现；
- `verify PASS` 被默认连接到 closeout；
- `finalize` 自动执行 `git add`、commit、merge、push、PR 操作、comment 与 worktree cleanup。

本阶段负责把上述风险在**项目本地 schema** 中收缩为人审安全模式。此阶段仍不是实现工具验证或真实业务开发阶段。

---

## 2. 关键范围修正：不得依据未证实路径扩大修改面

Phase 3A 报告在变更蓝图中列出：

```text
openspec/schemas/superspec/schema.yaml
openspec/schemas/superspec/templates/apply.md
openspec/schemas/superspec/templates/finalize.md
如有必要 openspec/config.yaml
```

其中，报告已具体定位高风险执行节点位于：

```text
openspec/schemas/superspec/schema.yaml
```

但未提供证据证明 `templates/apply.md` 或 `templates/finalize.md` 存在、被 schema 引用、或承载需要覆盖的行为。本阶段采用最小安全边界：

### 2.1 默认唯一允许修改的既有文件

```text
openspec/schemas/superspec/schema.yaml
```

### 2.2 唯一允许新增报告

```text
docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
```

### 2.3 若仅修改 `schema.yaml` 无法完整安全覆盖

若只读分析证明：

- schema 引用了外置模板且高风险指令实际存在于其他文件；或
- 验证失败且必须修改其他 schema 文件才能实现安全模式；

则必须：

1. 停止实施，不修改未授权文件；
2. 若尚未修改 `schema.yaml`，不新增报告文件，仅在聊天回传阻断证据；
3. 若已完成部分授权范围修改，再生成 `12-*report.md`，结论写为 `FAIL / BLOCKED`，记录需要新增授权的精确路径与理由；
4. 不得自行修改 templates 或 `openspec/config.yaml`。

---

## 3. 前置门禁

### 3.1 只读命令

进入整改 worktree 后执行：

```bash
git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git log --oneline --decorate -6
git ls-files -- \
  openspec/config.yaml \
  openspec/schemas/superspec/schema.yaml \
  docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md \
  docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md \
  docs/rectification/07-superspec-config-gate-syntax-fix-report.md \
  docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md \
  docs/rectification/09-superspec-phase2-final-gate-correction-and-admission-closure-report.md \
  docs/rectification/10-superspec-phase3-execution-readiness-and-safety-gate-audit-report.md \
  docs/rectification/11-superspec-phase3a-repository-execution-policy-and-schema-safety-override-design-report.md
```

仅使用只读检索确认：

```bash
git grep -n -E "Do not execute real business implementation through SuperSpec apply until Phase 3 approves|Do not execute Git/PR closeout through SuperSpec finalize until Phase 3 approves" -- openspec/config.yaml
git grep -n -i -E "superpowers|subagent|worktree|apply|verify|finalize|git add|git commit|merge|push|pull request|PR|cleanup" -- openspec/schemas/superspec/schema.yaml
```

Windows shell 中如上述引号/转义不兼容，可使用等价只读检索命令；必须在报告中写明实际命令及输出摘要。

### 3.2 开始条件

必须满足：

| 条件 | 必须满足的状态 |
|---|---|
| 当前分支 | `chore/superspec-governance-migration` |
| 初始工作区 | 干净，无修改或未跟踪文件 |
| 基线证据 | `05-*` 至 `11-*` 报告均已进入当前 HEAD |
| config 门禁 | Phase 2D 两条禁止性门禁仍存在 |
| schema 文件 | `openspec/schemas/superspec/schema.yaml` 已被跟踪且为高风险节点承载文件 |

前置失败时，不得新增 `12-*report.md`，只回传阻断证据。

---

## 4. 允许与禁止变更边界

### 4.1 前置检查通过后的授权变更集合

```text
M  openspec/schemas/superspec/schema.yaml
?? docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
```

### 4.2 禁止修改文件与路径

```text
openspec/config.yaml
openspec/schemas/superspec/**        # schema.yaml 除外
openspec/specs/**
openspec/changes/**
docs/rectification/00-* ... docs/rectification/11-*
AGENT.md
AGENTS.md
docs/README.md
work-items/**
.claude/**
.opencode/**
src/**
backend/**
frontend/**
tests/**
test/**
依赖文件与锁文件
.gitignore
```

### 4.3 禁止执行操作

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
任何 /opsx:* lifecycle 命令
SuperSpec apply / verify / finalize
Superpowers 安装、初始化、运行或配置
Claude Code / opencode 配置修改
任何真实业务代码或测试执行实现
```

允许：

```text
git status / diff / log / ls-files / grep / worktree list 等只读检查
openspec schemas
openspec validate --all --json
openspec validate --all
只读 YAML/text parser 断言脚本
```

---

## 5. `schema.yaml` 安全覆盖目标

编辑 `openspec/schemas/superspec/schema.yaml` 时，仅在支持以下行为变更所需的节点做最小改动。

### 5.1 Schema 标识与来源追踪

必须保留：

- schema 名称/可被 `openspec schemas` 识别的结构；
- 上游基线来源可追踪性，不得伪装为未经修改的 upstream canonical 行为。

应在适当 description/instruction 语义中明确：

- 当前为 **DiagnoseToolPy repository-safe human-gated override**；
- 保留 superspec 工作流结构，但 `apply/finalize` 行为由项目安全策略覆盖；
- upstream canonical automatic closeout 在本项目中**未被默认批准**。

不要为此新增无规范依据的 YAML 顶层字段，避免破坏 schema parser；优先修改已有 description/instruction 文本。

### 5.2 `apply`：人审后的实现入口，而不是自动执行授权

安全覆盖后，相关 apply instruction/phase 必须表达：

1. `apply` 前存在 **Gate B**：
   - 人工批准实现工具；
   - 人工批准允许修改路径/任务范围；
   - 人工批准 worktree 策略；
   - 人工批准测试、review 与回退策略。
2. 未满足 Gate B 时：
   - 不得启动真实业务实现；
   - 不得运行 Superpowers；
   - 不得创建实现 worktree；
   - 不得调度 subagent-driven-development；
   - 不得修改代码或测试。
3. `apply.md` / receipt（如 workflow 生成该产物）仅记录批准状态、执行证据与阻断信息，不得自行等价为批准。
4. Claude Code / opencode 的实现职责不得由 schema 自动选择或升级；必须引用“approved implementation tool”语义。

### 5.3 `verify`：验证不等于 closeout 授权

安全覆盖后，相关 verify instruction 必须表达：

1. verify 负责检查测试证据、scope compliance、未闭合风险与 receipt 一致性；
2. verify `PASS` 只能表明验证通过，**不得自动授权 finalize 或 Git closeout**；
3. verify PASS 后必须进入 **Gate D：人工批准 Git closeout**；
4. 不得保留无门禁的 “PASS → `/opsx:continue` 直接执行 finalize 自动 closeout” 行为描述。

### 5.4 `finalize`：默认改为人工 closeout receipt

安全覆盖后，相关 finalize instruction/phase 必须表达：

1. `finalize` 默认仅产生或更新 closeout receipt / closeout recommendation；
2. 不得自动执行：
   - `git add`
   - `git commit`
   - `git merge`
   - `git push`
   - 创建、更新或评论 PR
   - `git worktree remove` / cleanup
   - 删除 branch
3. 只有在 Gate D 已人工批准，并由用户人工执行或在未来独立批准的自动 closeout 模式下执行后，finalize receipt 才可记录结果；
4. 如 schema 中保留 upstream canonical 行为的历史说明，必须明确其在本项目中是**禁用的参考行为**，不能成为可执行 instruction；
5. 任何 escape hatch / fallback 也不得绕过 Gate D。

---

## 6. 修改前后的文本与结构断言

### 6.1 修改前必须记录的命中点

在报告中记录对 `schema.yaml` 的只读定位结果，至少包括含有下列风险关键词的节点或行号摘要：

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
PR
cleanup
/opsx:continue
```

未命中的关键词应写明“未命中”，不得虚构。

### 6.2 修改后必须进行的安全语义断言

使用等价脚本或只读文本检查，断言 `schema.yaml` 的可执行 instruction 语义已覆盖以下概念。具体实现可根据真实 schema 结构调整，但报告必须记录脚本和结果：

```text
repository-safe human-gated override
Gate B
approved implementation tool
Do not start real business implementation
Do not run Superpowers
Gate D
Verification PASS does not authorize finalize
closeout receipt
Do not execute git add
Do not execute git commit
Do not execute git merge
Do not execute git push
Do not create, update, or comment on a pull request
Do not clean up or remove a worktree
```

### 6.3 高风险残留检查

修改后，对 schema 中仍出现的下列关键词进行审查：

```text
git add
git commit
merge
push
pull request
PR
cleanup
worktree remove
/opsx:continue
superpowers:
```

判定规则：

- 关键词可因历史说明、禁用说明或受 Gate B/Gate D 限制的描述保留；
- 若其仍存在为默认直接执行命令/可执行 instruction，判定为失败；
- 报告必须逐项说明每个仍保留风险关键词为何不是未受控自动执行路径。

---

## 7. 验证要求

### 7.1 OpenSpec 验证

执行：

```bash
openspec schemas
openspec validate --all --json
openspec validate --all
```

通过标准：

- `superspec (project)` 仍可见；
- `openspec validate --all --json` 为 `11 passed, 0 failed`；
- `openspec validate --all` 为 `11 passed, 0 failed`。

### 7.2 Git 范围验证

执行并写入报告：

```bash
git status --short --branch --untracked-files=all
git diff --name-only
git diff --stat
git diff -- openspec/schemas/superspec/schema.yaml
```

最终可见范围必须仅为：

```text
 M openspec/schemas/superspec/schema.yaml
?? docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
```

若出现任何其他路径，阶段结果必须为 `FAIL`，不得自行清理或修改未经授权文件。

---

## 8. 必须新增的执行报告

前置检查通过并完成本阶段实施后，新增且仅新增：

```text
docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
```

### 8.1 报告必需章节

```markdown
# DiagnoseToolPy SuperSpec Phase 3B 项目级安全覆盖 Schema 实施报告

## 1. 执行摘要
## 2. Phase 3A 审核批准路线与本阶段范围收窄说明
## 3. 基线提交、工作区洁净性与前置门禁核验
## 4. 修改前 Schema 高风险行为定位证据
## 5. Schema 安全覆盖实施内容
## 6. Apply / Verify / Finalize 修改后行为说明
## 7. 修改后安全语义断言与高风险残留审查
## 8. OpenSpec 验证结果
## 9. 配置与 Schema 精确 Diff
## 10. 最终 Git 可见变更集合
## 11. 保护范围确认
## 12. 结论
```

### 8.2 必须明确的事实

报告必须声明：

- Phase 3A 推荐的方案 A 已获 ChatGPT 审核批准进入受控实施；
- 本阶段因证据不足，未授权修改 `templates/apply.md`、`templates/finalize.md` 或 `openspec/config.yaml`；
- 若只修改 `schema.yaml` 已满足覆盖目标，明确说明依据；
- 若不能满足，必须记录阻断并判为 FAIL，不得扩大范围；
- schema 安全覆盖只解决默认危险行为问题，**不等于 Superpowers 可用、实现工具已验证或真实业务执行已获准**。

### 8.3 结论格式

全部通过时仅可写：

```text
- Phase 3B 实施结果：PASS（项目级安全覆盖 schema 已实施并通过结构验证）
- Phase 3 执行就绪判定：仍为 NOT READY
- 是否允许安装或运行 Superpowers：否
- 是否允许执行真实业务 SuperSpec apply：否
- 是否允许执行 SuperSpec finalize：否
- 是否允许提交本阶段 schema 与报告：待 ChatGPT 人工审核
- 是否允许进入后续隔离能力验证阶段：待 ChatGPT 人工审核
```

发生任一阻断或验证失败时写：

```text
- Phase 3B 实施结果：FAIL / BLOCKED
- Phase 3 执行就绪判定：NOT READY
- 是否允许提交本阶段变更：否
- 是否允许执行任何后续 SuperSpec / Superpowers 行为：否
- 阻断原因：<精确证据>
```

---

## 9. 完成后回传要求

完成后只回传：

```text
docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
```

不得提交本阶段变更，不得安装工具，不得继续进入隔离验证或业务实现。
