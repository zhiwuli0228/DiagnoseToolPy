## Overview

在 Header 区域增加语言切换下拉框。

## Component Structure

```typescript
// LanguageSwitcher.tsx
import { Dropdown, Button } from 'antd';
import { GlobalOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

export function LanguageSwitcher() {
  const { i18n } = useTranslation();

  const items = [
    { key: 'zh', label: '中文' },
    { key: 'en', label: 'English' },
  ];

  return (
    <Dropdown
      menu={{
        items,
        selectedKeys: [i18n.language],
        onClick: ({ key }) => i18n.changeLanguage(key),
      }}
      placement="bottomRight"
    >
      <Button icon={<GlobalOutlined />}>
        {i18n.language === 'zh' ? '中文' : 'EN'}
      </Button>
    </Dropdown>
  );
}
```

## Integration

在 App.tsx Header 中添加：

```tsx
<Header>
  <LanguageSwitcher />
  <AIDiagnosisButton ... />
</Header>
```

## Persistence

通过 i18next-browser-languagedetector 自动检测和持久化语言选择。
