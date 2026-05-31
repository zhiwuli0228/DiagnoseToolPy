## Why

当前侧边栏存在功能重叠和用户体验问题："诊断工作室"和"AI Diagnosis"都指向同一个页面，AI Diagnosis 已废弃只是重定向，中英文混合的命名风格不统一。用户需要在 Analysis Tasks 页面能快速发起诊断，而不是在侧边栏寻找入口。

## What Changes

- 从侧边栏移除"诊断工作室"菜单项（/diagnosis-studio）
- 从侧边栏移除"AI Diagnosis"菜单项（/diagnosis，已废弃）
- 在 AnalysisTasksPage 增加"开始诊断"快捷按钮，点击后跳转到 /diagnosis-studio?start=1
- 保留 AIDiagnosisButton（header 中的浮动按钮）作为备用入口

## Capabilities

### New Capabilities
- `quick-diagnosis-button`: 在 AnalysisTasksPage 页面增加诊断快捷入口

### Modified Capabilities
- 无

## Impact

- Frontend: App.tsx (侧边栏菜单), AnalysisTasksPage.tsx (新增按钮)
- 用户习惯改变：需从 Analysis Tasks 页面发起诊断
