import { Card, Typography, Space, Timeline, Input } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { ConversationTurn } from '../types/api';
import AIQuestionCard from './AIQuestionCard';
import DiagnosisActionBar from './DiagnosisActionBar';

const { Text } = Typography;
const { TextArea } = Input;

interface ConversationThreadProps {
  turns: ConversationTurn[];
  currentQuestion?: string | null;
  onContinue?: (reply: string) => void;
  onSkip?: () => void;
  onEnd?: () => void;
  loading?: boolean;
}

export default function ConversationThread({
  turns,
  currentQuestion,
  onContinue,
  onSkip,
  onEnd,
  loading = false,
}: ConversationThreadProps) {
  const [replyText, setReplyText] = useState('');

  const handleSendReply = () => {
    if (replyText.trim() && onContinue) {
      onContinue(replyText);
      setReplyText('');
    }
  };

  const renderUserContext = (ctx: { phenomenon?: string; stack?: string; params?: string }) => {
    const parts = [];
    if (ctx.phenomenon) {
      parts.push(
        <div key="phenomenon">
          <Text strong>## 现象</Text>
          <div style={{ marginLeft: 8, marginBottom: 8 }}>{ctx.phenomenon}</div>
        </div>
      );
    }
    if (ctx.stack) {
      parts.push(
        <div key="stack">
          <Text strong>## 堆栈</Text>
          <pre style={{ marginLeft: 8, marginBottom: 8, fontSize: 12, background: '#f5f5f5', padding: 8, borderRadius: 4 }}>
            {ctx.stack}
          </pre>
        </div>
      );
    }
    if (ctx.params) {
      parts.push(
        <div key="params">
          <Text strong>## 入参</Text>
          <div style={{ marginLeft: 8, marginBottom: 8, fontSize: 12 }}>{ctx.params}</div>
        </div>
      );
    }
    return parts;
  };

  return (
    <Card
      title={
        <Space>
          <RobotOutlined />
          <span>诊断对话</span>
        </Space>
      }
      size="small"
    >
      {turns.length === 0 && !currentQuestion ? (
        <div style={{ textAlign: 'center', color: '#888', padding: 24 }}>
          输入问题描述和选择日志证据后，点击"开始诊断"发起对话
        </div>
      ) : (
        <>
          <Timeline style={{ marginBottom: 16 }}>
            {turns.map((turn) => (
              <Timeline.Item key={turn.turn_id}>
                {/* User Input */}
                <Card
                  size="small"
                  style={{ marginBottom: 8, background: '#e6f7ff', borderColor: '#91d5ff' }}
                >
                  <Space>
                    <UserOutlined />
                    <Text type="secondary">用户</Text>
                  </Space>
                  <div style={{ marginTop: 8 }}>
                    {renderUserContext(turn.user_context)}
                  </div>
                </Card>

                {/* AI Question (if any) */}
                {turn.ai_question && (
                  <AIQuestionCard question={turn.ai_question} showSkip={false} />
                )}

                {/* AI Diagnosis (if any) */}
                {turn.ai_diagnosis && (
                  <Card
                    size="small"
                    style={{ marginTop: 8, background: '#fff7e6', borderColor: '#ffd591' }}
                  >
                    <Space>
                      <RobotOutlined />
                      <Text type="secondary">AI 诊断</Text>
                    </Space>
                    <div
                      style={{
                        marginTop: 8,
                        whiteSpace: 'pre-wrap',
                        lineHeight: 1.8,
                      }}
                    >
                      <Text>{turn.ai_diagnosis}</Text>
                    </div>
                  </Card>
                )}
              </Timeline.Item>
            ))}
          </Timeline>

          {/* Current Question (awaiting reply) */}
          {currentQuestion && (
            <>
              <AIQuestionCard
                question={currentQuestion}
                onSkip={onSkip}
                showSkip={true}
              />
              <div style={{ marginTop: 16 }}>
                <TextArea
                  placeholder="输入您的回复..."
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  rows={3}
                  autoSize={{ minRows: 2, maxRows: 6 }}
                  onPressEnter={(e) => {
                    if (e.shiftKey) return;
                    e.preventDefault();
                    handleSendReply();
                  }}
                />
                <DiagnosisActionBar
                  onContinue={handleSendReply}
                  onSkip={onSkip}
                  onEnd={onEnd}
                  showSkip={true}
                  loading={loading}
                  disabled={!replyText.trim()}
                />
              </div>
            </>
          )}
        </>
      )}
    </Card>
  );
}
