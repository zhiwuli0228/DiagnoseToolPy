import { useEffect, useState } from 'react';
import { Card, Table, Tag, Button } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getTasks, type TaskSummary } from '../api/taskApi';

function TaskHistoryTable() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTasks();
      setTasks(data);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || t('analysisTasks.taskTable.loadError', 'Failed to load tasks'));
      setTasks([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const statusColor = (status: string | null) => {
    if (!status) return 'default';
    if (status === 'done' || status === 'completed') return 'green';
    if (status === 'failed' || status === 'error') return 'red';
    if (status === 'scanning' || status === 'in_progress') return 'blue';
    return 'default';
  };

  return (
    <Card
      title={t('analysisTasks.taskTable.title', 'Historical Tasks')}
      size="small"
      style={{ marginTop: 24 }}
      extra={
        <Button size="small" icon={<ReloadOutlined />} onClick={load} loading={loading}>
          {t('analysisTasks.taskTable.refresh', 'Refresh')}
        </Button>
      }
    >
      {error && (
        <div style={{ marginBottom: 8, color: '#cf1322' }}>
          {error}
          <Button size="small" type="link" onClick={load}>
            {t('analysisTasks.taskTable.retry', 'Retry')}
          </Button>
        </div>
      )}
      <Table
        dataSource={tasks}
        rowKey="task_id"
        size="small"
        loading={loading}
        pagination={tasks.length > 20 ? { pageSize: 20 } : false}
        locale={{
          emptyText: t('analysisTasks.taskTable.empty', 'No historical tasks'),
        }}
        onRow={(record) => ({
          onClick: () => navigate(`/analysis/${record.task_id}`),
          style: { cursor: 'pointer' },
        })}
        columns={[
          {
            title: t('analysisTasks.taskTable.taskId', 'Task ID'),
            dataIndex: 'task_id',
            width: 240,
            ellipsis: true,
          },
          {
            title: t('analysisTasks.taskTable.status', 'Status'),
            dataIndex: 'status',
            width: 110,
            render: (status: string | null) => (
              <Tag color={statusColor(status)}>{status || '-'}</Tag>
            ),
          },
          {
            title: t('analysisTasks.taskTable.progress', 'Progress'),
            dataIndex: 'progress',
            width: 100,
            render: (progress: Record<string, unknown>) => {
              const p = progress?.progress;
              return typeof p === 'number' ? `${p}%` : '-';
            },
          },
          {
            title: t('analysisTasks.taskTable.currentStep', 'Current Step'),
            dataIndex: 'progress',
            render: (progress: Record<string, unknown>) => {
              const step = progress?.current_step;
              return typeof step === 'string' ? step : '-';
            },
          },
          {
            title: t('analysisTasks.taskTable.updatedAt', 'Updated'),
            dataIndex: 'progress',
            width: 180,
            render: (progress: Record<string, unknown>) => {
              const ts = progress?.updated_at;
              return typeof ts === 'string' ? ts : '-';
            },
          },
        ]}
      />
    </Card>
  );
}

export default TaskHistoryTable;
