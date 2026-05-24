## Why

当前的 AI 诊断只能基于已有日志进行一次性分析，但在真实问题定位场景中，日志往往不足以得出明确结论。用户需要能够补充问题现象、运行时堆栈、关键入参等自定义上下文信息，并与 AI 进行多轮交互式诊断，让 AI 主动追问缺失信息，最终得到更准确的诊断结果。

## What Changes

### Backend Changes

1. **诊断会话 API**：新增 `POST /api/diagnosis/conversation` — 创建或继续诊断会话，支持多轮对话
2. **用户上下文提取**：后端解析用户输入的 `##现象`、`##堆栈`、`##入参` 标记，结构化处理后注入 prompt
3. **主动追问机制**：当用户上下文信息不足时，LLM 主动生成追问问题；支持配置最大追问轮数（默认 3 轮）
4. **会话状态管理**：后端维护诊断会话状态（session_id 标识），支持会话上下文续写
5. **智能截断**：JVM 堆栈解析器 — 识别重复帧、合并相同包前缀、精简过长堆栈
6. **Case 质量评分与自动晋升**：诊断结束后根据对话轮数、用户反馈、AI 置信度评估质量，高质量自动晋升为正式 case，低质量存入草稿箱
7. **草稿箱机制**：`case-draft.md` 非正式 case，不参与检索，定期清理过期草稿

### Frontend Changes

1. **诊断工作区页面**：重构诊断入口为独立页面（B2 方案），左侧日志选择区，右侧诊断工作区
2. **用户上下文输入**：结构化输入区域，支持 `##现象`、`##堆栈`、`##入参` 标记格式，JVM 堆栈粘贴时自动提示精简
3. **对话式诊断 UI**：展示 AI 追问、历史对话轮次、用户追问输入框
4. **诊断模式切换**：用户可切换"用户输入优先"或"日志优先"模式
5. **Session 管理**：浏览器 localStorage 存储 session_id，同一浏览器自动关联会话

### Storage Changes

1. **会话存储**：`data/sessions/{session_id}/` 存储会话状态和对话历史
2. **草稿 Case**：`data/cases/_drafts/` 存储未确认质量的草稿 case
3. **对话历史**：`data/cases/{case_id}/conversation/` 存储完整多轮对话

## Capabilities

### New Capabilities

- `conversational-diagnosis`: 多轮对话式诊断能力。用户输入上下文后，AI 分析并主动追问缺失信息，支持多轮迭代，最终生成诊断结论并可选存入 case
- `session-management`: 浏览器 session 管理能力。通过 localStorage 存储 session_id，实现同一浏览器会话保持
- `case-quality-scoring`: Case 质量评分能力。根据对话轮数、用户反馈、AI 置信度评估诊断质量，决定自动晋升或进入草稿箱
- `jvm-stack-parser`: JVM 堆栈解析与精简能力。识别重复帧、合并相同包前缀、精简过长堆栈
- `context-priority-mode`: 诊断优先级模式能力。支持"用户输入优先"和"日志优先"两种诊断模式

### Modified Capabilities

- `ai-diagnosis`: 现有 ai-diagnosis 能力从单轮一次性诊断扩展为多轮对话式诊断。修改 F3（DiagnosisOrchestrator）、F4（API 端点）行为，新增对话上下文、主动追问、草稿晋升逻辑

## Impact

### Backend

- 新增 `diagnose_tool/api/routes_conversation.py` — 对话式诊断 API
- 新增 `diagnose_tool/analyzer/conversation_manager.py` — 会话状态管理
- 新增 `diagnose_tool/analyzer/question_generator.py` — AI 追问生成逻辑
- 新增 `diagnose_tool/analyzer/stack_parser.py` — JVM 堆栈解析器
- 新增 `diagnose_tool/analyzer/case_quality_scorer.py` — Case 质量评分
- 修改 `diagnose_tool/api/routes_diagnosis.py` — 适配新对话流程
- 修改 `diagnose_tool/analyzer/diagnosis.py` — DiagnosisOrchestrator 支持对话上下文

### Frontend

- 新增 `frontend/src/pages/DiagnosisStudio.tsx` — 诊断工作区主页面（B2 方案）
- 新增 `frontend/src/components/UserContextInput.tsx` — 用户上下文输入组件
- 新增 `frontend/src/components/ConversationThread.tsx` — 对话历史展示组件
- 新增 `frontend/src/components/AIQuestionCard.tsx` — AI 追问卡片组件
- 新增 `frontend/src/components/DiagnosisModeToggle.tsx` — 诊断模式切换组件
- 新增 `frontend/src/hooks/useSession.ts` — Session 管理 hook
- 新增 `frontend/src/api/conversationApi.ts` — 对话式诊断 API 客户端
- 修改 `frontend/src/App.tsx` — 添加新路由
- 删除或重构 `frontend/src/pages/AIDiagnosisPage.tsx` — 整合到新页面

### Storage

- `data/sessions/{session_id}/` — 会话状态（临时，不持久化跨设备）
- `data/sessions/{session_id}/conversation/{turn_id}.json` — 对话轮次
- `data/cases/_drafts/{draft_id}/` — 草稿 case
- `data/cases/{case_id}/conversation/` — 正式 case 的对话历史

### API Changes

- `POST /api/diagnosis/conversation` — 新增，对话式诊断
- `GET /api/diagnosis/conversation/{session_id}` — 新增，获取会话状态和历史
- `POST /api/diagnosis/conversation/{session_id}/continue` — 新增，继续对话（追问响应）
- `POST /api/diagnosis/conversation/{session_id}/skip` — 新增，跳过追问直接出结论
