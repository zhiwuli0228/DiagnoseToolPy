## Tasks

### Task 1: Remove diagnosis menu items from sidebar
- File: `frontend/src/App.tsx`
- Remove menu item with key `/diagnosis-studio`
- Remove menu item with key `/diagnosis`

### Task 2: Add diagnosis button to AnalysisTasksPage
- File: `frontend/src/pages/AnalysisTasksPage.tsx`
- Import `ThunderboltOutlined` icon
- Add "开始诊断" button in operation area
- Button onClick navigates to `/diagnosis-studio?start=1`

### Task 3: Verify changes
- [ ] Sidebar shows only 4 menu items
- [ ] AnalysisTasksPage shows diagnosis button
- [ ] Button click navigates correctly
