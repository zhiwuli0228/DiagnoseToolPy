import { Card, Input, Typography, Alert, Space } from 'antd';
import { useState } from 'react';

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
        return '描述问题的具体表现，例如：\n- 服务偶发超时，错误率约 2%\n- 订单接口响应时间从 100ms 增长到 5000ms\n- 凌晨 3 点出现大量 GC 日志';
      case 'stack':
        return '粘贴异常堆栈信息（可选），例如：\nat com.demo.OrderService.query(OrderService.java:42)\nat com.demo.OrderController.get(OrderController.java:30)';
      case 'params':
        return '提供关键入参信息（可选），例如：\norderId=12345\nuserId=789\nproductId=SKU-001';
      default:
        return '';
    }
  };

  return (
    <Card title="问题描述" size="small">
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        <div>
          <Title level={5} style={{ marginBottom: 8 }}>## 现象</Title>
          <TextArea
            placeholder={getPlaceholder('phenomenon')}
            value={value.phenomenon}
            onChange={handlePhenomenonChange}
            rows={3}
            autoSize={{ minRows: 2, maxRows: 6 }}
          />
        </div>

        <div>
          <Title level={5} style={{ marginBottom: 8 }}>## 堆栈（可选）</Title>
          <TextArea
            placeholder={getPlaceholder('stack')}
            value={value.stack}
            onChange={handleStackChange}
            rows={5}
            autoSize={{ minRows: 3, maxRows: 10 }}
          />
          {stackLines > 30 && (
            <Alert
              message="检测到较长堆栈，系统将自动精简以节省 token"
              type="info"
              showIcon
              style={{ marginTop: 8 }}
            />
          )}
        </div>

        <div>
          <Title level={5} style={{ marginBottom: 8 }}>## 入参（可选）</Title>
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
