# DiagnoseToolPy SuperSpec Phase 3B Project Safe Schema Override Implementation Report

> 执行阶段：Phase 3B  
> 执行工具：Codex  
> 整改工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 整改分支：`chore/superspec-governance-migration`  
> 修改范围：仅 `openspec/schemas/superspec/schema.yaml` 与本报告

## 1. 执行摘要

- Phase 3B 实施结果：`PASS`
- Phase 3 执行就绪判定：`NOT READY`
- 是否允许安装或运行 Superpowers：`否`
- 是否允许执行真实业务 SuperSpec apply：`否`
- 是否允许执行 SuperSpec finalize：`否`
- 是否允许进入后续隔离能力验证阶段：`待 ChatGPT 人工审核`

本阶段仅对本项目本地 `superspec` schema 做了 repository-safe human-gated override 适配，不安装或运行 Superpowers，不执行 `apply` / `finalize`，不修改任何配置、规格、业务代码、测试、文档或工具目录之外的文件。

## 2. 前置核验

### 2.1 分支与状态

- 当前分支：`chore/superspec-governance-migration`
- 当前工作区状态：`仅有 openspec/schemas/superspec/schema.yaml 修改，另新增本报告`

### 2.2 受控资产核验

已确认以下项目级治理资产仍被当前 HEAD 跟踪并保留：

- `openspec/config.yaml`
- `docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md`
- `docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md`
- `docs/rectification/07-superspec-config-gate-syntax-fix-report.md`
- `docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md`
- `docs/rectification/09-superspec-phase2-final-gate-correction-and-admission-closure-report.md`
- `docs/rectification/10-superspec-phase3-execution-readiness-and-safety-gate-audit-report.md`
- `docs/rectification/11-superspec-phase3a-repository-execution-policy-and-schema-safety-override-design-report.md`

`openspec/config.yaml` 中两条 Phase 3 阻断门禁仍然存在，且未被弱化：

- `rules.apply` 相关阻断语义仍要求 Phase 3 前不得执行真实业务实现
- `rules.finalize` 相关阻断语义仍要求 Phase 3 前不得执行 Git/PR closeout

## 3. 实施内容

### 3.1 顶层 schema 语义

已将 `openspec/schemas/superspec/schema.yaml` 的顶层描述改为 repository-safe human-gated override 语义，明确：

- 本项目启用人审安全模式
- `apply` 是人审门禁，不是自动化授权
- `verify` PASS 不自动授权 `finalize`
- `finalize` 默认是人工 closeout receipt，而不是自动 merge / push / PR closeout
- 未来若要恢复自动 closeout，必须通过独立且重新批准的 schema 变更

### 3.2 `apply` 语义

已收口 `apply` 语义，使其明确：

- 仅在 Gate B 经人工批准后才允许继续
- 未批准前不得运行 Superpowers
- 未批准前不得创建实现 worktree
- 未批准前不得启动 subagent-driven-development
- 未批准前不得变更业务代码
- `apply.md` 只是门禁收据，不是实施授权

### 3.3 `verify` 语义

已收口 `verify` 语义，使其明确：

- `verify` 仅确认事实证据、一致性与范围
- `PASS` 不自动授权 `finalize`
- `PASS` 后必须等待独立 Gate D 人工批准 closeout

### 3.4 `finalize` 语义

已收口 `finalize` 语义，使其默认成为人工 closeout receipt / 建议步骤记录阶段：

- 不自动执行 `git add`
- 不自动执行 `commit`
- 不自动执行 `merge`
- 不自动执行 `push`
- 不自动执行 PR 创建 / 更新
- 不自动执行 PR comment
- 不自动执行 worktree cleanup
- 不自动执行 branch 删除
- 仅记录经人工批准后由用户实际执行或明确授权执行的 closeout 结果
- 任何未来自动 closeout 模式都必须由独立阶段另行批准

## 4. YAML parser 硬断言结果

已对 `openspec/schemas/superspec/schema.yaml` 做 YAML 解析与结构核验，结论如下：

- 文件可被成功解析为 YAML
- 顶层 `apply` 键存在，且其内容为 repository-safe human-gated override
- `finalize` 的安全语义已位于 `artifacts` 中的 `finalize` artifact 定义内
- `apply` / `verify` / `finalize` 的安全覆盖语义均已存在
- 顶层自动 Git closeout 的 canonical 执行路径已不再是直接可执行路径

## 5. OpenSpec 验证结果

### 5.1 `openspec schemas`

`superspec (project)` 仍可被正确识别。

### 5.2 `openspec validate --all --json`

- `11 passed, 0 failed`

### 5.3 `openspec validate --all`

- `11 passed, 0 failed`

## 6. 配置与变更边界

### 6.1 精确变更

仅修改：

- `openspec/schemas/superspec/schema.yaml`

仅新增：

- `docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md`

### 6.2 未修改范围

未修改以下任何内容：

- `openspec/config.yaml`
- `openspec/specs/**`
- `openspec/changes/**`
- `AGENTS.md`
- `AGENT.md`
- `docs/README.md`
- `work-items/**`
- `.claude/**`
- `.opencode/**`
- 业务代码
- 测试代码
- 依赖文件
- 任何既有 `docs/rectification/00-*` 至 `11-*` 报告

## 7. 最终 Git 可见变更集合

### `git status --short --branch --untracked-files=all`

```text
## chore/superspec-governance-migration...origin/chore/superspec-governance-migration
 M openspec/schemas/superspec/schema.yaml
?? docs/rectification/12-superspec-phase3b-project-safe-schema-override-implementation-report.md
```

### `git diff --stat`

```text
 openspec/schemas/superspec/schema.yaml | 605 ++++-----------------------------
 1 file changed, 69 insertions(+), 536 deletions(-)
```

### `git diff --name-only`

```text
openspec/schemas/superspec/schema.yaml
```

## 8. 结论

- Phase 3B 实施结果：`PASS`
- Phase 3 执行就绪判定：`NOT READY`
- 是否允许安装或运行 Superpowers：`否`
- 是否允许执行真实业务 SuperSpec apply：`否`
- 是否允许执行 SuperSpec finalize：`否`
- 是否允许进入后续隔离能力验证阶段：`待 ChatGPT 人工审核`

本次仅完成项目级安全覆盖 schema 的实施，不提交、不推送、不进入下一阶段。
