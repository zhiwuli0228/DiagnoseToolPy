## Context

当前的 AI 诊断是一次性生成模式：用户选择日志 → 调用 LLM → 返回诊断结论。这种模式在真实问题定位中效果有限，因为：
- 日志往往不足以支撑明确结论
- 用户可能有额外的上下文信息（堆栈、入参、问题现象）无法注入
- 单轮诊断无法处理复杂问题的逐步定位

本次设计在 `evidence-builder`（日志证据选择）基础上，新增用户自定义上下文输入和多轮对话式诊断能力。

**约束**：
- 无用户登录系统，session 通过浏览器 localStorage 管理
- LLM 使用 OpenAI-compatible API
- 后端必须独立于 FastAPI（保持 analyzer 模块的纯净）
- Case 存储为文件系统（`.md` + `.yaml`）

## Goals / Non-Goals

**Goals:**
- 支持用户输入问题现象、堆栈、入参等自定义上下文
- AI 能够主动追问缺失信息（最多 3 轮可配置）
- 完整对话历史可追溯
- Case 质量自动评估，高质量自动晋升，低质量进草稿箱
- 诊断优先级模式可切换（用户输入优先 vs 日志优先）

**Non-Goals:**
- 用户认证/登录系统
- 流式 LLM 响应（v1）
- 向量检索/语义搜索
- 跨设备会话同步
- 多诊断会话并行

---

## Decisions

### D1: API Endpoint 设计

**决策**：采用 RESTful API，会话资源嵌套在 URL 中。

```
POST   /api/diagnosis/conversation              # 创建/继续会话
GET    /api/diagnosis/conversation/{session_id} # 获取会话状态和历史
POST   /api/diagnosis/conversation/{session_id}/continue  # 用户回答追问
POST   /api/diagnosis/conversation/{session_id}/skip      # 跳过追问
POST   /api/diagnosis/conversation/{session_id}/end       # 结束会话
```

**为什么**：
- RESTful 语义清晰，与现有 `routes_diagnosis.py` 风格一致
- 会话 ID 作为路径参数，便于中间件拦截验证
- 不使用 WebSocket（当前规模不需要实时性）

**备选考虑**：
- GraphQL：过度设计，当前场景不需要
- 单一 POST 端点 + action 参数：不够 RESTful，URL 更冗长

---

### D2: 会话状态存储位置

**决策**：后端文件系统存储 + 前端 session_id 标识。

```
data/sessions/{session_id}/
├── metadata.yaml       # session_id, created_at, last_active, mode, turns
├── conversation/
│   ├── turn-001.json  # 第一轮对话
│   ├── turn-002.json
│   └── ...
└── draft_case/         # 如果质量不够，临时存放
```

**为什么**：
- 与现有 case 存储风格一致（文件系统 + YAML metadata）
- 便于调试和人工检查
- 后端可独立清理过期 session

**备选考虑**：
- 前端 localStorage 存储完整状态：数据量大，跨标签页无法共享
- Redis 存储：引入额外依赖，当前规模不需要

---

### D3: 主动追问触发机制

**决策**：两阶段 LLM 调用。

```
阶段1: 信息评估
  ↓
  LLM 判断信息是否充分
  ↓充分/不充分
  ├── 充分 → 阶段2A: 直接生成诊断
  └── 不充分 → 阶段2B: 生成追问问题
```

**Prompt 策略**：
```
阶段1 (评估):
  system: "你是一个诊断助手。评估用户输入是否充分..."
  user: "{user_context}\n\n证据:\n{evidence}"

  期望返回: { "sufficient": true/false, "missing": ["堆栈信息", ...], "confidence": 0.8 }

阶段2A (诊断):
  system: "你是一个资深后端稳定性工程师..."
  user: "基于以下信息提供诊断...\n{user_context}\n\n证据:\n{evidence}"

阶段2B (追问):
  system: "你是一个诊断助手。当信息不足时生成针对性问题..."
  user: "{user_context}\n\n缺失信息:\n{missing}"
```

**为什么**：
- 可控性强：追问逻辑与诊断逻辑分离
- 可配置：max_follow_up_rounds 控制追问轮数
- 调试友好：两个阶段独立测试

**备选考虑**：
- 单次调用同时返回诊断和追问：LLM 可能混淆两者职责
- 前端判断缺失字段：不够灵活，依赖预定义规则

---

### D4: Case 质量评分与晋升

**决策**：会话结束时触发评分，高分自动晋升，低分进草稿箱。

```
评分公式:
  total = rounds*0.3 + questions*0.2 + completeness*0.3 + ai_confidence*0.2

  thresholds:
    >= 8.0 → auto_promote
    < 8.0  → draft
```

**草稿箱清理**：每日定时任务清理超过 30 天的草稿。

**为什么**：
- 自动化晋升减少用户操作成本
- 草稿箱隔离低质量 case，保护 case base 检索质量
- 评分公式可调整权重

**备选考虑**：
- 全部自动晋升 + 用户手动降级：可能污染 case base
- 全部手动确认：用户体验差

---

### D5: 前端页面架构（B2 方案）

**决策**：新建 `DiagnosisStudio.tsx` 作为诊断主页面。

```
┌─────────────────────────────────────────────────────────────────────┐
│  DiagnosisStudio                                                    │
├───────────────────────────────┬─────────────────────────────────────┤
│  LeftPanel (40%)             │  RightPanel (60%)                   │
│  ┌─────────────────────────┐ │  ┌─────────────────────────────┐   │
│  │ SearchLogsPanel          │ │  │ UserContextInput             │   │
│  │ (from AnalysisTasksPage) │ │  │ (##现象, ##堆栈, ##入参)     │   │
│  └─────────────────────────┘ │  └─────────────────────────────┘   │
│  ┌─────────────────────────┐ │  ┌─────────────────────────────┐   │
│  │ EvidenceBasket           │ │  │ DiagnosisModeToggle          │   │
│  │ (selected logs)         │ │  │ (用户输入优先 / 日志优先)     │   │
│  └─────────────────────────┘ │  └─────────────────────────────┘   │
│                              │  ┌─────────────────────────────┐   │
│  [开始诊断]                  │  │ ConversationThread           │   │
│                              │  │ (AI诊断 / 追问 / 用户回复)    │   │
│                              │  └─────────────────────────────┘   │
│                              │  ┌─────────────────────────────┐   │
│                              │  │ [追问回复框] [跳过] [结束]    │   │
│                              │  └─────────────────────────────┘   │
└──────────────────────────────┴─────────────────────────────────────┘
```

**为什么**：
- 职责分离：左侧选日志，右侧做诊断
- 复用现有 EvidenceBasket 组件
- 不会破坏现有 AnalysisTasksPage

---

### D6: Session 管理（前端的角色）

**决策**：session_id 存储在 localStorage，前端在请求头中传递。

```typescript
// hooks/useSession.ts
const SESSION_KEY = 'diagnose_session_id';

function useSession() {
  const sessionId = localStorage.getItem(SESSION_KEY);

  useEffect(() => {
    if (!sessionId) {
      const newId = crypto.randomUUID();
      localStorage.setItem(SESSION_KEY, newId);
    }
  }, []);

  return sessionId;
}
```

**API 请求头**：
```
X-Session-ID: {session_id}
```

**为什么**：
- 简单直接，无需后端 session 创建 API
- 后端通过 session_id 识别会话，加载对应状态

---

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| **LLM 追问质量不可控** | 追问可能无意义或误导用户 | 提供追问示例 prompt，可调整 LLM temperature |
| **Session 存储膨胀** | 大量废弃 session 占用磁盘 | 每日清理 7 天无活动的 session |
| **草稿箱污染** | 低质量诊断占用存储 | 30 天自动清理 + 清理时记录日志 |
| **追问循环** | 用户与 AI 无限追问 | max_follow_up_rounds 强制上限 |
| **token 消耗** | 多轮对话 token 快速增长 | 智能截断 + token 预算控制 |

---

## Migration Plan

### Phase 1: 后端核心（不破坏现有功能）
1. 新增 `conversation_manager.py` — 会话状态管理
2. 新增 `question_generator.py` — 追问生成逻辑
3. 新增 `routes_conversation.py` — 新 API 端点
4. 新增 `stack_parser.py` — JVM 堆栈解析
5. 新增 `case_quality_scorer.py` — 质量评分

### Phase 2: 前端核心
1. 新增 `DiagnosisStudio.tsx` — 新诊断页面
2. 新增 `UserContextInput.tsx` — 上下文输入组件
3. 新增 `ConversationThread.tsx` — 对话展示
4. 新增 `useSession.ts` — session hook
5. 新增 `conversationApi.ts` — API 客户端

### Phase 3: 集成与清理
1. 修改路由，指向新页面
2. 保留或删除旧的 `AIDiagnosisPage.tsx`（向后兼容）
3. 添加草稿箱清理定时任务
4. 添加 session 清理定时任务

### 回滚策略
- 前端：回滚路由配置，切回旧页面
- 后端：新 API 独立，不影响旧 `/api/diagnosis` 端点

---

## Open Questions

| Question | 优先级 | 状态 |
|----------|--------|------|
| LLM 追问的 temperature 是否需要单独配置？ | 中 | 待定 |
| 草稿箱是否需要独立的 UI 页面？ | 低 | 待定 |
| 多语言支持（中文/英文 prompt）？ | 低 | 不做 |
| session 清理的 cron 表达式？ | 中 | 每日凌晨 |
