import { Card, Input, Typography, Alert, Space } from 'antd';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

const { TextArea } = Input;
const { Title } = Typography;

interface UserContextInputProps {
  value: {
    phenomenon: string;
    stack: string;
    params: string;
  };
  onChange: (value: { phenomenon: string; stack: string; params: string }) => void;
  onStackLong?: (isLong: boolean) => void;
}

export default function UserContextInput({
  value,
  onChange,
  onStackLong,
}: UserContextInputProps) {
  const { t } = useTranslation();
  const [stackLines, setStackLines] = useState(0);

  const handlePhenomenonChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange({ ...value, phenomenon: e.target.value });
  };

  const handleStackChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    const lines = text.split('\n').length;
    setStackLines(lines);
    onChange({ ...value, stack: text });
    if (onStackLong) {
      onStackLong(lines > 30);
    }
  };

  const handleParamsChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange({ ...value, params: e.target.value });
  };

  const getPlaceholder = (type: string) => {
    switch (type) {
      case 'phenomenon':
        return t('diagnosis.problemPhenomenonPlaceholder');
      case 'stack':
        return t('diagnosis.stackInfoPlaceholder');
      case 'params':
        return t('diagnosis.keyParamsPlaceholder');
      default:
        return '';
    }
  };

  return (
    <Card title={t('diagnosis.problemPhenomenon')} size="small">
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        <div>
          <Title level={5} style={{ marginBottom: 8 }}>## {t('userContext.phenomenon')}</Title>
          <TextArea
            placeholder={getPlaceholder('phenomenon')}
            value={value.phenomenon}
            onChange={handlePhenomenonChange}
            rows={3}
            autoSize={{ minRows: 2, maxRows: 6 }}
          />
        </div>

        <div>
          <Title level={5} style={{ marginBottom: 8 }}>## {t('userContext.stackOptional')}</Title>
          <TextArea
            placeholder={getPlaceholder('stack')}
            value={value.stack}
            onChange={handleStackChange}
            rows={5}
            autoSize={{ minRows: 3, maxRows: 10 }}
          />
          {stackLines > 30 && (
            <Alert
              message={t('userContext.longStackAlert')}
              type="info"
              showIcon
              style={{ marginTop: 8 }}
            />
          )}
        </div>

        <div>
          <Title level={5} style={{ marginBottom: 8 }}>## {t('userContext.paramsOptional')}</Title>
          <TextArea
            placeholder={getPlaceholder('params')}
            value={value.params}
            onChange={handleParamsChange}
            rows={2}
            autoSize={{ minRows: 1, maxRows: 4 }}
          />
        </div>
      </Space>
    </Card>
  );
}
