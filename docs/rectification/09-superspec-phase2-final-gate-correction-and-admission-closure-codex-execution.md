# DiagnoseToolPy SuperSpec Phase 2D：Phase 2 门禁最终语义修正与准入证据闭合 — Codex 执行任务书

> 任务类型：治理纠偏执行任务书  
> 执行工具：Codex  
> 生成日期：2026-05-31  
> 目标工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 目标分支：`chore/superspec-governance-migration`  
> 本任务书位置要求：**保存在仓库外，不得复制或提交到项目仓库。**

---

## 1. 执行背景与审核结论

Phase 2C 执行报告 `docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md` 已由人工审核判定为 **未通过准入**。

原因不是 YAML 类型或 OpenSpec 校验失败，而是其实际配置文本未满足 Phase 2C 已批准的门禁语义：

1. `rules.apply` 当前末项仅要求 active change 获得实现授权，未明确规定 **Phase 3 批准前不得通过 SuperSpec apply 执行真实业务实现**，也未绑定 implementation tool、Superpowers availability、worktree behavior、review discipline 与 Git-safety prerequisites。
2. `rules.finalize` 当前末项仅要求 verify green 与 repository-specific safety review 批准 closeout，未明确规定 **Phase 3 批准前不得通过 SuperSpec finalize 执行 Git/PR closeout**，也未绑定 merge、push、worktree cleanup 与 pull-request safety prerequisites。
3. Phase 2C 报告中的 `PASS` 与“允许进入 Phase 3：是”结论已被本次人工审核否决；该报告保留为历史证据，不得修改或删除。
4. Phase 2C 报告结论只提及提交 `openspec/config.yaml` 与“本次新增报告”，未完整闭合此前尚未跟踪的 `05-*`、`06-*`、`07-*` 历史证据链。本次必须明确最终待人工提交的授权文件集合。

**本任务目标：**仅修正两条门禁文本，新增一份 Phase 2D 纠偏报告，重新完成 Phase 2 系列的最终准入判定。  
**在本任务通过并经人工审核前：不得进入 Phase 3，不得提交现有 Phase 2 未提交变更。**

---

## 2. 强制执行边界

### 2.1 允许修改路径

本次仅允许发生以下文件变化：

```text
M  openspec/config.yaml
?? docs/rectification/09-superspec-phase2-final-gate-correction-and-admission-closure-report.md
```

说明：

- `openspec/config.yaml` 当前已处于 Phase 2 系列未提交修改状态；本次仅允许替换 `rules.apply` 与 `rules.finalize` 的最后一条字符串。
- 新报告序号使用 `09-*`，因为 `08-*` 报告已经存在并作为失败证据保留。

### 2.2 禁止修改路径

不得修改、覆盖、重命名、删除或格式化以下范围：

```text
docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
docs/rectification/07-superspec-config-gate-syntax-fix-report.md
docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md

openspec/schemas/**
openspec/specs/**
openspec/changes/**

src/**
backend/**
frontend/**
tests/**
test/**
*.py
*.ts
*.tsx
*.js

AGENT.md
AGENTS.md
work-items/**
docs/ai-harness/**
.claude/**
.opencode/**
.gitignore
```

若实际仓库中不存在上述某些业务目录，不需要创建；其含义是禁止触碰任何业务代码、测试、工具或治理权威入口资产。

### 2.3 禁止执行的操作

本阶段不得执行：

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
任何 /opsx:* lifecycle 命令
任何 SuperSpec apply / finalize 实际执行
任何 Superpowers 安装或运行
```

允许执行只读 Git 检查命令，例如：

```bash
git status --short --branch --untracked-files=all
git diff -- openspec/config.yaml
git diff --name-only
git diff --stat
git rev-parse HEAD
git branch --show-current
```

---

## 3. 开始前检查：必须记录现状

进入目标工作区后，先执行并在 `09-*report.md` 中记录输出：

```bash
git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git diff -- openspec/config.yaml
```

必须确认：

1. 当前分支为：

```text
chore/superspec-governance-migration
```

2. 当前 HEAD 与报告显示的 Phase 2 基线关系是否一致；若 HEAD 与此前报告记录的 `d34c81ba6355309ebe577006c3b981fde8d08736` 不一致，**停止修改并在报告中记录阻断原因**。
3. 下列历史报告均存在，且在本次修改前不得被编辑：

```text
docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
docs/rectification/07-superspec-config-gate-syntax-fix-report.md
docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md
```

4. 记录 `05-*` 至 `08-*` 的 Git 跟踪状态。预期在用户尚未手工提交的前提下，其状态为未跟踪文件。

---

## 4. 唯一配置修改要求

仅编辑：

```text
openspec/config.yaml
```

### 4.1 `rules.apply` 最后一条必须精确替换为

```yaml
- "Do not execute real business implementation through SuperSpec apply until Phase 3 approves the implementation tool, Superpowers availability, worktree behavior, review discipline, and Git-safety prerequisites for this repository."
```

### 4.2 `rules.finalize` 最后一条必须精确替换为

```yaml
- "Do not execute Git/PR closeout through SuperSpec finalize until Phase 3 approves repository-specific merge, push, worktree cleanup, and pull-request safety prerequisites."
```

### 4.3 精确性约束

- 文本必须与上方内容逐字符一致，包括 `SuperSpec apply`、`SuperSpec finalize`、`Phase 3`、`Superpowers`、`Git-safety`、`worktree cleanup`、`pull-request` 等关键词。
- 两项必须是 YAML 字符串列表项，不能写成 mapping，也不能移动到顶层或其他 `rules.*` 节点。
- 不允许同步润色、重排或格式化其他配置内容。
- 不允许将门禁改写为“只要 active change 授权即可执行”或“只要 verify green 即可 closeout”的弱化语义。

---

## 5. YAML Parser 硬断言

修改后必须使用 Python YAML parser 执行硬断言。可使用下列等价脚本；不得只依赖肉眼检查或 `openspec validate`：

```python
from pathlib import Path
import yaml

config_path = Path("openspec/config.yaml")
data = yaml.safe_load(config_path.read_text(encoding="utf-8"))

expected_apply = (
    "Do not execute real business implementation through SuperSpec apply until Phase 3 "
    "approves the implementation tool, Superpowers availability, worktree behavior, "
    "review discipline, and Git-safety prerequisites for this repository."
)
expected_finalize = (
    "Do not execute Git/PR closeout through SuperSpec finalize until Phase 3 approves "
    "repository-specific merge, push, worktree cleanup, and pull-request safety prerequisites."
)

assert "apply" not in data
assert "finalize" not in data
assert isinstance(data.get("rules"), dict)

apply_rules = data["rules"].get("apply")
finalize_rules = data["rules"].get("finalize")

assert isinstance(apply_rules, list)
assert isinstance(finalize_rules, list)
assert all(isinstance(item, str) for item in apply_rules)
assert all(isinstance(item, str) for item in finalize_rules)
assert apply_rules[-1] == expected_apply
assert finalize_rules[-1] == expected_finalize

print({
    "top_keys": list(data.keys()),
    "rules_keys": list(data["rules"].keys()),
    "apply_last": apply_rules[-1],
    "finalize_last": finalize_rules[-1],
    "assertions": "passed",
})
```

将实际输出原样记录在 `09-*report.md` 中。

---

## 6. OpenSpec 验证要求

完成配置修正与 parser 断言后，执行：

```bash
openspec schemas
openspec validate --all --json
openspec validate --all
```

最低通过标准：

```text
superspec (project)
11 passed, 0 failed
```

若任一验证失败：

- 不得尝试扩大修改范围修复其他文件；
- 在 `09-*report.md` 中记录失败命令、完整关键输出和阻断结论；
- 阶段结论必须为 `FAIL`，不得建议进入 Phase 3。

---

## 7. 必须新增的执行报告

新增且仅新增：

```text
docs/rectification/09-superspec-phase2-final-gate-correction-and-admission-closure-report.md
```

### 7.1 报告必须包含的章节

```markdown
# DiagnoseToolPy SuperSpec Phase 2D Phase 2 门禁最终语义修正与准入证据闭合报告

## 1. 执行摘要
## 2. Phase 2C 人工审核否决记录
## 3. 开始前工作区与证据链状态
## 4. 配置精确 diff
## 5. YAML Parser 硬断言输出
## 6. OpenSpec 验证结果
## 7. 最终 Git 可见变更集合
## 8. 最终授权待人工提交文件集合
## 9. 保护范围确认
## 10. 结论
```

### 7.2 报告关键内容要求

#### `## 2. Phase 2C 人工审核否决记录`

必须明确写明：

- `08-*report.md` 的执行事实保留为证据；
- 其 `PASS` 和“允许进入 Phase 3”结论被人工审核否决；
- 否决理由为两条门禁文本未绑定 Phase 3 前置批准，语义未满足既定目标；
- 本报告不篡改历史报告，而是作为后续纠偏与最终准入依据。

#### `## 4. 配置精确 diff`

必须附上仅针对 `openspec/config.yaml` 的真实 diff，并确认只有两条末项门禁发生预期替换。

#### `## 7. 最终 Git 可见变更集合`

必须粘贴：

```bash
git status --short --branch --untracked-files=all
git diff --stat
git diff --name-only
```

#### `## 8. 最终授权待人工提交文件集合`

若 parser 与 OpenSpec 验证全部通过，报告必须声明人工提交范围**仅限**以下文件：

```text
openspec/config.yaml
docs/rectification/05-superspec-project-context-and-artifact-rules-injection-report.md
docs/rectification/06-superspec-config-source-consistency-and-rule-tightening-report.md
docs/rectification/07-superspec-config-gate-syntax-fix-report.md
docs/rectification/08-superspec-execution-gate-semantic-correction-and-evidence-closure-report.md
docs/rectification/09-superspec-phase2-final-gate-correction-and-admission-closure-report.md
```

并明确：

- `06-*`、`07-*`、`08-*` 中任何早先的“允许进入 Phase 3”结论均已被后续人工审核覆盖，仅作为可追溯历史证据保留；
- 只有 `09-*` 经 ChatGPT 人工审核通过后，才可以作为 Phase 2 系列最终准入依据；
- Codex 本次不得代替用户执行 `git add`、`commit` 或 `push`。

#### `## 10. 结论`

仅当全部检查通过时，可以写：

```text
- Phase 2D 执行结果：PASS
- 是否允许提交 Phase 2 系列授权证据集合：待 ChatGPT 人工审核
- 是否允许进入 Phase 3：待 ChatGPT 人工审核
```

不得直接声明已允许提交或已允许进入 Phase 3。

---

## 8. 完成后回传要求

完成执行后，请仅向用户回传：

```text
docs/rectification/09-superspec-phase2-final-gate-correction-and-admission-closure-report.md
```

无需回传本任务书，无需额外复制仓库文件。

---

## 9. 准入判定标准

ChatGPT 后续仅在以下条件全部满足时批准人工提交并允许进入 Phase 3：

| 检查项 | 通过标准 |
|---|---|
| 配置变更范围 | 仅两条门禁字符串发生预期修正 |
| `rules.apply` 门禁 | 精确绑定 `SuperSpec apply` 与 `Phase 3` 批准条件 |
| `rules.finalize` 门禁 | 精确绑定 `SuperSpec finalize` 与 `Phase 3` 批准条件 |
| YAML 结构 | parser 硬断言全部通过，两项均为列表字符串 |
| OpenSpec 验证 | `11 passed, 0 failed` |
| 证据链 | `05-*` 至 `09-*` 均保留，`09-*` 明确覆盖早期错误准入结论 |
| 修改隔离 | 未触碰 schema、living specs、业务代码、工具目录或权威治理入口 |
| Git 操作 | Codex 未执行 add / commit / push / merge 等写操作 |

任一条件不满足，Phase 2 继续保持未通过状态，仍不得进入 Phase 3。
