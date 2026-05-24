import { Progress, Card, Typography } from 'antd';

const { Text } = Typography;

interface ClusterProgressProps {
  status: string;
  progress: number;
  currentStep: string;
}

const STATUS_STEPS: Record<string, { percent: number; label: string }> = {
  scanning: { percent: 20, label: '扫描日志中...' },
  aggregating: { percent: 50, label: '异常聚类中...' },
  matching: { percent: 80, label: '历史案例匹配中...' },
  done: { percent: 100, label: '分析完成' },
};

export default function ClusterProgress({ status, progress, currentStep }: ClusterProgressProps) {
  const stepInfo = STATUS_STEPS[status] || { percent: progress, label: currentStep };

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
          <Text strong>{stepInfo.label}</Text>
          <br />
          <Text type="secondary">{currentStep}</Text>
        </div>
      </div>
    </Card>
  );
}