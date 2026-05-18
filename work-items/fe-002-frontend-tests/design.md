# 前端测试策略方案

## 项目背景

- **技术栈**：React 18 + TypeScript + Vite + Ant Design
- **现有状态**：无测试框架
- **目标**：建立可持续的前端测试体系，支持 CI 自动化

---

## 1. 测试框架选型

### 推荐：Vitest

| 对比项 | Vitest | Jest |
|--------|--------|------|
| Vite 集成 | 原生支持，零配置 | 需额外配置 transformers |
| TypeScript | 原生 TS 支持 | 需额外配置 ts-jest |
| HMR 速度 | 极快（Vite 子进程） | 较慢 |
| Mock API | 丰富，接近 Jest | 丰富 |
| CI 兼容 | ✅ | ✅ |
| Ant Design 兼容 | ✅ | ✅（需配置） |
| 学习曲线 | 低（API 与 Jest 相似） | 低 |

**结论**：Vitest 与 Vite 同源，配置最少，速度最快，与现有项目契合度最高。

---

## 2. 测试库选型

| 库 | 用途 | 理由 |
|----|------|------|
| `@testing-library/react` | 组件测试 | DOM 行为测试，不依赖实现细节 |
| `@testing-library/user-event` | 用户交互模拟 | 补充 `fireEvent`，更接近真实用户行为 |
| `msw` (Mock Service Worker) | API Mock | 拦截 HTTP 层，支持真实 fetch/axios，与 pytest 可共存 |
| `vitest` | 测试运行器 | 内置 expect/match/mock |

---

## 3. 测试目录结构

```
src/
├── __tests__/                    # 集成/端到端测试（可选）
├── components/
│   └── layout/
│       └── AppLayout.tsx
│       └── __tests__/
│           └── AppLayout.test.tsx
├── pages/
│   ├── DashboardPage.tsx
│   ├── AIDiagnosisPage.tsx
│   ├── AnalysisTasksPage.tsx
│   ├── TaskDetailPage.tsx
│   ├── CasebasePage.tsx
│   ├── CaseDetailPage.tsx
│   ├── SettingsPage.tsx
│   └── __tests__/               # 各页面同目录或统一收集
│       ├── DashboardPage.test.tsx
│       ├── AIDiagnosisPage.test.tsx
│       └── ...
├── api/
│   ├── client.ts
│   ├── caseApi.ts
│   ├── diagnosisApi.ts
│   ├── sourceApi.ts
│   └── __tests__/
│       ├── caseApi.test.ts
│       ├── diagnosisApi.test.ts
│       └── sourceApi.test.ts
└── mocks/
    ├── handlers.ts              # msw 请求处理
    ├── browser.ts               # msw 浏览器启动
    └── server.ts                # msw Node 端启动（CI 用）
```

---

## 4. Mock 策略

### 4.1 API Mock（msw）

采用 **msw** 而非直接 mock axios 模块，理由：
- 拦截 HTTP 层，测试更接近真实请求
- 前后端 Mock 可并存（后端用 pytest fixtures，前端用 msw）
- 支持请求验证（检查参数）

```typescript
// src/mocks/handlers.ts 示例
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const handlers = [
  http.get('/api/cases', () => HttpResponse.json([{ id: 1, name: 'test' }])),
  http.post('/api/diagnosis', () => HttpResponse.json({ result: 'ok' })),
];

export const server = setupServer(...handlers);
```

### 4.2 组件内 Mock

- 使用 `vi.mock()` mock 组件依赖（如子组件、hooks）
- 使用 `@testing-library/react` 的 `MockedProvider`（Apollo 等场景）

### 4.3 Vitest 内置 Mock

```typescript
import { vi } from 'vitest';
vi.mock('@/api/client', () => ({
  client: { get: vi.fn() }
}));
```

---

## 5. 关键测试场景

### 5.1 页面组件（6个）

| 页面 | 关键测试场景 |
|------|-------------|
| `DashboardPage` | 渲染统计卡片、加载状态、空状态 |
| `AIDiagnosisPage` | 表单提交、验证、加载中状态、错误提示 |
| `AnalysisTasksPage` | 任务列表渲染、分页、筛选、空状态 |
| `TaskDetailPage` | 详情加载、状态切换、刷新 |
| `CasebasePage` | 病例列表、搜索、详情跳转 |
| `CaseDetailPage` | 病例详情渲染、相关操作 |
| `SettingsPage` | 设置项保存、表单验证 |

### 5.2 API 客户端（4个）

| 模块 | 关键测试场景 |
|------|-------------|
| `client.ts` | 请求拦截、Header 注入、错误响应处理 |
| `caseApi.ts` | CRUD 请求构造、参数传递 |
| `diagnosisApi.ts` | 诊断请求构造、响应解析 |
| `sourceApi.ts` | 数据源请求构造 |

### 5.3 通用组件

| 组件 | 关键测试场景 |
|------|-------------|
| `AppLayout` | 布局渲染、导航菜单高亮、响应式 |

---

## 6. CI 集成

### 6.1 npm script

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  }
}
```

### 6.2 CI 配置示例（GitHub Actions）

```yaml
- name: Run Frontend Tests
  run: npm run test:coverage
```

### 6.3 覆盖率目标

| 类型 | 目标 |
|------|------|
| API 模块 | 80%+ |
| 页面组件 | 60%+（交互逻辑优先） |
| 通用组件 | 70%+ |

---

## 7. 实现步骤与工作量估算

### Phase 1：基础设施（0.5 天）

| 任务 | 工作量 |
|------|--------|
| 安装依赖（vitest, @testing-library/react, @testing-library/user-event, msw） | 0.1 天 |
| 配置 `vite.config.ts` 中的 vitest | 0.1 天 |
| 配置 `tsconfig.json` 测试路径 | 0.1 天 |
| 初始化 msw service worker | 0.2 天 |

### Phase 2：API 测试（1 天）

| 任务 | 工作量 |
|------|--------|
| 编写 msw handlers（4个 API 模块） | 0.3 天 |
| 编写 client.ts 测试 | 0.2 天 |
| 编写 caseApi.ts 测试 | 0.15 天 |
| 编写 diagnosisApi.ts 测试 | 0.15 天 |
| 编写 sourceApi.ts 测试 | 0.15 天 |

### Phase 3：组件测试（1.5 天）

| 任务 | 工作量 |
|------|--------|
| AppLayout 测试 | 0.2 天 |
| DashboardPage 测试 | 0.2 天 |
| AIDiagnosisPage 测试 | 0.25 天 |
| AnalysisTasksPage 测试 | 0.2 天 |
| TaskDetailPage 测试 | 0.2 天 |
| CasebasePage 测试 | 0.15 天 |
| CaseDetailPage 测试 | 0.15 天 |
| SettingsPage 测试 | 0.15 天 |

### Phase 4：CI 与文档（0.5 天）

| 任务 | 工作量 |
|------|--------|
| GitHub Actions 配置 | 0.2 天 |
| 测试文档编写 | 0.3 天 |

---

## 8. 依赖清单

```json
{
  "devDependencies": {
    "vitest": "^2.x",
    "@vitest/coverage-v8": "^2.x",
    "@testing-library/react": "^16.x",
    "@testing-library/user-event": "^14.x",
    "jsdom": "^25.x",
    "msw": "^2.x"
  }
}
```

> **注意**：`@testing-library/react` v16 需要 React 18，版本匹配无误。

---

## 9. 风险与注意事项

| 风险 | 缓解方案 |
|------|----------|
| Ant Design 组件样式 mock | 使用 `@testing-library/react` 直接测行为，不测样式 |
| axios 与 msw 兼容 | msw 拦截 HTTP 层，axios 正常发起请求即可 |
| 异步状态测试 | 使用 `waitFor` 或 `findBy` 查询符 |
| CI 环境 msw | 使用 `server.listen({ onUnhandledRequest: 'error' })` 强制检查未处理请求 |

---

## 10. 总结

| 项目 | 选择 |
|------|------|
| 测试框架 | Vitest |
| 组件测试库 | @testing-library/react + user-event |
| API Mock | msw |
| 测试位置 | 组件同目录 `__tests__/` 或 `api/__tests__/` |
| CI 支持 | ✅（vitest run + coverage） |
| 总工作量 | **~3.5 人天** |
