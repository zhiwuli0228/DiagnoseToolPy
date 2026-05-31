# Spec: context-priority-mode

## Spec ID

`context-priority-mode`

## Change ID

`conversational-diagnosis-with-user-context`

## Overview

诊断优先级模式能力。支持「用户输入优先」和「日志优先」两种诊断模式。

---

## ADDED Requirements

### Requirement: 模式定义

系统 SHALL 支持两种诊断优先级模式：

1. **用户输入优先（user-priority）**：以用户描述为主，日志作为补充
2. **日志优先（log-priority）**：以日志分析为主，用户描述作为补充

#### Scenario: 用户选择用户输入优先
- **WHEN** 用户切换到「用户输入优先」模式
- **THEN** 系统在 prompt 中将用户上下文放在日志证据之前

#### Scenario: 用户选择日志优先
- **WHEN** 用户切换到「日志优先」模式
- **THEN** 系统在 prompt 中将日志证据放在用户上下文之前

### Requirement: 模式切换 UI

系统 SHALL 在诊断工作区提供模式切换组件。

#### Scenario: 模式切换组件
- **WHEN** 用户在诊断工作区
- **THEN** 系统显示模式切换按钮/下拉框

### Requirement: 模式影响 Prompt 构建

不同模式 SHALL 影响 LLM prompt 的结构：

**用户输入优先模式 Prompt 结构**：
```
1. 用户提供的上下文（现象、堆栈、入参）
2. 日志证据（作为补充参考）
3. 相似历史案例
```

**日志优先模式 Prompt 结构**：
```
1. 日志证据分析
2. 用户提供的上下文（作为补充信息）
3. 相似历史案例
```

### Requirement: 模式存储

当前选择的模式 SHALL 随会话一起存储。

#### Scenario: 模式持久化
- **WHEN** 用户切换诊断模式
- **THEN** 系统将会话模式保存到会话状态

### Requirement: 模式默认值

新会话的默认模式 SHALL 是「用户输入优先」。

#### Scenario: 新会话默认模式
- **WHEN** 用户创建新会话
- **THEN** 系统默认选择「用户输入优先」模式

### Requirement: 追问不受模式影响

追问机制 SHALL 不受优先级模式影响，始终基于当前可用的信息生成。

#### Scenario: 追问与模式无关
- **WHEN** 系统需要追问
- **THEN** 追问内容不因模式不同而变化

---

## API Field

### `POST /api/diagnosis/conversation` 请求体

```json
{
  "session_id": "uuid",
  "user_context": { ... },
  "evidence_refs": ["log_id_1"],
  "mode": "user-priority" | "log-priority",
  "max_follow_up_rounds": 3
}
```

---

## Frontend Component

### `DiagnosisModeToggle`

```typescript
interface DiagnosisModeToggleProps {
  value: 'user-priority' | 'log-priority';
  onChange: (mode: 'user-priority' | 'log-priority') => void;
}
```

显示：
- 「用户输入优先」— 以用户描述为主
- 「日志优先」— 以日志分析为主

---

## Acceptance Criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC1 | 模式切换 UI 正确显示 | 前端测试 |
| AC2 | 模式切换影响 prompt 结构 | 集成测试（mock LLM） |
| AC3 | 模式随会话持久化 | API 测试 |
| AC4 | 新会话默认用户输入优先 | API 测试 |
| AC5 | 追问不受模式影响 | 集成测试 |
