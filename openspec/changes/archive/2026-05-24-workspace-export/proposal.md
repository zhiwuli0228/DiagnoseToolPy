## Why

当前诊断工具依赖外部 LLM API 提供 AI 诊断能力。当 LLM 不可用（网络问题、服务宕机、API 限流）时，用户只能等待，无法完成诊断。同时，内部部署的 OpenCode 具备 MCP 工具访问、完整 codebase 上下文和文件读取能力，理论上能提供更准确的诊断。因此需要：
1. 当 LLM 可用时，提供「预览 Prompt」选项让用户主动导出
2. 当 LLM 不可用时，自动降级，将诊断所需的完整上下文导出到用户指定目录，用户可在 OpenCode 中手动完成诊断
3. 支持诊断结果的自动回收，形成完整闭环

## What Changes

- **新增「预览 Prompt」按钮**：在诊断工作室页面，提供按钮让用户预览并导出完整诊断上下文到指定工作区目录
- **LLM 失败自动降级**：当 LLM API 调用失败时，自动弹出目录选择器，引导用户导出工作区
- **工作区目录结构化导出**：将日志证据、用户上下文、相似案例、诊断指令等分目录组织
- **诊断结果自动检测**：用户将结果保存为 `result.md` 后，系统自动检测并提示导入
- **覆盖全部诊断入口**：对话式诊断（/api/diagnosis/conversation）、一键诊断（/api/diagnosis）、搜索/聚类诊断（/api/diagnosis/search, /api/diagnosis/cluster）

## Capabilities

### New Capabilities

- `workspace-export`: 工作区导出能力。将完整诊断上下文（日志证据、用户上下文、相似案例）分目录组织到用户指定路径，支持 OpenCode 直接读取诊断。核心包括工作区组装、目录写入、文件模板化。
- `diagnosis-degraded-mode`: 诊断降级模式能力。当 LLM 不可用时，自动或手动触发工作区导出，提供有别于「无诊断可用」的降级方案。
- `result-auto-recovery`: 诊断结果自动回收能力。检测用户工作区中的 `result.md`，自动提示工程师导入诊断结论，形成诊断闭环。

### Modified Capabilities

- `evidence-report-generation`: 当前 `evidence-pack.md` 格式无需变化，但导出时需支持分目录结构；能力本身无需求变更。

## Impact

- **前端**: `DiagnosisStudioPage` 新增「预览 Prompt」按钮和目录选择器；各诊断入口页面在 LLM 失败时展示降级引导
- **后端**: 新增 `workspace_exporter.py` 模块；各诊断路由增加降级处理逻辑；新增 `/api/diagnosis/export-workspace` 端点
- **存储**: 新增 `data/sessions/{session_id}/workspace/` 用于会话级工作区（可选，按需创建）；诊断结果存回用户工作区目录
- **配置**: 无需新增配置项
