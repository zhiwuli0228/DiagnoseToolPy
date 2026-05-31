## Context

诊断工具当前依赖 `LLMClient` 调用外部 LLM API 完成 AI 诊断。调用链路为：

```
前端 DiagnosisStudioPage → /api/diagnosis/conversation → ConversationManager
  → DiagnosisOrchestrator.run() → LLMClient.chat() → 外部 LLM API
```

当 LLM API 不可用时，`LLMClient.chat()` 抛出 `LLMClientError`，上层路由捕获后仅返回错误信息，用户无法完成诊断。

OpenCode 部署于内网，具备 MCP 工具访问、完整 codebase 上下文和文件系统读取能力，比纯 API 方式更强大。用户希望：当 LLM API 不可用时，能导出完整诊断上下文到本地目录，在 OpenCode 中手动完成诊断。

## Goals / Non-Goals

**Goals:**
- 提供「预览 Prompt」按钮，让用户在任何时候可主动导出完整诊断上下文
- LLM API 调用失败时，自动降级引导用户导出工作区
- 工作区目录结构化组织，便于 OpenCode 直接读取文件而非依赖长 prompt
- 支持诊断结果的自动检测和导入提示

**Non-Goals:**
- 不实现 OpenCode MCP 直接集成（未来可扩展）
- 不强制要求用户回填诊断结果（检测到则提示，未检测到不阻塞）
- 不修改现有 `evidence-pack.md` 的格式或生成逻辑

## Decisions

### Decision 1: 工作区目录结构

**选择**: 子目录分类结构（`context/`、`logs/`、`cases/`、`prompt.md`）

**理由**: 当前诊断上下文（日志证据、用户描述、相似案例）是异构信息，分目录组织便于 OpenCode 按需读取，避免上下文爆炸时被迫截断。

**目录结构**:
```
{user_selected_dir}/
├── README.md              # 说明文件，包含诊断指令
├── prompt.md              # 诊断指令 prompt
├── context/
│   ├── phenomenon.md   # 问题现象
│   ├── stack.md        # 堆栈信息
│   └── params.md       # 关键入参
├── logs/
│   └── evidence-pack.md # 日志证据（压缩版）
└── cases/
    ├── case-001.md      # 相似案例 1
    └── case-002.md      # 相似案例 2
```

**替代方案**:
- 扁平结构（所有文件放同一目录）：简单但不便于区分信息类型
- 极简结构（仅 prompt.md + evidence-pack.md）：信息不足，诊断质量下降

### Decision 2: 目录选择方式

**选择**: 前端使用系统目录选择器，每次诊断时由用户指定工作区目录

**理由**:
- 用户对工作区位置有完全控制权
- 避免写入敏感目录或覆盖重要文件
- 未来可与 IDE/编辑器集成（用户可直接在对应目录打开 OpenCode）

**替代方案**:
- 固定目录模板（`data/diagnostic-workspace/{timestamp}/`）：自动但用户失去控制
- 配置默认目录：增加配置复杂度，用户意图不够显式

### Decision 3: 后端 Prompt 拼接与导出分离

**选择**: 在 `DiagnosisOrchestrator` 中提取 `_build_prompt()` 为 public 方法，`WorkspaceExporter` 调用该方法获取 prompt 内容而非重复拼接

**理由**:
- 复用现有 prompt 拼接逻辑，保持诊断指令一致性
- 避免两个代码路径（直接诊断 vs 导出诊断）产生差异
- 未来替换 prompt 模板时只需修改一处

### Decision 4: 结果检测机制

**选择**: 前端轮询检测用户工作区是否存在 `result.md`，检测到后弹出导入提示

**理由**:
- 前端发起请求，后端只负责检查文件和导入
- 不需要 WebSocket 或持久连接
- 用户可自由选择何时保存结果到 `result.md`

**替代方案**:
- 后端文件监听（watchdog）：增加复杂度，且在容器环境中不易实现
- 强制导入：用户必须回填，不符合「不强制要求」的原则

### Decision 5: 新增 API 端点

**选择**: 新增 `/api/diagnosis/export-workspace` 端点，统一处理工作区导出

**理由**:
- 统一的导出逻辑，便于维护和扩展
- 各诊断入口（conversation、search、cluster）均可调用
- 未来 opencode 集成时，可扩展为支持不同 backend

**端点设计**:
```typescript
// Request
interface ExportWorkspaceRequest {
  task_id?: string;          // 已有任务 ID
  session_id?: string;        // 会话 ID（用于 conversation 场景）
  workspace_dir: string;      // 用户选择的目录（绝对路径）
  selections?: SelectionItem[]; // 搜索/聚类选中的证据
}

// Response
interface ExportWorkspaceResponse {
  success: boolean;
  workspace_dir: string;
  files_written: string[];    // 写入的文件列表
  detection_hint?: string;    // result.md 检测提示
}
```

## Risks / Trade-offs

- **[Risk] 敏感信息泄露** → 用户导出的工作区包含完整日志，可能包含密码、密钥等敏感信息
  - **Mitigation**: README.md 中增加安全提示；未来可增加「脱敏选项」
- **[Risk] result.md 检测时机** → 用户可能长时间不保存结果，或保存到其他文件名
  - **Mitigation**: 前端轮询 + 提示，用户可手动触发检测；不强制要求
- **[Risk] 长路径 Windows 兼容性** → 用户选择的目录可能超过 Windows 路径长度限制
  - **Mitigation**: 路径验证 + 错误提示
- **[Trade-off] 复杂度增加** → 新增工作区导出模块，与现有诊断流程并行
  - **Mitigation**: 严格按 spec 拆分，逐步实现，避免一次性大规模重构

## Migration Plan

1. **Phase 1**: 实现 `workspace_exporter.py` 模块，验证目录写入逻辑
2. **Phase 2**: 新增 `/api/diagnosis/export-workspace` 端点
3. **Phase 3**: 前端增加「预览 Prompt」按钮和目录选择器
4. **Phase 4**: 各诊断路由增加降级处理（LLM 失败时引导导出）
5. **Phase 5**: 实现 result.md 检测和导入流程

**回滚策略**: 功能通过 feature flag 控制，默认关闭。出现问题可关闭 flag 降级。

## Open Questions

1. **result.md 检测频率**: 前端轮询间隔多少合适？（建议 5-10 秒）
2. **文件覆盖策略**: 当工作区目录已存在文件时，是否覆盖？是否需要用户确认？
3. **大日志处理**: 当 evidence-pack.md 很大时，是否需要分块或压缩？
