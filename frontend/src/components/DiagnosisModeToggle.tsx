import { Radio, Space } from 'antd';
import type { RadioChangeEvent } from 'antd';

interface DiagnosisModeToggleProps {
  value: 'user-priority' | 'log-priority';
  onChange: (mode: 'user-priority' | 'log-priority') => void;
}

export default function DiagnosisModeToggle({
  value,
  onChange,
}: DiagnosisModeToggleProps) {
  const handleChange = (e: RadioChangeEvent) => {
    onChange(e.target.value);
  };

  return (
    <div style={{ marginBottom: 16 }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <div style={{ fontSize: 12, color: '#888' }}>诊断优先级模式</div>
        <Radio.Group
          value={value}
          onChange={handleChange}
          optionType="button"
          buttonStyle="solid"
        >
          <Radio.Button value="user-priority">
            用户输入优先
          </Radio.Button>
          <Radio.Button value="log-priority">
            日志优先
          </Radio.Button>
        </Radio.Group>
        <div style={{ fontSize: 12, color: '#666' }}>
          {value === 'user-priority'
            ? '以用户描述为主，日志作为补充参考'
            : '以日志分析为主，用户描述作为补充'}
        </div>
      </Space>
    </div>
  );
}
