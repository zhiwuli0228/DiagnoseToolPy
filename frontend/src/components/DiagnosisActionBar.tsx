import { Button, Space } from 'antd';
import {
  SendOutlined,
  ForwardOutlined,
  StopOutlined,
} from '@ant-design/icons';

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
          发送回复
        </Button>
      )}
      {showSkip && onSkip && (
        <Button
          icon={<ForwardOutlined />}
          onClick={onSkip}
          disabled={disabled || loading}
        >
          跳过追问
        </Button>
      )}
      {showEnd && onEnd && (
        <Button
          danger
          icon={<StopOutlined />}
          onClick={onEnd}
          disabled={loading}
        >
          结束诊断
        </Button>
      )}
    </Space>
  );
}
