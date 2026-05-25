import { Radio, Space } from 'antd';
import type { RadioChangeEvent } from 'antd';
import { useTranslation } from 'react-i18next';

interface DiagnosisModeToggleProps {
  value: 'user-priority' | 'log-priority';
  onChange: (mode: 'user-priority' | 'log-priority') => void;
}

export default function DiagnosisModeToggle({
  value,
  onChange,
}: DiagnosisModeToggleProps) {
  const { t } = useTranslation();
  const handleChange = (e: RadioChangeEvent) => {
    onChange(e.target.value);
  };

  return (
    <div style={{ marginBottom: 16 }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <div style={{ fontSize: 12, color: '#888' }}>{t('diagnosis.diagnosisPriorityMode')}</div>
        <Radio.Group
          value={value}
          onChange={handleChange}
          optionType="button"
          buttonStyle="solid"
        >
          <Radio.Button value="user-priority">
            {t('diagnosis.userInputPriority')}
          </Radio.Button>
          <Radio.Button value="log-priority">
            {t('diagnosis.logPriority')}
          </Radio.Button>
        </Radio.Group>
        <div style={{ fontSize: 12, color: '#666' }}>
          {value === 'user-priority'
            ? t('diagnosis.userInputPriorityDesc')
            : t('diagnosis.logPriorityDesc')}
        </div>
      </Space>
    </div>
  );
}
