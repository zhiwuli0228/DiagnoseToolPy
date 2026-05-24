import { useState, useEffect } from 'react';
import {
  Card,
  Input,
  Button,
  Checkbox,
  Tag,
  Table,
  Spin,
  Alert,
  Space,
  Typography,
  Badge,
} from 'antd';
import { SearchOutlined, FolderOutlined } from '@ant-design/icons';
import { searchLogContent } from '../api/sourceApi';
import type { LogSearchResponse, LogSearchResult, SelectionItem } from '../types/api';

const { Text } = Typography;

interface SearchPanelProps {
  path: string;
  selections: SelectionItem[];
  onToggleSelection: (sel: SelectionItem) => void;
  onPathChange?: (path: string) => void;
  initialResults?: LogSearchResponse | null;
  loading?: boolean;
}

export default function SearchPanel({
  path,
  selections,
  onToggleSelection,
  onPathChange,
  initialResults,
  loading: externalLoading,
}: SearchPanelProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<LogSearchResponse | null>(null);

  // Use external results if provided
  useEffect(() => {
    if (initialResults !== undefined) {
      setResults(initialResults);
    }
  }, [initialResults]);

  const isExternalLoading = externalLoading !== undefined;
  const effectiveLoading = isExternalLoading ? externalLoading : loading;

  const [thread, setThread] = useState('');
  const [keywords, setKeywords] = useState<string[]>([]);
  const [keywordInput, setKeywordInput] = useState('');
  const [includeStack, setIncludeStack] = useState(true);

  const isSelected = (sel: SelectionItem) => {
    return selections.some(s => {
      if (s.type !== sel.type) return false;
      if (sel.type === 'log' && s.id !== sel.id) return false;
      if ((sel.type === 'group' || sel.type === 'group_all') && s.group_key !== sel.group_key) return false;
      return true;
    });
  };

  const handleSearch = async () => {
    if (!path.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const result = await searchLogContent({
        path,
        thread: thread || undefined,
        keywords: keywords.length > 0 ? keywords : undefined,
        include_stack: includeStack,
      });
      setResults(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '搜索失败');
    } finally {
      setLoading(false);
    }
  };

  const addKeyword = (value: string) => {
    const trimmed = value.trim();
    if (trimmed && !keywords.includes(trimmed)) {
      setKeywords([...keywords, trimmed]);
    }
    setKeywordInput('');
  };

  const removeKeyword = (kw: string) => {
    setKeywords(keywords.filter(k => k !== kw));
  };

  const columns = [
    { title: 'File', dataIndex: 'file_path', key: 'file_path', width: 150, ellipsis: true },
    { title: 'Line', dataIndex: 'line_no', key: 'line_no', width: 50 },
    { title: 'Time', dataIndex: 'timestamp', key: 'timestamp', width: 150 },
    { title: 'Level', dataIndex: 'level', key: 'level', width: 60 },
    { title: 'Message', dataIndex: 'message', key: 'message', ellipsis: true },
  ];

  return (
    <Card title="日志搜索" size="small">
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        <Input
          placeholder="日志目录路径"
          value={path}
          onChange={e => onPathChange?.(e.target.value)}
          prefix={<FolderOutlined />}
          style={{ width: '100%' }}
          size="small"
        />
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Input
            placeholder="Thread"
            value={thread}
            onChange={e => setThread(e.target.value)}
            style={{ width: 120 }}
            size="small"
          />
          <Input
            placeholder="Keyword"
            value={keywordInput}
            onChange={e => setKeywordInput(e.target.value)}
            onPressEnter={() => addKeyword(keywordInput)}
            style={{ width: 120 }}
            size="small"
          />
          <Button
            size="small"
            onClick={() => addKeyword(keywordInput)}
          >
            Add
          </Button>
          <Checkbox
            checked={includeStack}
            onChange={e => setIncludeStack(e.target.checked)}
          >
            堆栈
          </Checkbox>
          <Button
            type="primary"
            icon={<SearchOutlined />}
            onClick={handleSearch}
            loading={effectiveLoading}
            size="small"
          >
            搜索
          </Button>
        </div>

        {keywords.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {keywords.map(kw => (
              <Tag key={kw} closable onClose={() => removeKeyword(kw)}>{kw}</Tag>
            ))}
          </div>
        )}

        {error && (
          <Alert message={error} type="error" showIcon />
        )}

        {effectiveLoading && (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <Spin tip="搜索中..." />
          </div>
        )}

        {results && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <Text type="secondary">
                找到 {results.matched_count} 条匹配，扫描 {results.total_scanned_lines} 行
              </Text>
              <Badge count={selections.length} style={{ marginLeft: 8 }} />
            </div>

            {results.aggregated && results.aggregated.length > 0 ? (
              <div>
                {results.aggregated.slice(0, 10).map(group => {
                  const groupKey = group.key.replace(/[^a-zA-Z0-9]/g, '_');
                  const groupSelectedCount = group.matched_lines.slice(0, 5).filter((ml, idx) =>
                    isSelected({ type: 'log', id: `g:${groupKey}:${ml.file_path}:${ml.line_no}:${idx}` })
                  ).length;
                  const handleGroupToggle = () => {
                    onToggleSelection({ type: 'group', group_key: group.key });
                  };
                  const handleSelectAllInGroup = () => {
                    group.matched_lines.slice(0, 5).forEach((ml, idx) => {
                      onToggleSelection({ type: 'log', id: `g:${groupKey}:${ml.file_path}:${ml.line_no}:${idx}` });
                    });
                  };
                  return (
                    <Card
                      key={group.key}
                      size="small"
                      style={{ marginBottom: 8 }}
                      title={
                        <div style={{ display: 'flex', alignItems: 'center', width: '100%', justifyContent: 'space-between' }}>
                          <Checkbox
                            checked={isSelected({ type: 'group', group_key: group.key })}
                            onChange={handleGroupToggle}
                          >
                            {group.key} ({group.count})
                            {groupSelectedCount > 0 && (
                              <Tag color="blue" style={{ marginLeft: 8 }}>{groupSelectedCount} 已选</Tag>
                            )}
                          </Checkbox>
                          <Button size="small" type="link" onClick={handleSelectAllInGroup}>
                            全选
                          </Button>
                        </div>
                      }
                    >
                      <div style={{ maxHeight: 200, overflow: 'auto' }}>
                        {group.matched_lines.slice(0, 5).map((log, idx) => {
                          const logId = `g:${groupKey}:${log.file_path}:${log.line_no}:${idx}`;
                          return (
                            <div
                              key={logId}
                              style={{
                                display: 'flex',
                                gap: 8,
                                padding: '4px 0',
                                borderBottom: '1px solid #f0f0f0',
                              }}
                            >
                              <Checkbox
                                checked={isSelected({ type: 'log', id: logId })}
                                onChange={() => onToggleSelection({ type: 'log', id: logId })}
                              />
                              <Text type="secondary" style={{ fontSize: 11, width: 50 }}>
                                {log.line_no}
                              </Text>
                              <Text style={{ fontSize: 11 }} ellipsis>
                                {log.message}
                              </Text>
                            </div>
                          );
                        })}
                        {group.matched_lines.length > 5 && (
                          <Text type="secondary">... 还有 {group.matched_lines.length - 5} 条</Text>
                        )}
                      </div>
                    </Card>
                  );
                })}
              </div>
            ) : (
              <div>
                <div style={{ marginBottom: 8 }}>
                  <Button size="small" onClick={() => {
                    results.results.slice(0, 100).forEach((record, idx) => {
                      onToggleSelection({ type: 'log', id: `t:${record.file_path}:${record.line_no}:${idx}` });
                    });
                  }}>
                    全选当前页
                  </Button>
                </div>
                <Table
                  dataSource={results.results.slice(0, 100)}
                  columns={[
                    {
                      key: 'selection',
                      width: 40,
                      render: (_: unknown, record: LogSearchResult, index: number) => {
                        const logId = `t:${record.file_path}:${record.line_no}:${index}`;
                        return (
                          <Checkbox
                            checked={isSelected({ type: 'log', id: logId })}
                            onChange={() => onToggleSelection({ type: 'log', id: logId })}
                          />
                        );
                      },
                    },
                    ...columns,
                  ]}
                  rowKey={(_, i) => `${(_ as LogSearchResult).file_path}-${(_ as LogSearchResult).line_no}-${i}`}
                  size="small"
                  pagination={{ pageSize: 20 }}
                  scroll={{ x: 600 }}
                />
              </div>
            )}
          </div>
        )}
      </Space>
    </Card>
  );
}
