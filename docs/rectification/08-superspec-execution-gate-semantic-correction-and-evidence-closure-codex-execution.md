# DiagnoseToolPy 全面适配 SuperSpec：Phase 2C 执行门禁语义纠偏与证据链闭合执行任务书

> **交付对象**：Codex  
> **执行阶段**：Phase 2C — Execution-Gate Semantic Correction & Evidence Closure  
> **执行任务书定位**：仓库外指令载体，禁止复制或保存到项目仓库  
> **执行工作区**：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> **执行分支**：`chore/superspec-governance-migration`  
> **已采用 Schema**：`danielhanold/superspec` version `4`  
> **上游 Schema Commit**：`e1c8f417ee3601208416d988ba3b37d83ddb63f2`  
> **前置结果**：Phase 2B 已完成 YAML 列表项类型修复，但门禁语义仍未达到 Phase 3 前禁用真实执行的要求  
> **本阶段性质**：只修正 `openspec/config.yaml` 中两条门禁语义，并闭合 Phase 2 系列报告证据链；不进入 Phase 3

---

## 1. 本阶段背景与结论

### 1.1 不得重新执行 Phase 2B

以下任务已经执行完成，不得重跑：

```text
Phase 2B：配置门禁 YAML 类型修正与提交证据链初步复核
```

对应既有报告：

```text
docs/rectification/07-superspec-config-gate-syntax-fix-report.md
```

Phase 2B 已确认：

- `rules.apply` 与 `rules.finalize` 当前均为 YAML list；
- 两条门禁已被修复为字符串列表项；
- `openspec validate --all --json` 为 `11 passed, 0 failed`；
- `docs/rectification/05-*`、`06-*`、`07-*` 仍未提交。

### 1.2 Phase 2B 仍未通过准入的原因

Phase 2B 修复后的规则文本为：

```yaml
rules:
  apply:
    - "Do not start real business implementation for the active change until the active change is authorized and the task scope is clear."

  finalize:
    - "Do not perform Git/PR closeout, merge, or push until verification is green and the repository-specific safety review has approved the action."
```

以上文本虽然已具备正确 YAML 类型，但没有落实当前迁移期硬门禁：

```text
在 Phase 3 完成实现工具、Superpowers、worktree、review 和 Git/PR
安全治理以前，不得对真实业务 change 执行 SuperSpec apply/finalize。
```

其中：

- `rules.apply` 只要求 change 授权与 scope 清晰，可能允许 Phase 3 前开始真实业务实现；
- `rules.finalize` 未明确以 Phase 3 审批为解锁条件，存在误执行 Git/PR closeout 的风险。

### 1.3 本阶段最终目标

本阶段结束时必须满足：

```text
1. `rules.apply` 明确禁止 Phase 3 批准前通过 SuperSpec apply 执行真实业务实现；
2. `rules.finalize` 明确禁止 Phase 3 批准前通过 SuperSpec finalize 执行 Git/PR closeout；
3. 两条规则通过 YAML parser 被证实为对应列表中的字符串项；
4. `openspec validate --all --json` 保持 11 passed, 0 failed；
5. `05-*`、`06-*`、`07-*` 报告状态得到核验，`08-*` 报告成为 Phase 2 系列最终准入依据；
6. Codex 不执行提交，等待用户人工审核后统一提交。
```

---

## 2. 任务书和报告资产纪律

### 2.1 本任务书不得入库

禁止将本文件复制、另存或生成到以下任何路径：

```text
docs/rectification/
docs/
openspec/
项目根目录
```

### 2.2 前序报告只能保留，不得修改

若存在以下文件，必须保留原文，不得编辑、重命名或删除：

```text
docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
docs/rectification/07-superspec-config-gate-syntax-fix-report.md
```

说明：

- `05-*` 记录初始 context/rules 注入；
- `06-*` 记录来源一致性复核与 `current-state` 收窄，其 Phase 3 准入结论已被后续审核否决；
- `07-*` 记录 YAML 类型修复，其 Phase 3 准入结论因门禁语义不足已被后续审核否决；
- 本阶段新增 `08-*` 作为 Phase 2 系列最终审计结论。

### 2.3 本阶段仅允许新增正式报告

```text
docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md
```

---

## 3. 严格允许与禁止范围

### 3.1 允许读取的路径

```text
openspec/config.yaml
openspec/schemas/superspec/schema.yaml
docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
docs/rectification/07-superspec-config-gate-syntax-fix-report.md
AGENTS.md
docs/README.md
work-items/README.md
```

允许使用 Git 只读查询：

```text
openspec/config.yaml
docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
docs/rectification/07-superspec-config-gate-syntax-fix-report.md
```

### 3.2 允许修改的文件

```text
openspec/config.yaml
```

### 3.3 允许新增的文件

```text
docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md
```

### 3.4 严格禁止修改的路径

```text
.gitignore
AGENT.md
AGENTS.md
CLAUDE.md
work-items/**
docs/README.md
docs/00-project/**
docs/01-architecture/**
docs/02-harness/**
docs/03-openspec/**
docs/04-development/**
docs/05-domain/**
docs/06-operations/**
docs/07-templates/**
docs/99-archive/**
docs/rectification/00-*
docs/rectification/01-*
docs/rectification/02-*
docs/rectification/03-*
docs/rectification/04-*
docs/rectification/05-*
docs/rectification/06-*
docs/rectification/07-*
openspec/schemas/**
openspec/specs/**
openspec/changes/**
diagnose_tool/**
frontend/**
tests/**
config/**
data/**
diagnosis_prompt/**
main.py
pyproject.toml
uv.lock
Dockerfile
docker-compose.yml
.github/**
.claude/**
.opencode/**
README.md
README_ZH.md
```

### 3.5 禁止执行的命令类型

严禁执行：

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
git worktree add
git worktree remove
git rm
git mv

openspec init
openspec update
openspec config set
openspec config profile
openspec schema init
openspec schema fork

任何 /opsx:* 或 opsx-* lifecycle 命令
任何 Superpowers skill 或安装命令
```

---

## 4. 启动门禁：核验 Phase 2B 当前状态

在整改 worktree 中执行：

```powershell
Set-Location E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance

git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git diff --stat
git diff --name-only
git diff -- openspec/config.yaml
git ls-files --others --exclude-standard docs/rectification/
```

### 4.1 必须满足

```text
分支：chore/superspec-governance-migration
```

依据 Phase 2B 回传，预期起始可见集合为：

```text
M  openspec/config.yaml
?? docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
?? docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
?? docs/rectification/07-superspec-config-gate-syntax-fix-report.md
```

### 4.2 HEAD 分支处理规则

Phase 2B 报告记录的基线 HEAD 为：

```text
d34c81ba6355309ebe577006c3b981fde8d08736
```

若当前 HEAD 不同，不得直接判定失败；必须通过第 5 节 Git 历史核验判断是否发生用户人工提交。

### 4.3 立即停止条件

若出现下列任意内容，立即停止且不得修改 config：

```text
- 任意 `*-codex-execution.md` 文件进入仓库工作树；
- 任意 schema、living specs、openspec/changes、业务或工具目录变更；
- 任意未能由 Git 历史解释的额外路径。
```

停止回传：

```text
STOPPED: Phase 2B pending-change set differs from the authorized Phase 2C starting state.
Unexpected paths:
- <path>
No Phase 2C changes were made.
```

---

## 5. Phase 2 系列提交证据链核验

### Step 1：核验三份既有报告是否存在及其跟踪状态

执行：

```powershell
Test-Path docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
Test-Path docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
Test-Path docs/rectification/07-superspec-config-gate-syntax-fix-report.md

git ls-files docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
git ls-files docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
git ls-files docs/rectification/07-superspec-config-gate-syntax-fix-report.md

git log --oneline --follow -- docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
git log --oneline --follow -- docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
git log --oneline --follow -- docs/rectification/07-superspec-config-gate-syntax-fix-report.md
git log --oneline --follow -- openspec/config.yaml
git show --stat --oneline HEAD
```

### Step 2：证据链判定

| 状态 | 处理方式 |
|---|---|
| `05/06/07` 均为未跟踪文件，config 为 modified | 按当前 Phase 2C 正常继续，最终提交需包含 `05/06/07/08` 与 config |
| 任一报告已提交，且 config 提交关系可解释 | 记录提前提交事实，继续修 config，最终提交只包含仍未提交报告与本阶段修正 |
| 任一报告不存在且未出现在 Git 历史 | `BLOCKED`，证据缺失，不修改 config |
| config 已提交但其对应报告缺失或不可解释 | `BLOCKED`，证据链不完整，不修改 config |

---

## 6. 修正前 YAML Parser 基线验证

### Step 3：确认可使用 YAML parser

不得安装依赖。依次尝试：

```powershell
python -c "import yaml; print('PyYAML available')"
```

若失败，允许：

```powershell
uv run python -c "import yaml; print('PyYAML available')"
```

两者均失败则停止并报告。

### Step 4：解析当前规则

使用可用的 Python 前缀执行：

```powershell
python -c "import yaml, pathlib, json; d=yaml.safe_load(pathlib.Path('openspec/config.yaml').read_text(encoding='utf-8')); r=d.get('rules') or {}; print('top_keys=', list(d.keys())); print('rule_keys=', list(r.keys())); print('tasks=', json.dumps(r.get('tasks'), ensure_ascii=False)); print('apply=', json.dumps(r.get('apply'), ensure_ascii=False)); print('finalize=', json.dumps(r.get('finalize'), ensure_ascii=False)); assert isinstance(r.get('tasks'), list); assert isinstance(r.get('apply'), list); assert isinstance(r.get('finalize'), list); assert any('Update durable docs, including current-state, only when an approved change alters long-term capabilities' in x for x in r['tasks']); assert any('Do not start real business implementation for the active change until the active change is authorized and the task scope is clear.' == x for x in r['apply']); assert any('Do not perform Git/PR closeout, merge, or push until verification is green and the repository-specific safety review has approved the action.' == x for x in r['finalize']); print('PHASE2B_GATE_BASELINE_CONFIRMED')"
```

若使用 `uv run python` 才可运行，则相应替换命令前缀。

### 必须输出

```text
PHASE2B_GATE_BASELINE_CONFIRMED
```

若门禁文本已被其他操作修改，不得猜测性覆盖；停止并报告实际 parser 输出。

---

## 7. `openspec/config.yaml` 唯一允许修正

仅允许对以下两个字符串做替换，不得修改其他内容。

### 7.1 替换 `rules.apply` 的最后一条门禁

将：

```yaml
    - "Do not start real business implementation for the active change until the active change is authorized and the task scope is clear."
```

替换为：

```yaml
    - "Do not execute real business implementation through SuperSpec apply until Phase 3 approves the implementation tool, Superpowers availability, worktree behavior, review discipline, and Git-safety prerequisites for this repository."
```

### 7.2 替换 `rules.finalize` 的最后一条门禁

将：

```yaml
    - "Do not perform Git/PR closeout, merge, or push until verification is green and the repository-specific safety review has approved the action."
```

替换为：

```yaml
    - "Do not execute Git/PR closeout through SuperSpec finalize until Phase 3 approves repository-specific merge, push, worktree cleanup, and pull-request safety prerequisites."
```

### 7.3 必须保持不变的内容

不得修改：

```text
- schema: superspec
- context 全部内容
- rules.brainstorm / proposal / design / specs / tasks / plan / verify
- rules.apply 除最后门禁字符串外的条目
- rules.finalize 除最后门禁字符串外的条目
```

特别是必须保留已收窄的 tasks 规则：

```yaml
    - Update durable docs, including current-state, only when an approved change alters long-term capabilities, architecture boundaries, operations contracts, or recorded limitations.
```

---

## 8. 修正后 YAML Parser 硬断言

修改后执行：

```powershell
python -c "import yaml, pathlib, json; d=yaml.safe_load(pathlib.Path('openspec/config.yaml').read_text(encoding='utf-8')); r=d.get('rules') or {}; print('top_keys=', list(d.keys())); print('rule_keys=', list(r.keys())); print('tasks=', json.dumps(r.get('tasks'), ensure_ascii=False)); print('apply=', json.dumps(r.get('apply'), ensure_ascii=False)); print('finalize=', json.dumps(r.get('finalize'), ensure_ascii=False)); assert isinstance(r.get('apply'), list); assert isinstance(r.get('finalize'), list); assert any('Do not execute real business implementation through SuperSpec apply until Phase 3 approves the implementation tool, Superpowers availability, worktree behavior, review discipline, and Git-safety prerequisites for this repository.' == x for x in r['apply']); assert any('Do not execute Git/PR closeout through SuperSpec finalize until Phase 3 approves repository-specific merge, push, worktree cleanup, and pull-request safety prerequisites.' == x for x in r['finalize']); assert not any('Do not start real business implementation for the active change until the active change is authorized and the task scope is clear.' == x for x in r['apply']); assert not any('Do not perform Git/PR closeout, merge, or push until verification is green and the repository-specific safety review has approved the action.' == x for x in r['finalize']); print('PHASE3_HARD_GATES_EFFECTIVE')"
```

若需要使用 `uv run python`，相应替换前缀。

必须输出：

```text
PHASE3_HARD_GATES_EFFECTIVE
```

---

## 9. OpenSpec 验证

执行：

```powershell
openspec schemas
openspec validate --all --json
openspec validate --all
```

必须满足：

```text
openspec schemas：识别 superspec (project)
openspec validate --all --json：11 passed, 0 failed
openspec validate --all：11 passed, 0 failed
```

若失败：

- 不得扩大修改范围；
- 不得修改 schema 或 specs；
- 报告结论为 `BLOCKED`；
- 回传完整错误信息。

---

## 10. 新增 Phase 2C 正式报告

必须新增：

```text
docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md
```

报告必须包含：

```markdown
# DiagnoseToolPy SuperSpec Phase 2C 执行门禁语义纠偏与证据链闭合报告

> 执行阶段：Phase 2C
> 执行工具：Codex
> 执行日期：<YYYY-MM-DD>
> 整改工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`
> 整改分支：`chore/superspec-governance-migration`
> 起始 HEAD：`<actual HEAD>`
> Schema：`superspec` version `4`
> 上游 schema commit：`e1c8f417ee3601208416d988ba3b37d83ddb63f2`

## 1. 执行摘要

- 执行结果：PASS / BLOCKED / STOPPED
- Phase 2B 外部审核结论：YAML 类型修正有效，但门禁语义不足，未获提交和 Phase 3 准入批准
- 是否修改 `openspec/config.yaml`：
- 是否建议提交 Phase 2 系列治理变更：
- 是否允许进入 Phase 3：

## 2. Phase 2 系列证据链状态

| 报告 | 是否存在 | 是否 tracked | 是否待提交 | 外部审核状态 |
|---|---:|---:|---:|---|
| `05-superspec-project-context-and-artifact-rules-injection-report.md` | | | | 初始注入证据，保留 |
| `06-superspec-config-source-consistency-and-rule-tightening-report.md` | | | | Phase 3 ALLOW 已被后续审核否决 |
| `07-superspec-config-gate-syntax-fix-report.md` | | | | YAML 修复有效；Phase 3 ALLOW 已被后续审核否决 |
| `08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md` | 是 | 否 | 是 | Phase 2 系列最终准入依据 |

### 是否存在提前提交或证据缺失

```text
<记录 Git 历史核验结论>
```

## 3. 修正前门禁核验

### Parser 输出

```text
<粘贴 PHASE2B_GATE_BASELINE_CONFIRMED 与关键 parsed rules>
```

### 语义不足说明

- `rules.apply`：
- `rules.finalize`：

## 4. 精确修正内容

### `rules.apply`

修改前：

```yaml
<原文>
```

修改后：

```yaml
<新文>
```

### `rules.finalize`

修改前：

```yaml
<原文>
```

修改后：

```yaml
<新文>
```

### 未修改项确认

- `context` 未修改：
- `rules.tasks` 的 durable-docs 收窄规则未修改：
- 其他 artifacts rules 未修改：

## 5. 修正后 Parser 硬断言

```text
<粘贴 PHASE3_HARD_GATES_EFFECTIVE 与关键输出>
```

## 6. OpenSpec 验证结果

### `openspec schemas`

```text
<输出>
```

### `openspec validate --all --json`

```text
<输出摘要>
```

### `openspec validate --all`

```text
<输出>
```

## 7. Git 最终变更集合

### `git status --short --branch --untracked-files=all`

```text
<输出>
```

### `git diff --stat`

```text
<输出>
```

### `git diff --name-only`

```text
<输出>
```

### 未跟踪报告

```text
<输出>
```

## 8. 保护范围确认

- [ ] 未修改 schema、living specs 或 changes
- [ ] 未修改业务、测试、数据或工具目录
- [ ] 未修改 `AGENTS.md`、`work-items/README.md` 或长期文档
- [ ] 未改写 `05-*`、`06-*`、`07-*` 报告
- [ ] 未将执行任务书复制入库
- [ ] 未执行 lifecycle / Superpowers / 禁止 Git 命令

## 9. 提交与 Phase 3 准入结论

- 是否允许人工提交：ALLOW / BLOCK
- 是否允许进入 Phase 3：ALLOW / BLOCK

### 若 `05/06/07` 仍均未提交，提交范围必须为

```text
openspec/config.yaml
docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
docs/rectification/07-superspec-config-gate-syntax-fix-report.md
docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md
```

### 建议 commit message

```text
chore(openspec): enforce governed superspec context and execution gates
```
```

---

## 11. 最终 Git 变更集合门禁

若 `05-*`、`06-*`、`07-*` 均仍未提交，则本阶段成功后的可见集合只能为：

```text
M  openspec/config.yaml
?? docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
?? docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
?? docs/rectification/07-superspec-config-gate-syntax-fix-report.md
?? docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md
```

若 Git 历史证明其中一部分已经由用户提交，则报告必须列出真实待提交集合，不得重复建议提交 tracked 文件。

禁止出现：

```text
docs/rectification/*-codex-execution.md
openspec/schemas/**
openspec/specs/**
openspec/changes/**
AGENT.md
AGENTS.md
work-items/**
任何业务、工具、测试、数据文件
```

---

## 12. Codex 回传要求

执行完成后必须回传：

1. `docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md`；
2. 启动 branch、HEAD 与待提交集合；
3. `05/06/07` 三份报告的存在性、tracked 状态及 Git 历史核验结果；
4. 修正前 `PHASE2B_GATE_BASELINE_CONFIRMED` parser 输出；
5. `openspec/config.yaml` 的精确 diff；
6. 修正后 `PHASE3_HARD_GATES_EFFECTIVE` parser 输出；
7. `openspec schemas` 与两种 `openspec validate` 结果；
8. 最终 Git 可见变更集合；
9. 明确提交范围建议；
10. 是否允许进入 Phase 3；
11. 未修改禁止路径、未将任务书入库、未执行禁止命令的确认。

---

## 13. 用户人工提交规则

Codex 不得提交。

只有当 `08-*` 报告给出 `ALLOW`，且最终变更集合符合第 11 节门禁时，用户才可人工提交。

在 `05/06/07` 均仍未提交的情况下，建议用户执行：

```bash
git add openspec/config.yaml docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md docs/rectification/07-superspec-config-gate-syntax-fix-report.md docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md
git commit -m "chore(openspec): enforce governed superspec context and execution gates"
```

提交后必须验证：

```bash
git status --short --branch --untracked-files=all
git rev-parse HEAD
```

工作树 clean 后，将新 HEAD 与 `08-*` 报告回传，方可开始 Phase 3。

---

## 14. 后续 Phase 3 范围预告

只有 Phase 2C 提交并恢复 clean 后，才进入：

```text
Phase 3：实现端与 SuperSpec 高风险执行链治理
```

Phase 3 将评估：

```text
- Claude Code 是否作为默认 apply / Superpowers 执行端；
- Codex 的整改文档实施与复核角色；
- OpenCode 备用兼容策略；
- `.claude/` / `.opencode/` 当前 opsx commands/skills 的治理方式；
- Superpowers 安装与可用性；
- worktree、TDD、review、merge、push、PR comment 的安全边界；
- 是否及如何解除 config 中 Phase 3 前的 apply/finalize 硬门禁。
```

Phase 3 完成之前，不得对真实业务 change 执行 SuperSpec `apply` 或 `finalize`。
