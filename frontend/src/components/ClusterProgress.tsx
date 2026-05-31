import { Progress, Card, Typography } from 'antd';
import { useTranslation } from 'react-i18next';

const { Text } = Typography;

interface ClusterProgressProps {
  status: string;
  progress: number;
  currentStep: string;
}

const STATUS_STEPS: Record<string, { percent: number; labelKey: string }> = {
  scanning: { percent: 20, labelKey: 'clusterProgress.scanning' },
  aggregating: { percent: 50, labelKey: 'clusterProgress.aggregating' },
  matching: { percent: 80, labelKey: 'clusterProgress.matching' },
  done: { percent: 100, labelKey: 'clusterProgress.done' },
};

export default function ClusterProgress({ status, progress, currentStep }: ClusterProgressProps) {
  const { t } = useTranslation();
  const stepInfo = STATUS_STEPS[status] || { percent: progress, labelKey: currentStep };

  return (
    <Card size="small" style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <Progress
          type="circle"
          percent={stepInfo.percent}
          size={60}
          status={status === 'done' ? 'success' : 'active'}
        />
        <div>
          <Text strong>{t(stepInfo.labelKey)}</Text>
          <br />
          <Text type="secondary">{currentStep}</Text>
        </div>
      </div>
    </Card>
  );
}