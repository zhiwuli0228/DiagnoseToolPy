import { Tag, Progress, Descriptions } from 'antd';
import { useTranslation } from 'react-i18next';

interface TaskOverviewProps {
  taskId: string;
  progress: Record<string, unknown> | null;
}

const STATUS_COLORS: Record<string, string> = {
  done: 'green',
  completed: 'green',
  failed: 'red',
  error: 'red',
  scanning: 'blue',
  in_progress: 'blue',
  pending: 'default',
};

function TaskOverview({ taskId, progress }: TaskOverviewProps) {
  const { t } = useTranslation();
  if (!progress) {
    return (
      <div style={{ color: '#999' }}>
        {t('taskDetail.overview.notProduced', 'No progress recorded for this task.')}
      </div>
    );
  }
  const status = typeof progress.status === 'string' ? progress.status : null;
  const step = typeof progress.current_step === 'string' ? progress.current_step : null;
  const updated = typeof progress.updated_at === 'string' ? progress.updated_at : null;
  const pct = typeof progress.progress === 'number' ? progress.progress : null;
  const started = typeof progress.started_at === 'string' ? progress.started_at : null;
  const finished = typeof progress.finished_at === 'string' ? progress.finished_at : null;
  const failure = typeof progress.failure_message === 'string' ? progress.failure_message : null;

  return (
    <Descriptions
      bordered
      size="small"
      column={1}
      title={t('taskDetail.overview.title', 'Task Overview')}
    >
      <Descriptions.Item label={t('taskDetail.overview.taskId', 'Task ID')}>
        <code>{taskId}</code>
      </Descriptions.Item>
      <Descriptions.Item label={t('taskDetail.overview.status', 'Status')}>
        <Tag color={STATUS_COLORS[status || ''] || 'default'}>{status || '-'}</Tag>
      </Descriptions.Item>
      {pct !== null && (
        <Descriptions.Item label={t('taskDetail.overview.progress', 'Progress')}>
          <Progress percent={pct} size="small" />
        </Descriptions.Item>
      )}
      {step && (
        <Descriptions.Item label={t('taskDetail.overview.currentStep', 'Current Step')}>
          {step}
        </Descriptions.Item>
      )}
      {updated && (
        <Descriptions.Item label={t('taskDetail.overview.updatedAt', 'Updated At')}>
          {updated}
        </Descriptions.Item>
      )}
      {started && (
        <Descriptions.Item label={t('taskDetail.overview.startedAt', 'Started At')}>
          {started}
        </Descriptions.Item>
      )}
      {finished && (
        <Descriptions.Item label={t('taskDetail.overview.finishedAt', 'Finished At')}>
          {finished}
        </Descriptions.Item>
      )}
      {failure && (
        <Descriptions.Item label={t('taskDetail.overview.failure', 'Failure')}>
          <span style={{ color: '#cf1322' }}>{failure}</span>
        </Descriptions.Item>
      )}
    </Descriptions>
  );
}

export default TaskOverview;
