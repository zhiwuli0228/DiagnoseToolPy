# DiagnoseToolPy SuperSpec Phase 3C Superpowers Integration Dual Harness Validation and Execution Admission Report

> 执行阶段：Phase 3C  
> 执行工具：Codex  
> 整改工作区：`E:/009workspace/claudecode/DiagnoseToolPy-superspec-governance`  
> 整改分支：`chore/superspec-governance-migration`  
> 目的：Superpowers 接入、Claude Code / OpenCode 双实现端兼容验证、最终执行放行判定

## 1. 执行摘要

- Phase 3C 执行状态：`WAITING FOR USER EVIDENCE`
- Claude Code 作为实现主端是否验证通过：`WAITING FOR USER EVIDENCE`
- opencode 作为兼容端是否验证通过：`WAITING FOR USER EVIDENCE`
- Superpowers skills 可用性是否验证通过：`WAITING FOR USER EVIDENCE`
- repository-safe schema 与工具端是否兼容：`WAITING FOR USER EVIDENCE`
- 是否允许开始第一个“试运行级业务 change”：`否`
- 即使允许试运行，是否仍必须禁止自动 finalize Git closeout：`是`

本阶段不对 DiagnoseToolPy 真实业务 change 执行 SuperSpec apply/finalize，不修改 `.claude/**`、`.opencode/**` 或任何项目文件；仅给出官方安装与识别步骤，并列出用户需要回传的证据命令。

## 2. 基线检查

### 2.1 分支与工作区

```text
branch: chore/superspec-governance-migration
status: clean
```

### 2.2 关键治理资产

已确认：

- `openspec/config.yaml` 中 Phase 3 的 apply/finalize 阻断门禁仍存在
- `openspec/schemas/superspec/schema.yaml` 已包含 repository-safe human-gated override
- `docs/rectification/16-superspec-phase3b-minimal-safe-schema-override-reimplementation-report.md` 已进入当前 HEAD

### 2.3 当前 HEAD 可追踪文件

当前 HEAD 已跟踪：

- `openspec/config.yaml`
- `openspec/schemas/superspec/schema.yaml`
- `docs/rectification/16-superspec-phase3b-minimal-safe-schema-override-reimplementation-report.md`

## 3. 官方安装与识别步骤

### 3.1 Claude Code 主端

依据 Superpowers 官方文档，Claude Code 使用官方插件市场安装。推荐步骤如下：

1. 打开 Claude Code 的插件界面。
2. 安装 Superpowers 插件：

```text
/plugin install superpowers@claude-plugins-official
```

3. 重启 Claude Code。
4. 验证技能是否可见：
   - 在新会话中调用 `Skill` 工具
   - 或让模型列出已发现的 Superpowers skills
   - 或询问 `"Tell me about your superpowers"` 进行最小可见性验证
5. 若官方市场不可用，可改用 Superpowers marketplace：

```text
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

### 3.2 opencode 兼容端

依据 Superpowers 官方 OpenCode 安装文档，OpenCode 需要单独安装，不与 Claude Code 共用同一次安装。推荐步骤如下：

1. 在全局或项目级 `opencode.json` 中加入插件：

```json
{
  "plugin": ["superpowers@git+https://github.com/obra/superpowers.git"]
}
```

2. 重启 OpenCode。
3. 验证技能是否可见：
   - 使用 OpenCode 原生 `skill` 工具列出技能
   - 载入 `superpowers/brainstorming` 或任一已知 skill
   - 询问 `"Tell me about your superpowers"` 进行最小可见性验证
4. Windows 环境如 git-backed 安装失败，官方文档允许使用 npm 前缀安装到用户级目录，再在 `opencode.json` 指向本地包路径：

```text
npm install superpowers@git+https://github.com/obra/superpowers.git --prefix "%USERPROFILE%\.config\opencode"
```

然后在 `opencode.json` 中引用本地包路径。

### 3.3 重要约束

- Claude Code 与 opencode 必须分别安装、分别验证
- 不修改 DiagnoseToolPy 项目内的 `.claude/**` 或 `.opencode/**`
- 若必须改用户级全局配置，先记录实际文件位置、修改内容和回退方式，再由用户或经明确批准后执行

## 4. 隔离 smoke test 方案

### 4.1 目的

不使用 DiagnoseToolPy 的真实 change，不执行本项目 SuperSpec apply/finalize，只验证：

- Claude Code 是否能发现并调用所需 Superpowers skills
- opencode 是否能发现并调用所需 Superpowers skills
- worktree / subagent / review / closeout 能力中哪些仅可“可见”，哪些不得运行

### 4.2 推荐测试方式

创建一个临时、无业务代码影响的最小样例目录，例如：

```text
%TEMP%\superspowers-smoke-test\
```

在该目录中仅执行：

1. 打开一个空白会话
2. 调用 skill discovery
3. 调用一个只读类 skill
4. 观察是否出现可用的 `superpowers` skills
5. 不执行任何真实业务实现，不创建 PR，不执行 merge/push/cleanup

### 4.3 不可执行项

以下能力在本阶段仅做可见性验证，不得实际运行：

- worktree 创建
- subagent 驱动执行
- review 自动化
- closeout 自动化
- merge / push / PR comment / worktree cleanup

## 5. 当前放行矩阵

### 5.1 现阶段判定

| 项目 | 判定 |
|---|---|
| Claude Code 作为实现主端 | `WAITING FOR USER EVIDENCE` |
| opencode 作为兼容端 | `WAITING FOR USER EVIDENCE` |
| Superpowers skills 可用性 | `WAITING FOR USER EVIDENCE` |
| repository-safe schema 与工具端兼容 | `WAITING FOR USER EVIDENCE` |
| 是否允许开始第一个试运行级业务 change | `否` |
| 即使允许试运行，是否仍必须禁止自动 finalize Git closeout | `是` |

### 5.2 当前结论

- 由于尚未获得实际安装/识别证据，不能将本阶段判定为通过
- `repo-safe schema` 与工具端的真实兼容性仍需等用户证据
- 在证据到齐前，不允许开始第一个试运行级业务 change

## 6. 需要用户回传的全部命令输出

### 6.1 Claude Code 端

请回传以下任一安装路径的完整命令输出：

```text
/plugin install superpowers@claude-plugins-official
```

或：

```text
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

并回传：

```text
Skill tool discovery output
```

以及：

```text
Tell me about your superpowers
```

### 6.2 opencode 端

请回传以下任一安装路径的完整命令输出：

```json
{
  "plugin": ["superpowers@git+https://github.com/obra/superpowers.git"]
}
```

或 Windows 备用路径（如果 git-backed 安装失败）：

```text
npm install superpowers@git+https://github.com/obra/superpowers.git --prefix "%USERPROFILE%\.config\opencode"
```

并回传：

```text
skill list
```

或对应的技能发现输出，以及：

```text
Tell me about your superpowers
```

### 6.3 需要同时提供的辅助信息

- 实际修改的用户级全局配置文件路径
- 修改前后 diff
- 回退方式
- 重启后版本号 / 插件加载日志

## 7. 保护范围确认

- [x] 未修改 `openspec/config.yaml`
- [x] 未修改 `openspec/schemas/superspec/schema.yaml`
- [x] 未修改 `docs/rectification/00-*` 至 `16-*`
- [x] 未修改 `AGENTS.md`
- [x] 未修改 `AGENT.md`
- [x] 未修改 `.claude/**`
- [x] 未修改 `.opencode/**`
- [x] 未修改业务代码、测试、依赖文件
- [x] 未执行 `git add`
- [x] 未执行 `commit`
- [x] 未执行 `push`
- [x] 未执行 `merge`
- [x] 未执行 `reset`
- [x] 未执行 `clean`
- [x] 未执行 `stash`
- [x] 未执行任何 DiagnoseToolPy 真实业务 apply/finalize

## 8. 结论

- Phase 3C 执行状态：`WAITING FOR USER EVIDENCE`
- Claude Code 作为实现主端是否验证通过：`WAITING FOR USER EVIDENCE`
- opencode 作为兼容端是否验证通过：`WAITING FOR USER EVIDENCE`
- Superpowers skills 可用性是否验证通过：`WAITING FOR USER EVIDENCE`
- repository-safe schema 与工具端是否兼容：`WAITING FOR USER EVIDENCE`
- 是否允许开始第一个“试运行级业务 change”：`否`
- 即使允许试运行，是否仍必须禁止自动 finalize Git closeout：`是`

本报告仅提供安装与验证路径，不自行安装、不改配置、不进入真实业务 change。
