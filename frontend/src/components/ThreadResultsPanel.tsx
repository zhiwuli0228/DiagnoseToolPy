import { useEffect, useState } from 'react';
import { Card, Table, Tag, Space, Button, Checkbox, Spin } from 'antd';
import { useTranslation } from 'react-i18next';
import { getThreadResults } from '../api/diagnosisApi';
import type { SelectionItem, ThreadResultItem, ThreadResultsResponse } from '../types/api';
import { useDiagnosis } from '../context/DiagnosisContext';

interface ThreadResultsPanelProps {
  taskId: string;
}

function ThreadResultsPanel({ taskId }: ThreadResultsPanelProps) {
  const { t } = useTranslation();
  const { selections, setSelections } = useDiagnosis();
  const [results, setResults] = useState<ThreadResultsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!taskId) {
      setResults(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    getThreadResults(taskId)
      .then(data => {
        if (!cancelled) setResults(data);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setError(axiosError.response?.data?.detail || 'Failed to load thread results');
        setResults(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [taskId]);

  const isSelected = (threadRef: string) =>
    selections.some(s => s.type === 'thread' && s.id === threadRef);

  const toggleSelection = (threadRef: string) => {
    setSelections(prev => {
      const exists = prev.some(s => s.type === 'thread' && s.id === threadRef);
      if (exists) {
        return prev.filter(s => !(s.type === 'thread' && s.id === threadRef));
      }
      const sel: SelectionItem = { type: 'thread', id: threadRef };
      return [...prev, sel];
    });
  };

  const addAllThreads = () => {
    if (!results) return;
    setSelections(prev => {
      const existingIds = new Set(prev.filter(s => s.type === 'thread').map(s => s.id));
      const toAdd: SelectionItem[] = results.threads
        .map(t => ({ type: 'thread' as const, id: t.thread_ref }))
        .filter(s => !existingIds.has(s.id));
      return [...prev, ...toAdd];
    });
  };

  if (loading) {
    return (
      <Card size="small" style={{ marginTop: 16 }}>
        <Spin size="small" /> {t('analysisTasks.loadingThreadResults', 'Loading thread results...')}
      </Card>
    );
  }

  if (error) {
    return (
      <Card size="small" style={{ marginTop: 16 }}>
        <span style={{ color: '#cf1322' }}>{error}</span>
      </Card>
    );
  }

  if (!results || results.total_threads === 0) {
    return (
      <Card size="small" style={{ marginTop: 16 }} title={t('analysisTasks.threadResults', 'Thread Stack Results')}>
        <span style={{ color: '#999' }}>
          {t('analysisTasks.noThreadResultsFound', 'No thread results found for this task.')}
        </span>
      </Card>
    );
  }

  const allSelected = results.threads.every(t => isSelected(t.thread_ref));

  return (
    <Card
      title={
        <Space>
          <span>{t('analysisTasks.threadResults', 'Thread Stack Results')}</span>
          <Tag>{results.total_threads} {t('analysisTasks.threads', 'threads')}</Tag>
          {results.status_counts.FULL && <Tag color="green">FULL {results.status_counts.FULL}</Tag>}
          {results.status_counts.PARTIAL && <Tag color="orange">PARTIAL {results.status_counts.PARTIAL}</Tag>}
        </Space>
      }
      size="small"
      style={{ marginTop: 16 }}
      extra={
        <Button size="small" onClick={addAllThreads} disabled={allSelected}>
          {t('analysisTasks.addAllThreads', 'Add All')}
        </Button>
      }
    >
      <Table
        dataSource={results.threads}
        rowKey="thread_ref"
        size="small"
        pagination={results.threads.length > 20 ? { pageSize: 20 } : false}
        columns={[
          {
            title: '',
            width: 40,
            render: (_: unknown, record: ThreadResultItem) => (
              <Checkbox
                checked={isSelected(record.thread_ref)}
                onChange={() => toggleSelection(record.thread_ref)}
              />
            ),
          },
          {
            title: t('analysisTasks.threadName', 'Thread Name'),
            dataIndex: 'thread_name',
            render: (name: string | null) => name || <span style={{ color: '#999' }}>(unnamed)</span>,
          },
          {
            title: t('analysisTasks.threadState', 'State'),
            dataIndex: 'thread_state',
            width: 140,
            render: (state: string | null) => {
              const colorMap: Record<string, string> = {
                RUNNABLE: 'green', BLOCKED: 'red', WAITING: 'blue', TIMED_WAITING: 'cyan',
              };
              return state ? <Tag color={colorMap[state] || 'default'}>{state}</Tag> : '-';
            },
          },
          {
            title: t('analysisTasks.parseStatus', 'Parse'),
            dataIndex: 'parse_status',
            width: 90,
            render: (status: string) => {
              const colorMap: Record<string, string> = { FULL: 'green', PARTIAL: 'orange', RAW: 'red' };
              return <Tag color={colorMap[status] || 'default'}>{status}</Tag>;
            },
          },
          {
            title: t('analysisTasks.frames', 'Frames'),
            dataIndex: 'frame_count',
            width: 70,
          },
        ]}
      />
    </Card>
  );
}

export default ThreadResultsPanel;
