## Overview

简化侧边栏，将诊断入口整合到 Analysis Tasks 页面。

## Changes

### 1. App.tsx 侧边栏修改

```typescript
// 当前 menuItems (删除 diagnosis-studio 和 diagnosis)
const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/analysis', icon: <FileSearchOutlined />, label: 'Analysis Tasks' },
  { key: '/cases', icon: <FolderOutlined />, label: 'Casebase' },
  // 删除 { key: '/diagnosis-studio', ... }
  // 删除 { key: '/diagnosis', ... }
  { key: '/settings', icon: <SettingOutlined />, label: 'Settings' },
];
```

### 2. AnalysisTasksPage.tsx 新增按钮

在页面顶部操作区域增加"开始诊断"按钮：

```typescript
<Button
  type="primary"
  icon={<ThunderboltOutlined />}
  onClick={() => navigate('/diagnosis-studio?start=1')}
>
  开始诊断
</Button>
```

## File Changes

- `frontend/src/App.tsx`: 删除 2 个 menuItems
- `frontend/src/pages/AnalysisTasksPage.tsx`: 新增诊断按钮
