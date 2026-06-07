import { useState } from 'react';
import { Button, Space, Alert } from 'antd';
import { useTranslation } from 'react-i18next';
import { useDiagnosis } from '../context/DiagnosisContext';
import type { SelectionItem } from '../types/api';

interface KeyLogsListProps {
  taskId: string;
  content: string | null;
}

function KeyLogsList({ taskId, content }: KeyLogsListProps) {
  const { t } = useTranslation();
  const { setSelections } = useDiagnosis();
  const [added, setAdded] = useState(false);

  if (!content) {
    return (
      <Alert
        type="info"
        showIcon
        message={t('taskDetail.keyLogs.empty', 'No key logs in this task.')}
      />
    );
  }

  const lines = content.split('\n').filter(line => line.trim().length > 0);
  const firstLinePreview = lines[0] || '';

  const addAll = () => {
    const sel: SelectionItem = {
      type: 'log',
      id: `key-logs:${taskId}`,
      group_key: `key-logs:${taskId}`,
    };
    setSelections(prev => {
      const exists = prev.some(
        s => s.type === 'log' && s.group_key === `key-logs:${taskId}`,
      );
      if (exists) return prev;
      return [...prev, sel];
    });
    setAdded(true);
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Space>
        <Button onClick={addAll} disabled={added}>
          {added
            ? t('taskDetail.keyLogs.added', 'Added to evidence basket')
            : t('taskDetail.keyLogs.addAll', 'Add all to evidence basket')}
        </Button>
        <span style={{ color: '#999' }}>
          {t('taskDetail.keyLogs.lineCount', '{n} lines').replace('{n}', String(lines.length))}
        </span>
      </Space>
      <pre
        data-testid="key-logs-pre"
        style={{
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          background: '#fafafa',
          border: '1px solid #f0f0f0',
          padding: 12,
          maxHeight: 400,
          overflow: 'auto',
          fontSize: 12,
          fontFamily: 'monospace',
        }}
      >
        {content}
      </pre>
      <span style={{ color: '#999', fontSize: 12 }}>
        {t('taskDetail.keyLogs.preview', 'First line: ')}
        {firstLinePreview.slice(0, 120)}
      </span>
    </Space>
  );
}

export default KeyLogsList;
