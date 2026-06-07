import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Tabs, Card, Button, Space, Modal, message, Alert, Spin } from 'antd';
import { useTranslation } from 'react-i18next';
import { getTaskProgress, getTaskEvidencePack, getTaskKeyLogs, getTaskCaseDraft } from '../api/taskApi';
import { exportWorkspace, previewPrompt } from '../api/diagnosisApi';
import { deleteTempDir } from '../api/sourceApi';
import { useDiagnosis } from '../context/DiagnosisContext';
import TaskOverview from '../components/TaskOverview';
import ThreadResultsPanel from '../components/ThreadResultsPanel';
import KeyLogsList from '../components/KeyLogsList';
import type { SelectionItem } from '../types/api';

type LoadState<T> = { status: 'loading' } | { status: 'ok'; data: T } | { status: 'error'; error: string };

function usePromise<T>(promiseFactory: () => Promise<T>, deps: unknown[], enabled = true): LoadState<T> {
  const [state, setState] = useState<LoadState<T>>({ status: 'loading' });
  useEffect(() => {
    if (!enabled) {
      setState({ status: 'loading' });
      return;
    }
    let cancelled = false;
    setState({ status: 'loading' });
    promiseFactory()
      .then(data => {
        if (!cancelled) setState({ status: 'ok', data });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setState({
          status: 'error',
          error: axiosError.response?.data?.detail || 'Request failed',
        });
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return state;
}

function TaskDetailPage() {
  const { t } = useTranslation();
  const location = useLocation();
  // The app's router does not use <Route> elements, so useParams() is empty.
  // Parse the taskId from the URL manually: /analysis/:taskId
  const taskId = location.pathname.startsWith('/analysis/')
    ? decodeURIComponent(location.pathname.slice('/analysis/'.length))
    : '';
  const navigate = useNavigate();
  const { selections, setSelections } = useDiagnosis();
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [exporting, setExporting] = useState(false);

  const progressState = usePromise(() => getTaskProgress(taskId), [taskId], Boolean(taskId));
  const evidenceState = usePromise(() => getTaskEvidencePack(taskId), [taskId], Boolean(taskId));
  const keyLogsState = usePromise(() => getTaskKeyLogs(taskId), [taskId], Boolean(taskId));
  const caseDraftState = usePromise(() => getTaskCaseDraft(taskId), [taskId], Boolean(taskId));

  const startDiagnosis = async () => {
    // Pre-seed the basket with the current task's threads (if any) and key-logs.
    const seed: SelectionItem[] = [];
    if (keyLogsState.status === 'ok' && keyLogsState.data) {
      seed.push({ type: 'log', id: `key-logs:${taskId}`, group_key: `key-logs:${taskId}` });
    }
    if (seed.length > 0) {
      setSelections(prev => {
        const existing = new Set(prev.map(s => `${s.type}:${s.id}`));
        const unique = seed.filter(s => !existing.has(`${s.type}:${s.id}`));
        return [...prev, ...unique];
      });
    }
    try {
      const result = await previewPrompt({
        task_id: taskId,
        user_context: { phenomenon: '', stack: '', params: '' },
        selections: selections,
      });
      // Show a small modal with the generated prompt; this is the same flow
      // the Analysis page uses.
      Modal.info({
        title: t('taskDetail.actions.startDiagnosis.previewTitle', 'Diagnosis Prompt Preview'),
        width: 720,
        content: (
          <pre
            style={{
              whiteSpace: 'pre-wrap',
              maxHeight: 480,
              overflow: 'auto',
              fontSize: 12,
            }}
          >
            {result.prompt}
          </pre>
        ),
      });
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      message.error(axiosError.response?.data?.detail || 'Failed to start diagnosis');
    }
  };

  const doExport = async () => {
    setExporting(true);
    try {
      const res = await exportWorkspace({
        task_id: taskId,
        workspace_dir: 'exports',
        user_context: { phenomenon: '', stack: '', params: '' },
        selections: selections,
      });
      message.success(t('taskDetail.actions.export.success', 'Workspace exported'));
      Modal.info({
        title: t('taskDetail.actions.export.title', 'Export Workspace'),
        content: (
          <div>
            <p>{t('taskDetail.actions.export.path', 'Path')}: {res.workspace_dir}</p>
          </div>
        ),
      });
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      message.error(axiosError.response?.data?.detail || 'Export failed');
    } finally {
      setExporting(false);
    }
  };

  const confirmDelete = async () => {
    try {
      await deleteTempDir(taskId);
      message.success(t('taskDetail.actions.delete.success', 'Task deleted'));
      setDeleteOpen(false);
      navigate('/analysis');
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      message.error(axiosError.response?.data?.detail || 'Delete failed');
    }
  };

  const progress = progressState.status === 'ok' ? progressState.data : null;
  const evidence = evidenceState.status === 'ok' ? evidenceState.data : null;
  const keyLogs = keyLogsState.status === 'ok' ? keyLogsState.data : null;
  const caseDraft = caseDraftState.status === 'ok' ? caseDraftState.data : null;

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button onClick={() => navigate('/analysis')}>
          {t('taskDetail.back', 'Back to Analysis')}
        </Button>
        <h2 style={{ margin: 0 }}>
          {t('taskDetail.title', 'Task Detail')}: <code>{taskId}</code>
        </h2>
      </Space>

      <Card>
        <Tabs
          defaultActiveKey="overview"
          items={[
            {
              key: 'overview',
              label: t('taskDetail.tabs.overview', 'Overview'),
              children: (
                <TaskOverview taskId={taskId} progress={progress} />
              ),
            },
            {
              key: 'evidence',
              label: t('taskDetail.tabs.evidence', 'Evidence & Threads'),
              children: (
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Card
                    size="small"
                    title={t('taskDetail.evidence.title', 'Evidence Pack')}
                  >
                    {evidenceState.status === 'loading' && <Spin />}
                    {evidenceState.status === 'error' && (
                      <Alert type="error" message={evidenceState.error} />
                    )}
                    {evidenceState.status === 'ok' && !evidence && (
                      <Alert
                        type="info"
                        showIcon
                        message={t('taskDetail.evidence.notProduced', 'No evidence pack produced for this task.')}
                      />
                    )}
                    {evidenceState.status === 'ok' && evidence && (
                      <pre
                        data-testid="evidence-pack-pre"
                        style={{
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                          background: '#fafafa',
                          border: '1px solid #f0f0f0',
                          padding: 12,
                          maxHeight: 400,
                          overflow: 'auto',
                          fontSize: 12,
                        }}
                      >
                        {evidence}
                      </pre>
                    )}
                  </Card>
                  <ThreadResultsPanel taskId={taskId} />
                </Space>
              ),
            },
            {
              key: 'keylogs',
              label: t('taskDetail.tabs.keyLogs', 'Key Logs & Case Draft'),
              children: (
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Card size="small" title={t('taskDetail.keyLogs.title', 'Key Logs')}>
                    {keyLogsState.status === 'loading' && <Spin />}
                    {keyLogsState.status === 'error' && (
                      <Alert type="error" message={keyLogsState.error} />
                    )}
                    {keyLogsState.status === 'ok' && (
                      <KeyLogsList taskId={taskId} content={keyLogs} />
                    )}
                  </Card>
                  <Card size="small" title={t('taskDetail.caseDraft.title', 'Case Draft')}>
                    {caseDraftState.status === 'loading' && <Spin />}
                    {caseDraftState.status === 'error' && (
                      <Alert type="error" message={caseDraftState.error} />
                    )}
                    {caseDraftState.status === 'ok' && !caseDraft && (
                      <Alert
                        type="info"
                        showIcon
                        message={t('taskDetail.caseDraft.notProduced', 'No case draft produced for this task.')}
                      />
                    )}
                    {caseDraftState.status === 'ok' && caseDraft && (
                      <pre
                        data-testid="case-draft-pre"
                        style={{
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                          background: '#fafafa',
                          border: '1px solid #f0f0f0',
                          padding: 12,
                          maxHeight: 400,
                          overflow: 'auto',
                          fontSize: 12,
                        }}
                      >
                        {caseDraft}
                      </pre>
                    )}
                  </Card>
                </Space>
              ),
            },
            {
              key: 'actions',
              label: t('taskDetail.tabs.actions', 'Actions'),
              children: (
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Button type="primary" onClick={startDiagnosis} data-testid="action-start-diagnosis">
                    {t('taskDetail.actions.startDiagnosis.label', 'Start diagnosis')}
                  </Button>
                  <Button onClick={doExport} loading={exporting} data-testid="action-export-workspace">
                    {t('taskDetail.actions.export.label', 'Export workspace')}
                  </Button>
                  <Button onClick={() => navigate('/analysis')} data-testid="action-rerun-scan">
                    {t('taskDetail.actions.rerun.label', 'Re-run scan')}
                  </Button>
                  <Button danger onClick={() => setDeleteOpen(true)} data-testid="action-delete">
                    {t('taskDetail.actions.delete.label', 'Delete task')}
                  </Button>
                </Space>
              ),
            },
          ]}
        />
      </Card>

      <Modal
        title={t('taskDetail.actions.delete.confirmTitle', 'Delete task?')}
        open={deleteOpen}
        onCancel={() => setDeleteOpen(false)}
        onOk={confirmDelete}
        okText={t('taskDetail.actions.delete.confirmOk', 'Delete')}
        cancelText={t('common.cancel', 'Cancel')}
        okButtonProps={{ danger: true }}
      >
        <p>
          {t('taskDetail.actions.delete.confirmBody', 'This will remove the temporary directory for task {id}.').replace('{id}', taskId)}
        </p>
      </Modal>
    </div>
  );
}

export default TaskDetailPage;
