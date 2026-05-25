## Overview

将所有硬编码中文字符串替换为 i18n t() 调用。

## 翻译 Key 命名规范

采用层级命名：`{page}.{component}.{element}`

示例：
- `diagnosisStudio.startButton`
- `analysisTasks.previewPrompt`
- `evidenceBasket.selectLogs`

## 替换模式

### 简单字符串
```tsx
// Before
<span>开始诊断</span>

// After
<span>{t('diagnosis.startButton')}</span>
```

### 带变量的字符串
```tsx
// Before
`已选 ${selections.length} 条证据`

// After
t('evidence.selectedCount', { count: selections.length })
```

### Placeholder
```tsx
// Before
placeholder="描述观察到的问题现象"

// After
placeholder={t('evidenceBasket.problemPlaceholder')}
```

## 文件清单

需修改约 15 个组件文件，详见 tasks.md。
