# Spec: conversational-diagnosis

## Spec ID

`conversational-diagnosis`

## Change ID

`conversational-diagnosis-with-user-context`

## Overview

多轮对话式诊断能力。用户输入上下文后，AI 分析并主动追问缺失信息，支持多轮迭代，最终生成诊断结论并可选存入 case。

---

## ADDED Requirements

### Requirement: 会话创建与初始化

系统 SHALL 在用户首次发起诊断时创建诊断会话。系统 SHALL 使用浏览器 localStorage 中的 session_id 标识会话。

#### Scenario: 新会话创建
- **WHEN** 用户在无 session_id 状态下发起诊断请求
- **THEN** 系统生成新的 session_id 并返回，浏览器将 session_id 存入 localStorage

#### Scenario: 已有会话恢复
- **WHEN** 用户在有 session_id 状态下发起诊断请求
- **THEN** 系统恢复该 session_id 对应的会话上下文

### Requirement: 用户上下文解析

系统 SHALL 解析用户输入中的结构化标记。系统 SHALL 支持以下标记格式：
- `##现象` — 问题现象描述
- `##堆栈` — 运行时堆栈信息
- `##入参` — 关键入参信息

#### Scenario: 完整上下文输入
- **WHEN** 用户输入包含所有三个标记
- **THEN** 系统解析出三个独立的上下文字段

#### Scenario: 部分上下文输入
- **WHEN** 用户输入只包含部分标记（如只有 `##现象`）
- **THEN** 系统解析已有字段，缺失字段标记为空

### Requirement: 主动追问机制

当用户上下文信息不足以支撑明确诊断时，系统 SHALL 让 LLM 生成追问问题。系统 SHALL 支持配置最大追问轮数（默认 3 轮）。

#### Scenario: 信息充足直接诊断
- **WHEN** 用户提供了完整的堆栈和现象描述
- **THEN** 系统直接生成诊断结论，无需追问

#### Scenario: 信息不足触发追问
- **WHEN** 用户只提供了问题现象，无堆栈信息
- **THEN** 系统返回追问：「请提供异常堆栈信息以便进一步定位」

#### Scenario: 追问轮数耗尽
- **WHEN** 追问轮数达到配置上限（默认 3 轮）
- **THEN** 系统 SHALL 强制生成诊断结论，并明确告知「信息可能不完整，结论仅供参考」

### Requirement: 跳过追问机制

用户 SHALL 有权跳过追问，直接基于现有信息强制生成诊断结论。

#### Scenario: 用户选择跳过
- **WHEN** 用户点击「跳过，直接给出诊断」
- **THEN** 系统生成诊断结论，并在结论前显示「以下结论基于不完整信息，仅供参考」

### Requirement: 多轮对话历史

系统 SHALL 维护完整的对话历史，包括用户输入、AI 诊断、AI 追问、用户追问回复。

#### Scenario: 查看对话历史
- **WHEN** 用户在诊断过程中查看历史
- **THEN** 系统展示完整的对话时间线

### Requirement: 诊断模式切换

用户 SHALL 能够切换诊断优先级模式：
- 「用户输入优先」— 以用户描述为主，日志作为补充
- 「日志优先」— 以日志分析为主，用户描述作为补充

#### Scenario: 切换到用户输入优先
- **WHEN** 用户选择「用户输入优先」模式
- **THEN** 系统在构建 prompt 时将用户上下文放在日志证据之前

### Requirement: 会话状态持久化

系统 SHALL 在每个对话轮次后保存会话状态到 `data/sessions/{session_id}/`。

#### Scenario: 会话中断恢复
- **WHEN** 用户关闭页面后重新打开（同一浏览器）
- **THEN** 系统恢复最近一次对话状态

---

## Data Formats

### `data/sessions/{session_id}/conversation/{turn_id}.json`

```json
{
  "turn_id": "001",
  "user_context": {
    "phenomenon": "服务偶发超时，错误率 2%",
    "stack": "at OrderService.query(...)\nat OrderController.get(...)",
    "params": "orderId=12345, userId=789"
  },
  "evidence_refs": ["log_id_1", "log_id_2"],
  "ai_question": "请提供异常堆栈信息以便进一步定位",
  "ai_diagnosis": "根据现有信息，怀疑是 OOM 导致 GC 停顿",
  "mode": "user-priority",
  "timestamp": "2026-05-24T10:30:00Z"
}
```

---

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/diagnosis/conversation` | 创建新会话或继续已有会话 |
| `GET` | `/api/diagnosis/conversation/{session_id}` | 获取会话状态和历史 |
| `POST` | `/api/diagnosis/conversation/{session_id}/continue` | 继续对话（回答追问） |
| `POST` | `/api/diagnosis/conversation/{session_id}/skip` | 跳过追问直接出结论 |
| `POST` | `/api/diagnosis/conversation/{session_id}/end` | 结束会话，触发 case 生成 |

---

## Acceptance Criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC1 | 新会话创建返回 session_id | API 测试 |
| AC2 | 已有会话恢复上下文 | API 测试 |
| AC3 | 上下文标记解析正确 | 单元测试 |
| AC4 | 信息不足时触发追问 | 集成测试（mock LLM） |
| AC5 | 追问轮数上限强制结束 | 集成测试 |
| AC6 | 跳过机制正常 | 集成测试 |
| AC7 | 对话历史正确保存 | 存储验证 |
| AC8 | 模式切换影响 prompt 构建 | 单元测试 |
