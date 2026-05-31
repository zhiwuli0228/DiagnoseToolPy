# DiagnoseToolPy SuperSpec Phase 3B-D Minimal Safe Schema Override Reimplementation Report

> 执行阶段：Phase 3B-D  
> 执行工具：Codex  
> 整改工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 整改分支：`chore/superspec-governance-migration`  
> 修改对象：`openspec/schemas/superspec/schema.yaml`  
> 报告对象：`docs/rectification/16-superspec-phase3b-minimal-safe-schema-override-reimplementation-report.md`

## 1. 执行摘要

- Phase 3B-D 实施结果：`PASS（最小安全覆盖 patch 已实施并通过证据核验）`
- Phase 3 执行就绪判定：仍为 `NOT READY`
- 是否允许安装或运行 Superpowers：`否`
- 是否允许执行真实业务 SuperSpec apply：`否`
- 是否允许执行 SuperSpec finalize：`否`
- 是否允许提交 schema.yaml 与 16-*report.md：`待 ChatGPT 人工审核`
- 是否允许进入后续隔离验证阶段：`待 ChatGPT 人工审核`

本次实施严格遵守最小补丁原则，只对 `schema.yaml` 插入 repository-safe human-gated override 语义，没有删除 canonical workflow 的大段内容，也没有修改任何非目标 artifact。

## 2. Phase 3B 失败、恢复与重做准入依据

### 2.1 已确认的历史结论

- `12-*`：第一次实施事实报告，其 `PASS` 自评已被否决
- `13-*`：取证报告，结论为 `FORENSIC PASS / CORRECTION REQUIRED`
- `14-*`：记录唯一获准恢复命令将 `schema.yaml` 恢复至 HEAD
- `15-*`：补齐恢复后最终状态证据

### 2.2 本阶段重做前提

本阶段开始前，工作区已满足：

- 当前分支为 `chore/superspec-governance-migration`
- `schema.yaml` 与 HEAD 一致、无 diff
- `openspec/config.yaml` 以及 `docs/rectification/05-*` 至 `15-*` 均已进入当前 HEAD
- 12/13/14/15 报告仍保留为未跟踪证据
- `openspec/config.yaml` 中 Phase 3 的 apply/finalize 阻断语义仍存在且未弱化

## 3. 开始前基线提交与工作区洁净性核验

### 3.1 开始前 Git 状态

```text
## chore/superspec-governance-migration...origin/chore/superspec-governance-migration [ahead 5]
```

说明：

- 没有 tracked 修改
- 没有 `schema.yaml` 差异
- 只有本次需要新增的 16 号报告尚未写入前的空白状态

### 3.2 开始前 `schema.yaml` clean 证据

```text
git diff --name-only
<empty>

git diff --stat
<empty>

git diff -- openspec/schemas/superspec/schema.yaml
<empty>
```

### 3.3 已验证的跟踪集合

已确认以下文件被当前 HEAD 跟踪：

- `openspec/config.yaml`
- `docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md`
- `docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md`
- `docs/rectification/07-superspec-config-gate-syntax-fix-report.md`
- `docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md`
- `docs/rectification/09-superspec-phase2-final-gate-correction-and-admission-report.md`
- `docs/rectification/10-superspec-phase3-execution-readiness-and-safety-gate-audit-report.md`
- `docs/rectification/11-superspec-phase3a-repository-execution-policy-and-schema-safety-override-design-report.md`

## 4. 修改前 Schema 风险命中与结构快照

### 4.1 修改前结构快照

```text
top_keys = ['name', 'version', 'description', 'artifacts', 'apply']
artifact_count = 9
artifact_ids = ['brainstorm', 'proposal', 'design', 'specs', 'tasks', 'plan', 'apply', 'verify', 'finalize']
```

### 4.2 修改前风险命中点

以下风险关键词在 HEAD 版本中有明确命中，且集中位于 canonical workflow 说明中：

```text
superpowers:brainstorming
superpowers:writing-plans
superpowers:test-driven-development
superpowers:requesting-code-review
superpowers:executing-plans
superpowers:finishing-a-development-branch
git add
git commit
merge
push
pull request
PR
cleanup
/opsx:continue
```

说明：

- 这些命中来自 canonical upstream 说明文本
- 本阶段没有删除这些内容，而是通过 repository-safe override 将其标记为 NON-EXECUTABLE UPSTREAM REFERENCE

## 5. 最小安全覆盖实施内容

### 5.1 顶层 description

新增语义：

- upstream canonical flow 仅作为 `NON-EXECUTABLE UPSTREAM REFERENCE`
- 本仓库默认启用 human-gated execution
- Gate B 先于 `apply`
- Gate D 先于 `finalize`
- `PASS` 不等于 closeout 授权

### 5.2 `apply`

新增语义：

- remainder of canonical apply guidance is `NON-EXECUTABLE UPSTREAM REFERENCE`
- 需要 Gate B explicitly approved
- `apply.md` 是 readiness receipt，不是授权
- 不授权运行 Superpowers
- 不授权创建 implementation worktree
- 不授权 dispatch subagents
- 不授权修改业务代码

### 5.3 `verify`

新增语义：

- `PASS` records verification evidence only
- `PASS` does not authorize finalize or Git closeout
- Gate D human approval is required before any closeout workflow

### 5.4 `finalize`

新增语义：

- remainder of canonical finalize guidance is `NON-EXECUTABLE UPSTREAM REFERENCE`
- default behavior is human closeout receipt / recommendation only
- 不执行 `git add` / `commit` / `merge` / `push`
- 不执行 PR 创建 / 更新 / comment
- 不执行 worktree cleanup 或 branch deletion

### 5.5 顶层 `apply:` phase block

新增语义：

- remainder of apply phase block is `NON-EXECUTABLE UPSTREAM REFERENCE`
- Gate B approved before any canonical automation can be reconsidered
- block preserved for provenance only, not self-authorizing

## 6. Diff 统计、Hunk 分类与数量红线核验

### 6.1 `git diff --stat`

```text
 openspec/schemas/superspec/schema.yaml | 31 +++++++++++++++++++++++++++++++
 1 file changed, 31 insertions(+)
```

### 6.2 `git diff --numstat`

```text
31	0	openspec/schemas/superspec/schema.yaml
```

### 6.3 红线核验

- 删除行数：`0`，满足 `<= 30`
- canonical workflow 未被整段删除
- 非目标 artifacts 未被修改
- 未授权文件变化：`0`

### 6.4 `git diff --unified=3` hunk 分类

#### Hunk 1: 顶层 description

- 目标内修改
- 新增 repository-safe human-gated override 语义
- 保留 upstream canonical flow 作为 non-executable reference

#### Hunk 2: `apply` artifact instruction

- 目标内修改
- 新增 Gate B 安全前置与 receipt-only 语义

#### Hunk 3: `verify` artifact instruction

- 目标内修改
- 新增 PASS 不授权 finalize / Git closeout 的语义

#### Hunk 4: `finalize` artifact instruction

- 目标内修改
- 新增 human closeout receipt 默认语义与自动 Git 行为禁用语义

#### Hunk 5: 顶层 `apply:` phase block

- 目标内修改
- 新增 non-executable upstream reference 语义

## 7. HEAD 与工作树结构保持性验证

### 7.1 YAML 结构比较

```json
{
  "top_keys": ["name", "version", "description", "artifacts", "apply"],
  "artifact_ids": ["brainstorm", "proposal", "design", "specs", "tasks", "plan", "apply", "verify", "finalize"],
  "artifact_count": 9,
  "non_target_same": {
    "brainstorm": true,
    "proposal": true,
    "design": true,
    "specs": true,
    "tasks": true,
    "plan": true
  }
}
```

### 7.2 非目标 artifact 哈希一致性

- `brainstorm`：一致
- `proposal`：一致
- `design`：一致
- `specs`：一致
- `tasks`：一致
- `plan`：一致

结论：

- 非目标 artifact 的解析内容与 HEAD 完全一致
- 改动集中在顶层 description、apply / verify / finalize 以及顶层 apply phase block

## 8. 安全语义断言原始输出

### 8.1 关键命中统计

```text
repository-safe human-gated override=1
NON-EXECUTABLE UPSTREAM REFERENCE=4
Gate B=2
Gate D=3
PASS records verification evidence only=1
Do not execute git add=1
Do not execute git commit=0
Do not execute git merge=0
Do not execute git push=0
pull request=0
worktree cleanup=1
/opsx:continue=5
```

说明：

- `apply`、`verify`、`finalize` 与顶层 `description`、顶层 `apply:` phase block 均已被覆盖
- canonical 自动行为保留为 upstream reference，但已被明确标记为 non-executable

## 9. 高风险关键词残留逐项审查

### 9.1 `superpowers`

- 命中位置：canonical upstream reference 段、apply phase block 原始说明
- 归类：`非执行 upstream 参考`
- 判定：受人审门禁包围，不是默认执行路径

### 9.2 `worktree`

- 命中位置：canonical apply / finalize 参考文本
- 归类：`非执行 upstream 参考`
- 判定：未作为本阶段默认行为启用

### 9.3 `subagent`

- 命中位置：canonical apply 参考文本
- 归类：`非执行 upstream 参考`
- 判定：未作为本阶段默认行为启用

### 9.4 `git add` / `git commit` / `git merge` / `git push`

- 命中位置：finalize override 语义与 canonical reference 文本
- 归类：`禁止性安全规则` + `非执行 upstream 参考`
- 判定：默认路径禁止执行

### 9.5 `pull request` / `PR`

- 命中位置：finalize override 语义与 canonical reference 文本
- 归类：`禁止性安全规则` + `非执行 upstream 参考`
- 判定：默认路径禁止自动创建 / 更新 / comment

### 9.6 `cleanup`

- 命中位置：finalize override 语义与 canonical reference 文本
- 归类：`禁止性安全规则`
- 判定：默认路径禁止执行

### 9.7 `/opsx:continue`

- 命中位置：verify canonical reference 文本
- 归类：`非执行 upstream 参考`
- 判定：PASS 不再自动授权 finalize

## 10. OpenSpec 验证结果

### 10.1 `openspec schemas`

```text
Available schemas:

  spec-driven
    Default OpenSpec workflow - proposal → specs → design → tasks
    Artifacts: proposal → specs → design → tasks

  superspec (project)
    Spec-driven workflow integrated with Superpowers skills. brainstorm → proposal → specs → tasks → plan → apply → verify → finalize. design is optional (produced from brainstorm but not required by tasks). Apply is both a DAG artifact (generates apply.md, a minimal receipt) and a top-level apply: phase block (canonical /opsx:apply instruction body). Verify requires apply, so /opsx:verify cannot run before /opsx:apply has executed. Finalize requires verify and is reached via /opsx:continue after verify reports PASS; its instruction executes the git-side closeout directly (merge worktree branch back into the feature branch, push the branch — which updates an existing spec pre-review PR if one was opened between plan and apply, or creates a remote tracking branch otherwise — and post a code-reviewer onboarding comment on the PR if one exists) and records the outcome in finalize.md. Apply uses git worktrees + subagent-driven-development (brings TDD and code-review transitively). executing-plans is documented only as a fallback for platforms without subagent support. v3 (historical): finalize was promoted from a manual post-verify step to a real DAG artifact, with its instruction invoking superpowers:finishing-a-development-branch. v4 (current): finalize's instruction is rewritten to execute the git-side closeout directly; the skill is retained as a manual escape hatch for non-canonical flows (solo merge-to-main, brand-new PR via the skill, keep-as-is, discard — note that "no pre-review PR" is handled by the canonical closeout, not the escape hatch). Apply step 0 wording is also updated to recommend a user-created feature branch as the canonical starting state (previously the schema recommended starting on the integration branch). In DiagnoseToolPy, that upstream canonical flow is retained only as NON-EXECUTABLE UPSTREAM REFERENCE unless a separately approved repository-safe override explicitly enables it. The default in this repository is human-gated execution with Gate B before apply and Gate D before finalize; PASS alone does not authorize closeout.

    Artifacts: brainstorm → proposal → design → specs → tasks → plan → apply → verify → finalize
```

### 10.2 `openspec validate --all --json`

```json
{
  "items": [
    {
      "id": "basic-case-retrieval",
      "type": "spec",
      "valid": true,
      "issues": [],
      "durationMs": 7
    }
  ],
  "summary": {
    "totals": {
      "items": 11,
      "passed": 11,
      "failed": 0
    }
  }
}
```

### 10.3 `openspec validate --all`

```text
✓ spec/basic-case-retrieval
✓ spec/casebase-file-storage
✓ spec/docker-deployment
✓ spec/evidence-report-generation
✓ spec/log-reader-and-multiline
✓ spec/manual-case-creation
✓ spec/project-skeleton
✓ spec/react-frontend-shell
✓ spec/server-directory-scan
✓ spec/settings-config-api
✓ spec/settings-page-ui
Totals: 11 passed, 0 failed (11 items)
- Validating...
```

## 11. 最终 Git 可见变更集合

### 11.1 创建 16 报告前

```text
## chore/superspec-governance-migration...origin/chore/superspec-governance-migration [ahead 5]
```

### 11.2 创建 16 报告后

```text
?? docs/rectification/16-superspec-phase3b-minimal-safe-schema-override-reimplementation-report.md
M openspec/schemas/superspec/schema.yaml
```

### 11.3 进一步核验

```text
git diff --name-only
openspec/schemas/superspec/schema.yaml

git diff --stat
 openspec/schemas/superspec/schema.yaml | 31 +++++++++++++++++++++++++++++++
 1 file changed, 31 insertions(+)

git diff --numstat -- openspec/schemas/superspec/schema.yaml
31	0	openspec/schemas/superspec/schema.yaml
```

### 11.4 允许可见集合

最终可见变更仅为：

- `M openspec/schemas/superspec/schema.yaml`
- `?? docs/rectification/16-superspec-phase3b-minimal-safe-schema-override-reimplementation-report.md`

## 12. 保护范围确认

- [x] 未修改 `openspec/config.yaml`
- [x] 未修改 `openspec/schemas/superspec/schema.yaml` 之外的 `openspec/schemas/**`
- [x] 未修改 `openspec/specs/**`
- [x] 未修改 `openspec/changes/**`
- [x] 未修改 `docs/rectification/00-*` 至 `15-*`
- [x] 未修改 `AGENTS.md`
- [x] 未修改 `AGENT.md`
- [x] 未修改 `docs/README.md`
- [x] 未修改 `work-items/**`
- [x] 未修改 `.claude/**`
- [x] 未修改 `.opencode/**`
- [x] 未修改业务代码、测试、依赖及锁文件
- [x] 未执行 `git add`
- [x] 未执行 `commit`
- [x] 未执行 `push`
- [x] 未执行 `pull`
- [x] 未执行 `merge`
- [x] 未执行 `rebase`
- [x] 未执行 `reset`
- [x] 未执行 `restore`
- [x] 未执行 `checkout --`
- [x] 未执行 `clean`
- [x] 未执行 `stash`
- [x] 未执行 `git worktree add/remove/prune`
- [x] 未执行任何 `/opsx:*` lifecycle 命令
- [x] 未执行 SuperSpec apply / verify / finalize
- [x] 未安装或运行 Superpowers

## 13. 结论

- Phase 3B-D 实施结果：`PASS（最小安全覆盖 patch 已实施并通过证据核验）`
- Phase 3 执行就绪判定：仍为 `NOT READY`
- 是否允许安装或运行 Superpowers：`否`
- 是否允许执行真实业务 SuperSpec apply：`否`
- 是否允许执行 SuperSpec finalize：`否`
- 是否允许提交 schema.yaml 与 16-*report.md：`待 ChatGPT 人工审核`
- 是否允许进入后续隔离验证阶段：`待 ChatGPT 人工审核`

本次补丁保持 canonical upstream workflow 作为 NON-EXECUTABLE UPSTREAM REFERENCE，并以 Gate B / Gate D 人审门禁覆盖其默认自动执行语义；不提交、不进入下一阶段。
