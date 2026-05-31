## Overview

建立 react-i18next 国际化基础设施。

## Architecture

```
src/
├── i18n/
│   └── index.ts          # i18next 配置
├── locales/
│   ├── en.json           # 英文翻译
│   └── zh.json           # 中文翻译
├── hooks/
│   └── useTranslation.ts # 翻译 hook 封装
```

## Dependencies

```bash
npm install react-i18next i18next i18next-browser-languagedetector
```

## i18n Configuration (index.ts)

```typescript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import en from '../locales/en.json';
import zh from '../locales/zh.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { en: { translation: en }, zh: { translation: zh } },
    lng: localStorage.getItem('i18nextLng') || 'zh',
    fallbackLng: 'en',
  });

export default i18n;
```

## Translation Files Structure

```json
// locales/zh.json
{
  "nav": {
    "dashboard": "仪表盘",
    "analysisTasks": "分析任务",
    "casebase": "案例库",
    "settings": "设置"
  },
  "diagnosis": {
    "start": "开始诊断",
    "aiAssistant": "AI 诊断助手"
  }
}
```
