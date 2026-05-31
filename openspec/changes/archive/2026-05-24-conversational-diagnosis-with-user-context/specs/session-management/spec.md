# Spec: session-management

## Spec ID

`session-management`

## Change ID

`conversational-diagnosis-with-user-context`

## Overview

浏览器 session 管理能力。通过 localStorage 存储 session_id，实现同一浏览器会话保持。

---

## ADDED Requirements

### Requirement: Session ID 生成

系统 SHALL 在用户首次访问时生成唯一的 session_id。session_id SHALL 是 UUID v4 格式。

#### Scenario: 首次访问生成 session_id
- **WHEN** 用户首次打开诊断页面且 localStorage 中无 session_id
- **THEN** 系统生成 UUID v4 格式的 session_id 并存入 localStorage

### Requirement: Session ID 持久化

系统 SHALL 将 session_id 持久化到浏览器 localStorage，键名为 `diagnose_session_id`。

#### Scenario: Session ID 持久化
- **WHEN** session_id 生成后
- **THEN** 系统执行 `localStorage.setItem('diagnose_session_id', session_id)`

### Requirement: Session ID 读取与恢复

系统 SHALL 在页面加载时从 localStorage 读取 session_id。

#### Scenario: 页面加载恢复 session
- **WHEN** 用户刷新或重新打开页面
- **THEN** 系统从 localStorage 读取 session_id 并用于后续请求

### Requirement: 不同浏览器独立 Session

系统 SHALL 确保不同浏览器或不同隐私模式产生独立的 session_id。

#### Scenario: 隐私模式新 session
- **WHEN** 用户在隐私/无痕模式打开页面
- **THEN** 系统生成新的 session_id（隐私模式 localStorage 不共享）

### Requirement: Session 生命周期

Session SHALL 在以下情况终结：
- 用户主动结束诊断并选择不保存
- 超过 7 天无任何活动
- 用户清除浏览器数据

#### Scenario: Session 超时清理
- **WHEN** Session 超过 7 天无活动
- **THEN** 系统在下次访问时生成新 session_id

---

## Frontend Integration

### Hook: `useSession`

```typescript
interface SessionManager {
  sessionId: string | null;
  isNewSession: boolean;
  createSession: () => void;
}
```

- `sessionId`: 当前 session_id，无则为 null
- `isNewSession`: 是否是新创建的 session（用于区分恢复 vs 新建）
- `createSession`: 强制创建新 session（用于用户主动「重新开始」）

---

## API Headers

所有诊断相关 API SHALL 在请求头中包含 session_id：

```
X-Session-ID: {session_id}
```

---

## Acceptance Criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC1 | 首次访问生成 UUID session_id | 单元测试 |
| AC2 | localStorage 持久化正确 | 浏览器测试 |
| AC3 | 刷新页面 session_id 不变 | 浏览器测试 |
| AC4 | 隐私模式生成新 session | 浏览器测试 |
| AC5 | 过期 session 正确处理 | 单元测试 |
