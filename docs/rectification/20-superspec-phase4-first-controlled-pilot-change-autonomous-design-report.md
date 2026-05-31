# DiagnoseToolPy SuperSpec Phase 4 首个受控 Pilot Change 自动选题与设计落地报告

> 执行阶段：Phase 4  
> 执行主体：Codex  
> 目标工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 目标分支：`chore/superspec-governance-migration`  
> 本阶段性质：自动选题、设计落地与本地提交  

## 1. 执行摘要

- Phase 4 执行结果：`PASS`
- Governance admission commit SHA：`f7b8e46fe762fdca72bced37672333b5eafd7729`
- Pilot change id：`2026-05-31-bugfix-prompt-export`
- Pilot change 设计状态：`READY FOR CHATGPT GATE B REVIEW`
- 是否已修改业务代码：`否`
- 是否允许执行真实 apply：`否`，等待下一阶段 Gate B
- 是否允许执行自动 finalize：`否`
- 本报告与设计资产 commit SHA：以 Codex 最终回传为准

## 2. 治理接入最终准入与 19 报告 Commit SHA

Phase 3C-B 已完成治理接入闭合，允许开始首个受控 pilot change 的 proposal / spec / design / tasks / plan。

治理准入承接来自：

- `docs/rectification/19-superspec-phase3c-final-autonomous-evidence-closure-and-governance-admission-report.md`
- 对应 commit SHA：`f7b8e46fe762fdca72bced37672333b5eafd7729`

该 commit 已进入当前 HEAD，且不需要再次提交。

## 3. 初始工作区与门禁有效性核验

### 3.1 工作区状态

在开始本阶段前，仓库处于 clean 状态，且仅是本地分支领先远端提交：

```text
git status --short --branch --untracked-files=all
## chore/superspec-governance-migration...origin/chore/superspec-governance-migration [ahead 2]
```

### 3.2 关键门禁

已确认：

- `openspec/config.yaml` 中 Phase 3 apply / finalize 阻断门禁仍存在
- `openspec/schemas/superspec/schema.yaml` 已包含 repository-safe human-gated override
- `docs/rectification/16-*`、`17-*`、`18-*`、`19-*` 均已进入当前 HEAD

### 3.3 允许状态

本阶段未修改任何治理文件、schema、业务代码或测试代码。

## 4. 当前仓库业务现状读取范围

为选择首个 pilot change，本阶段只读审查了：

- `README.md`
- `docs/00-project/project-brief.md`
- `docs/00-project/current-state.md`
- `docs/00-project/roadmap.md`
- `docs/01-architecture/architecture-overview.md`
- `docs/01-architecture/module-boundaries.md`
- `docs/01-architecture/retrieval-design.md`
- `docs/03-openspec/bugfix-rule.md`
- `docs/05-domain/prompt-template.md`
- `docs/05-domain/workspace-export-guide.md`
- `diagnose_tool/exporter/workspace_exporter.py`
- `diagnose_tool/analyzer/question_generator.py`
- `diagnose_tool/api/routes_diagnosis.py`
- `frontend/src/pages/DiagnosisStudioPage.tsx`
- `frontend/src/pages/AnalysisTasksPage.tsx`

结论：`bugfix prompt export` 是当前最小、最清晰、最贴近 roadmap 的首个受控 pilot change。

## 5. Pilot 候选列表、评分与自动选择理由

### 候选 1: Bugfix prompt export

- 用户价值：高
- 合同清晰度：高
- 改动面：小到中
- 数据/迁移风险：低
- 端到端验证性：高
- 与现有 spec 的关系：直接对应 roadmap 和 architecture 的 exporter 职责

### 候选 2: Test suggestion generation

- 用户价值：中高
- 合同清晰度：中
- 改动面：中到大
- 数据/迁移风险：低
- 端到端验证性：中
- 与现有 spec 的关系：符合 roadmap，但缺少当前代码雏形

### 候选 3: Monitoring suggestion generation

- 用户价值：中
- 合同清晰度：中
- 改动面：中到大
- 数据/迁移风险：低
- 端到端验证性：中
- 与现有 spec 的关系：符合 roadmap，但需要更多约束定义

### 自动选择结果

选择第一名：`bugfix prompt export`

原因：

1. 与 `docs/00-project/roadmap.md` 和 `docs/01-architecture/*` 的目标一致。
2. 可复用现有 diagnosis / exporter / prompt 模板基础。
3. 不需要先改治理、schema 或存储结构。
4. 适合作为 Claude Code 实现链路的首个受控 pilot。

## 6. 已选择 Pilot Change 标识与业务目标

- Pilot change id: `2026-05-31-bugfix-prompt-export`
- 一句话目标: 从现有分析任务输出生成一个可直接交给 Claude Code / OpenCode 的结构化 bugfix prompt markdown。

## 7. 生成的 proposal/spec/design/tasks/plan 资产清单

本阶段已生成以下设计资产：

```text
openspec/changes/2026-05-31-bugfix-prompt-export/.openspec.yaml
openspec/changes/2026-05-31-bugfix-prompt-export/proposal.md
openspec/changes/2026-05-31-bugfix-prompt-export/design.md
openspec/changes/2026-05-31-bugfix-prompt-export/tasks.md
openspec/changes/2026-05-31-bugfix-prompt-export/plan.md
openspec/changes/2026-05-31-bugfix-prompt-export/specs/bugfix-prompt-export/spec.md
```

设计要点：

- 生成 `data/output/{task_id}/bugfix-prompt.md`
- 不引入数据库
- 不读取全量日志到内存
- 不修改现有 diagnosis / casebase / retrieval 合同
- 不执行真实业务 apply
- 不允许自动 finalize

## 8. Gate B 前实现边界与后续实现端约束

后续实现主端：

- Claude Code：未来业务实现主端
- opencode：兼容/备用实现端

Codex 当前仅负责治理与设计收口，不作为默认业务实现端。

Gate B 前必须再次人工审核：

- 允许修改文件范围
- 禁止修改范围
- 测试与验收命令
- 是否需要 worktree
- 是否允许具体 implementation skill
- 回退方案

## 9. 静态验证结果

本阶段已根据当前仓库事实完成设计，不执行 apply / verify / finalize，也不修改业务代码。

后续实现时应验证：

- 新增 bugfix prompt exporter 的单元测试
- API 集成测试
- 前端按钮/预览测试
- `docs/00-project/current-state.md` 更新

## 10. 最终 Git 可见变更集合

本阶段形成的待提交文件集合仅限：

```text
openspec/changes/2026-05-31-bugfix-prompt-export/.openspec.yaml
openspec/changes/2026-05-31-bugfix-prompt-export/proposal.md
openspec/changes/2026-05-31-bugfix-prompt-export/design.md
openspec/changes/2026-05-31-bugfix-prompt-export/tasks.md
openspec/changes/2026-05-31-bugfix-prompt-export/plan.md
openspec/changes/2026-05-31-bugfix-prompt-export/specs/bugfix-prompt-export/spec.md
docs/rectification/20-superspec-phase4-first-controlled-pilot-change-autonomous-design-report.md
```

## 11. 本地 Design Commit 证据与 SHA 回传规则

本报告与设计资产所在 commit 的 SHA 由报告落盘后的 Git 提交生成；最终 SHA 以 Codex 回传的 `git rev-parse HEAD` 输出为准。

本阶段仅执行本地提交，不执行 push。

## 12. 保护范围确认

- [x] 未修改 `openspec/config.yaml`
- [x] 未修改 `openspec/schemas/superspec/schema.yaml`
- [x] 未修改 `openspec/specs/**`
- [x] 未修改 `openspec/changes/archive/**`
- [x] 未修改 `AGENT.md`
- [x] 未修改 `AGENTS.md`
- [x] 未修改 `.claude/**`
- [x] 未修改 `.opencode/**`
- [x] 未修改业务代码
- [x] 未修改测试代码
- [x] 未修改依赖或锁文件
- [x] 未执行 `git push`
- [x] 未执行 `git merge`
- [x] 未执行 `git reset`
- [x] 未执行 `git clean`
- [x] 未执行 `git stash`
- [x] 未执行真实业务 apply/finalize

## 13. 结论

- Phase 4 执行结果：`PASS`
- Governance admission commit SHA：`f7b8e46fe762fdca72bced37672333b5eafd7729`
- Pilot change id：`2026-05-31-bugfix-prompt-export`
- Pilot change 设计状态：`READY FOR CHATGPT GATE B REVIEW`
- 是否已修改业务代码：`否`
- 是否允许执行真实 apply：`否`，等待下一阶段 Gate B
- 是否允许执行自动 finalize：`否`
- 本报告与设计资产 commit SHA：以 Codex 最终回传为准

