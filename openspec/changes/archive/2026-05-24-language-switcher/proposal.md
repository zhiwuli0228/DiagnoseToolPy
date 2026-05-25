## Why

用户需要能在界面上切换中英文，当前没有语言切换入口。需要提供便捷的语言切换方式。

## What Changes

- 创建 `src/components/LanguageSwitcher.tsx` 语言切换组件
- 在 App.tsx 的 Header 区域集成语言切换器
- 使用 localStorage 持久化语言选择
- 切换语言后全局生效

## Capabilities

### New Capabilities
- `language-switcher`: Header 区域的语言切换下拉框

### Modified Capabilities
- 无

## Impact

- Frontend: App.tsx, 新增 LanguageSwitcher.tsx
- 依赖 i18n-infrastructure change
