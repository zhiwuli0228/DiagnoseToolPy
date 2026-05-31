import { Button, Space } from 'antd';
import {
  SendOutlined,
  ForwardOutlined,
  StopOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

interface DiagnosisActionBarProps {
  onContinue?: () => void;
  onSkip?: () => void;
  onEnd?: () => void;
  showContinue?: boolean;
  showSkip?: boolean;
  showEnd?: boolean;
  loading?: boolean;
  disabled?: boolean;
}

export default function DiagnosisActionBar({
  onContinue,
  onSkip,
  onEnd,
  showContinue = true,
  showSkip = true,
  showEnd = true,
  loading = false,
  disabled = false,
}: DiagnosisActionBarProps) {
  const { t } = useTranslation();
  return (
    <Space style={{ marginTop: 16 }}>
      {showContinue && onContinue && (
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={onContinue}
          loading={loading}
          disabled={disabled}
        >
          {t('conversation.sendReply')}
        </Button>
      )}
      {showSkip && onSkip && (
        <Button
          icon={<ForwardOutlined />}
          onClick={onSkip}
          disabled={disabled || loading}
        >
          {t('conversation.skipQuestion')}
        </Button>
      )}
      {showEnd && onEnd && (
        <Button
          danger
          icon={<StopOutlined />}
          onClick={onEnd}
          disabled={loading}
        >
          {t('conversation.endDiagnosis')}
        </Button>
      )}
    </Space>
  );
}
