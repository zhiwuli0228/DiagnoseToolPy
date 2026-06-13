import { useEffect, useState } from 'react';
import { Card, Alert, Spin, Tag, Space, Button, message } from 'antd';
import { useTranslation } from 'react-i18next';
import { getTaskMonitorSuggestions } from '../api/taskApi';

interface MonitorSuggestionsPanelProps {
  taskId: string;
  refreshKey?: number;
}

interface ParsedMonitor {
  name: string;
  type: string | null;
  target: string | null;
  condition: string | null;
  action: string | null;
}

function parseMonitorSuggestions(content: string): { section: string; monitors: ParsedMonitor[] }[] {
  if (!content.trim()) return [];
  const lines = content.split('\n');
  const sections: { section: string; monitors: ParsedMonitor[] }[] = [];
  let currentSection = '';
  let currentMonitor: ParsedMonitor | null = null;

  const flush = () => {
    if (currentMonitor) {
      sections[sections.length - 1].monitors.push(currentMonitor);
    }
    currentMonitor = null;
  };

  for (const line of lines) {
    const sectionMatch = line.match(/^##\s+(.+)$/);
    if (sectionMatch) {
      flush();
      currentSection = sectionMatch[1].trim();
      sections.push({ section: currentSection, monitors: [] });
      continue;
    }
    const monitorMatch = line.match(/^###\s+Monitor:\s*(.+)$/);
    if (monitorMatch) {
      flush();
      currentMonitor = { name: monitorMatch[1].trim(), type: null, target: null, condition: null, action: null };
      continue;
    }
    if (!currentMonitor) continue;

    const typeMatch = line.match(/^-\s*\*\*Type\*\*:\s*(.+)$/);
    if (typeMatch) { currentMonitor.type = typeMatch[1].trim(); continue; }
    const targetMatch = line.match(/^-\s*\*\*Target\*\*:\s*(.+)$/);
    if (targetMatch) { currentMonitor.target = targetMatch[1].trim(); continue; }
    const conditionMatch = line.match(/^-\s*\*\*Condition\*\*:\s*(.+)$/);
    if (conditionMatch) { currentMonitor.condition = conditionMatch[1].trim(); continue; }
    const actionMatch = line.match(/^-\s*\*\*Action\*\*:\s*(.+)$/);
    if (actionMatch) { currentMonitor.action = actionMatch[1].trim(); continue; }
  }
  flush();
  return sections;
}

function copyToClipboard(text: string) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text);
  }
  return Promise.reject(new Error('Clipboard API unavailable'));
}

function MonitorSuggestionsPanel({ taskId, refreshKey = 0 }: MonitorSuggestionsPanelProps) {
  const { t } = useTranslation();
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getTaskMonitorSuggestions(taskId)
      .then(data => {
        if (!cancelled) setContent(data);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const axiosError = err as { message?: string };
        setError(axiosError.message || t('taskDetail.monitorSuggestions.loadError', 'Failed to load monitor suggestions'));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [taskId, refreshKey]);

  if (loading) {
    return <Spin />;
  }
  if (error) {
    return <Alert type="error" message={error} />;
  }
  if (!content) {
    return (
      <Alert
        type="info"
        showIcon
        message={t('taskDetail.monitorSuggestions.notProduced', 'No monitor suggestions yet. Use the Generate button in Actions to produce them.')}
      />
    );
  }

  const sections = parseMonitorSuggestions(content);
  if (sections.length === 0 || sections.every(s => s.monitors.length === 0)) {
    return (
      <Alert
        type="warning"
        showIcon
        message={t('taskDetail.monitorSuggestions.empty', 'The monitor-suggestions file is empty or could not be parsed.')}
      />
    );
  }

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      {sections.map(section => (
        <Card key={section.section} size="small" title={section.section}>
          {section.monitors.length === 0 ? (
            <span style={{ color: '#999' }}>{t('taskDetail.monitorSuggestions.emptySection', 'No monitors in this section.')}</span>
          ) : (
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              {section.monitors.map((monitor, idx) => (
                <Card
                  key={`${section.section}-${idx}`}
                  size="small"
                  type="inner"
                  title={
                    <Space>
                      <span>{monitor.name}</span>
                      {monitor.type && <Tag color="blue">{monitor.type}</Tag>}
                    </Space>
                  }
                  extra={
                    monitor.target && (
                      <Button
                        size="small"
                        onClick={() => {
                          copyToClipboard(monitor.target!).then(
                            () => message.success(t('taskDetail.monitorSuggestions.copied', 'Copied')),
                            () => message.error(t('taskDetail.monitorSuggestions.copyFailed', 'Copy failed')),
                          );
                        }}
                        data-testid="copy-monitor-target"
                      >
                        {t('taskDetail.monitorSuggestions.copy', 'Copy')}
                      </Button>
                    )
                  }
                >
                  {monitor.target && (
                    <p style={{ margin: '0 0 8px 0' }}>
                      <strong>{t('taskDetail.monitorSuggestions.target', 'Target')}:</strong>{' '}
                      <code>{monitor.target}</code>
                    </p>
                  )}
                  {monitor.condition && (
                    <p style={{ margin: '0 0 8px 0' }}>
                      <strong>{t('taskDetail.monitorSuggestions.condition', 'Condition')}:</strong> {monitor.condition}
                    </p>
                  )}
                  {monitor.action && (
                    <p style={{ margin: '8px 0 0 0', color: '#555' }}>
                      <strong>{t('taskDetail.monitorSuggestions.action', 'Action')}:</strong> {monitor.action}
                    </p>
                  )}
                </Card>
              ))}
            </Space>
          )}
        </Card>
      ))}
    </Space>
  );
}

export default MonitorSuggestionsPanel;
