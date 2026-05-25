import { Dropdown, Button } from 'antd';
import type { MenuProps } from 'antd';
import { GlobalOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation();

  const items: MenuProps['items'] = [
    { key: 'zh', label: t('languageSwitcher.chinese') },
    { key: 'en', label: t('languageSwitcher.english') },
  ];

  const currentLang = i18n.language === 'en' ? 'EN' : t('languageSwitcher.chinese');

  return (
    <Dropdown
      menu={{
        items,
        selectedKeys: [i18n.language],
        onClick: ({ key }) => i18n.changeLanguage(key),
      }}
      placement="bottomRight"
      trigger={['click']}
    >
      <Button icon={<GlobalOutlined />}>
        {currentLang}
      </Button>
    </Dropdown>
  );
}

export default LanguageSwitcher;
