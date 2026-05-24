import { Card, Button, Space, Typography } from 'antd';
import { CommentOutlined, ForwardOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface AIQuestionCardProps {
  question: string;
  onSkip?: () => void;
  showSkip?: boolean;
}

export default function AIQuestionCard({
  question,
  onSkip,
  showSkip = true,
}: AIQuestionCardProps) {
  return (
    <Card
      size="small"
      style={{
        background: '#f6ffed',
        borderColor: '#b7eb8f',
      }}
      title={
        <Space>
          <CommentOutlined />
          <span>AI 追问</span>
        </Space>
      }
      extra={
        showSkip && onSkip && (
          <Button
            size="small"
            icon={<ForwardOutlined />}
            onClick={onSkip}
          >
            跳过，直接诊断
          </Button>
        )
      }
    >
      <div
        style={{
          whiteSpace: 'pre-wrap',
          lineHeight: 1.8,
        }}
      >
        <Text>{question}</Text>
      </div>
    </Card>
  );
}
