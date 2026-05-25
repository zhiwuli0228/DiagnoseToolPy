## Why

当前前端有约 190 处硬编码中文字符串分布在 15 个组件中，无法支持语言切换。需要全部替换为 i18n 调用。

## What Changes

将以下文件的硬编码字符串替换为 t('key') 调用：
- App.tsx (~1处)
- EvidenceBasket.tsx (~25处)
- AIDiagnosisButton.tsx (~20处)
- ClusterProgress.tsx (~4处)
- ClusterResult.tsx (~15处)
- ConversationThread.tsx (~10处)
- DiagnosisModeToggle.tsx (~6处)
- DiagnosisActionBar.tsx (~3处)
- AIQuestionCard.tsx (~2处)
- UserContextInput.tsx (~15处)
- SearchPanel.tsx (~15处)
- DiagnosisStudioPage.tsx (~60处)
- AnalysisTasksPage.tsx (~40处)
- useResultDetection.ts (~4处)
- AppLayout.tsx (~1处)

## Capabilities

### New Capabilities
- `i18n-translations`: 所有界面文字的翻译 key

### Modified Capabilities
- 无

## Impact

- Frontend: 约 15 个组件文件修改
- 依赖 i18n-infrastructure change
