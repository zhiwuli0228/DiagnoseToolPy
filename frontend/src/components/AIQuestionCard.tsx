import { Card, Button, Space, Typography } from 'antd';
import { CommentOutlined, ForwardOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

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
  const { t } = useTranslation();
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
          <span>{t('aiQuestion.title')}</span>
        </Space>
      }
      extra={
        showSkip && onSkip && (
          <Button
            size="small"
            icon={<ForwardOutlined />}
            onClick={onSkip}
          >
            {t('aiQuestion.skipAndDiagnose')}
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
