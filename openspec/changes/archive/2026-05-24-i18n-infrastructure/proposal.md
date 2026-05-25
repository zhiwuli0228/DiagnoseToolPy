## Why

当前前端没有 i18n 系统，所有界面文字都是硬编码的中英文混合字符串。随着应用功能增加，需要支持中英文两种语言切换以满足不同用户需求。

## What Changes

- 安装 `react-i18next` 和 `i18next` 依赖
- 创建 `src/i18n/index.ts` i18n 配置文件
- 创建 `src/locales/en.json` 英文翻译文件（初始为空结构）
- 创建 `src/locales/zh.json` 中文翻译文件（迁移现有硬编码中文）
- 创建 `src/hooks/useTranslation.ts` 翻译 hook 封装

## Capabilities

### New Capabilities
- `i18n-system`: 前端国际化基础设施，支持中英文切换

### Modified Capabilities
- 无

## Impact

- Frontend: 新增 i18n 配置和翻译文件
- 依赖: react-i18next, i18next
