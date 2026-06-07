import { useEffect, useState } from 'react';
import { Card, Alert, Spin, Tag, Space, Button, message } from 'antd';
import { useTranslation } from 'react-i18next';
import { getTaskTestSuggestions } from '../api/taskApi';

interface TestSuggestionsPanelProps {
  taskId: string;
  refreshKey?: number;
}

interface ParsedTest {
  name: string;
  type: string | null;
  goal: string | null;
  language: string;
  code: string;
  expected: string | null;
}

function parseTestSuggestions(content: string): { section: string; tests: ParsedTest[] }[] {
  if (!content.trim()) return [];
  const lines = content.split('\n');
  const sections: { section: string; tests: ParsedTest[] }[] = [];
  let currentSection = '';
  let currentTest: ParsedTest | null = null;
  let inCode = false;
  let codeBuffer: string[] = [];
  let codeLang = '';
  let expectCodeFence = false; // true after a `**Code**:` line, until we hit the opening fence or skip

  const flush = () => {
    if (currentTest) {
      currentTest.code = codeBuffer.join('\n').replace(/^\n+|\n+$/g, '');
      currentTest.language = codeLang;
      sections[sections.length - 1].tests.push(currentTest);
    }
    currentTest = null;
    codeBuffer = [];
    codeLang = '';
    expectCodeFence = false;
  };

  for (const line of lines) {
    const sectionMatch = line.match(/^##\s+(.+)$/);
    if (sectionMatch) {
      flush();
      currentSection = sectionMatch[1].trim();
      sections.push({ section: currentSection, tests: [] });
      continue;
    }
    const testMatch = line.match(/^###\s+Test:\s*(.+)$/);
    if (testMatch) {
      flush();
      currentTest = { name: testMatch[1].trim(), type: null, goal: null, language: '', code: '', expected: null };
      continue;
    }
    if (!currentTest) continue;

    // If we just hit `**Code**:`, look for the opening fence on the next non-empty line.
    if (expectCodeFence) {
      const fenceMatch = line.match(/^(\s*)?```(\w*)\s*$/);
      if (fenceMatch) {
        inCode = true;
        codeLang = fenceMatch[2] || '';
        expectCodeFence = false;
        continue;
      }
      // If a non-fence non-blank line appears, the code block was missing.
      if (line.trim() !== '') {
        expectCodeFence = false;
      }
    }

    if (inCode) {
      if (line.trim().startsWith('```')) {
        inCode = false;
      } else {
        codeBuffer.push(line);
      }
      continue;
    }

    const typeMatch = line.match(/^-\s*\*\*Type\*\*:\s*(.+)$/);
    if (typeMatch) { currentTest.type = typeMatch[1].trim(); continue; }
    const goalMatch = line.match(/^-\s*\*\*Goal\*\*:\s*(.+)$/);
    if (goalMatch) { currentTest.goal = goalMatch[1].trim(); continue; }
    const expectedMatch = line.match(/^-\s*\*\*Expected\*\*:\s*(.+)$/);
    if (expectedMatch) { currentTest.expected = expectedMatch[1].trim(); continue; }
    if (/^-?\s*\*\*Code\*\*:?\s*$/.test(line.trim())) {
      expectCodeFence = true;
      continue;
    }
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

function TestSuggestionsPanel({ taskId, refreshKey = 0 }: TestSuggestionsPanelProps) {
  const { t } = useTranslation();
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getTaskTestSuggestions(taskId)
      .then(data => {
        if (!cancelled) setContent(data);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const axiosError = err as { message?: string };
        setError(axiosError.message || t('taskDetail.testSuggestions.loadError', 'Failed to load test suggestions'));
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
        message={t('taskDetail.testSuggestions.notProduced', 'No test suggestions yet. Use the Generate button in Actions to produce them.')}
      />
    );
  }

  const sections = parseTestSuggestions(content);
  if (sections.length === 0 || sections.every(s => s.tests.length === 0)) {
    return (
      <Alert
        type="warning"
        showIcon
        message={t('taskDetail.testSuggestions.empty', 'The test-suggestions file is empty or could not be parsed.')}
      />
    );
  }

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      {sections.map(section => (
        <Card key={section.section} size="small" title={section.section}>
          {section.tests.length === 0 ? (
            <span style={{ color: '#999' }}>{t('taskDetail.testSuggestions.empty', 'No tests in this section.')}</span>
          ) : (
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              {section.tests.map((test, idx) => (
                <Card
                  key={`${section.section}-${idx}`}
                  size="small"
                  type="inner"
                  title={
                    <Space>
                      <span>{test.name}</span>
                      {test.type && <Tag color="blue">{test.type}</Tag>}
                    </Space>
                  }
                  extra={
                    <Button
                      size="small"
                      onClick={() => {
                        copyToClipboard(test.code).then(
                          () => message.success(t('taskDetail.testSuggestions.copied', 'Copied')),
                          () => message.error(t('taskDetail.testSuggestions.copyFailed', 'Copy failed')),
                        );
                      }}
                      data-testid="copy-test-code"
                    >
                      {t('taskDetail.testSuggestions.copy', 'Copy')}
                    </Button>
                  }
                >
                  {test.goal && (
                    <p style={{ margin: '0 0 8px 0' }}>
                      <strong>{t('taskDetail.testSuggestions.goal', 'Goal')}:</strong> {test.goal}
                    </p>
                  )}
                  {test.code && (
                    <pre
                      data-testid="test-code-pre"
                      style={{
                        background: '#fafafa',
                        border: '1px solid #f0f0f0',
                        padding: 8,
                        margin: 0,
                        fontSize: 12,
                        fontFamily: 'monospace',
                        overflowX: 'auto',
                      }}
                    >
                      {test.code}
                    </pre>
                  )}
                  {test.expected && (
                    <p style={{ margin: '8px 0 0 0', color: '#555' }}>
                      <strong>{t('taskDetail.testSuggestions.expected', 'Expected')}:</strong> {test.expected}
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

export default TestSuggestionsPanel;
