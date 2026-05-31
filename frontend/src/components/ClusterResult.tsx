import { Card, Tag, Timeline, Typography, Empty, Button, Checkbox, Space, Spin, Table } from 'antd';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { ClusterGroup, MatchedCase, SelectionItem, CachedLogEntry } from '../types/api';
import { getClusterMatchedLines } from '../api/clusterApi';

const { Text, Paragraph } = Typography;

interface MatchedCaseCardProps {
  matchedCase: MatchedCase;
}

export function MatchedCaseCard({ matchedCase }: MatchedCaseCardProps) {
  return (
    <Card size="small" style={{ marginTop: 8, background: '#f5f5f5' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Text strong>Case: {matchedCase.case_id}</Text>
        <Tag color={matchedCase.score >= 0.7 ? 'green' : matchedCase.score >= 0.5 ? 'orange' : 'default'}>
          {matchedCase.score.toFixed(2)}
        </Tag>
      </div>
      {matchedCase.summary && (
        <Paragraph type="secondary" style={{ marginBottom: 4, fontSize: 12 }}>
          {matchedCase.summary}
        </Paragraph>
      )}
      {matchedCase.root_cause && (
        <div style={{ marginBottom: 4 }}>
          <Text type="secondary" style={{ fontSize: 11 }}>Root Cause: </Text>
          <Text style={{ fontSize: 12 }}>{matchedCase.root_cause}</Text>
        </div>
      )}
      {matchedCase.solution && (
        <div>
          <Text type="secondary" style={{ fontSize: 11 }}>Solution: </Text>
          <Text style={{ fontSize: 12 }}>{matchedCase.solution}</Text>
        </div>
      )}
    </Card>
  );
}

interface ClusterResultProps {
  clusters: ClusterGroup[];
  taskId: string;
  onSelect?: (selection: SelectionItem) => void;
  selectedItems?: SelectionItem[];
}

export default function ClusterResult({ clusters, taskId, onSelect, selectedItems = [] }: ClusterResultProps) {
  const { t } = useTranslation();
  const [expandedClusters, setExpandedClusters] = useState<Set<number>>(new Set());
  const [matchedLinesMap, setMatchedLinesMap] = useState<Record<number, CachedLogEntry[]>>({});
  const [loadingLines, setLoadingLines] = useState<Set<number>>(new Set());

  const isClusterSelected = (clusterIndex: number) => {
    return selectedItems.some(s => s.type === 'cluster' && s.cluster_index === clusterIndex);
  };

  const toggleExpand = (clusterIndex: number) => {
    setExpandedClusters(prev => {
      const next = new Set(prev);
      if (next.has(clusterIndex)) {
        next.delete(clusterIndex);
      } else {
        next.add(clusterIndex);
      }
      return next;
    });

    // Load matched lines if expanding and not already loaded
    if (!expandedClusters.has(clusterIndex) && !matchedLinesMap[clusterIndex]) {
      loadMatchedLines(clusterIndex);
    }
  };

  const loadMatchedLines = async (clusterIndex: number) => {
    setLoadingLines(prev => new Set(prev).add(clusterIndex));
    try {
      const response = await getClusterMatchedLines(taskId, clusterIndex);
      setMatchedLinesMap(prev => ({
        ...prev,
        [clusterIndex]: response.matched_lines,
      }));
    } catch (error) {
      console.error('Failed to load matched lines:', error);
    } finally {
      setLoadingLines(prev => {
        const next = new Set(prev);
        next.delete(clusterIndex);
        return next;
      });
    }
  };

  const handleClusterSelect = (clusterIndex: number) => {
    if (onSelect) {
      onSelect({ type: 'cluster', cluster_index: clusterIndex });
    }
  };

  const isLogSelected = (logId: string) => {
    return selectedItems.some(s => s.type === 'log' && s.id === logId);
  };

  const handleLogSelect = (logId: string) => {
    if (onSelect) {
      onSelect({ type: 'log', id: logId });
    }
  };

  const matchedLinesColumns = [
    {
      title: 'Select',
      key: 'selection',
      width: 60,
      render: (_: unknown, record: CachedLogEntry) => (
        <Checkbox
          checked={isLogSelected(record.id)}
          onChange={() => handleLogSelect(record.id)}
        />
      ),
    },
    {
      title: 'Time',
      dataIndex: ['event', 'timestamp'],
      key: 'timestamp',
      width: 180,
      ellipsis: true,
    },
    {
      title: 'Level',
      dataIndex: ['event', 'level'],
      key: 'level',
      width: 70,
    },
    {
      title: 'Thread',
      dataIndex: ['event', 'thread'],
      key: 'thread',
      width: 120,
      ellipsis: true,
    },
    {
      title: 'Message',
      dataIndex: ['event', 'message'],
      key: 'message',
      ellipsis: true,
    },
  ];

  if (!clusters || clusters.length === 0) {
    return <Empty description={t('clusterResult.noAnomalyFound')} />;
  }

  return (
    <div>
      <Text strong style={{ display: 'block', marginBottom: 16 }}>
        {t('clusterResult.foundAnomalyPatterns', { count: clusters.length })}
      </Text>
      <Timeline
        items={clusters.map((cluster, clusterIndex) => {
          const hasMatches = cluster.matched_cases && cluster.matched_cases.length > 0;
          const isExpanded = expandedClusters.has(clusterIndex);
          const isSelected = isClusterSelected(clusterIndex);
          const isLoading = loadingLines.has(clusterIndex);
          const matchedLines = matchedLinesMap[clusterIndex] || [];

          return {
            color: hasMatches ? 'green' : 'gray',
            children: (
              <Card
                size="small"
                style={{
                  marginBottom: 8,
                  borderColor: isSelected ? '#1890ff' : hasMatches ? '#52c41a' : '#d9d9d9',
                  borderWidth: isSelected ? 2 : 1,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                  <div style={{ flex: 1, minWidth: 0, marginRight: 8 }}>
                    <Space align="start" size="small">
                      <Checkbox
                        checked={isSelected}
                        onChange={() => handleClusterSelect(clusterIndex)}
                      />
                      <Tag
                        color="error"
                        style={{
                          maxWidth: 300,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                        title={cluster.exception_class}
                      >
                        {cluster.exception_class.length > 40
                          ? cluster.exception_class.slice(0, 40) + '...'
                          : cluster.exception_class}
                      </Tag>
                      <Tag color="blue">{cluster.count} {t('clusterResult.times')}</Tag>
                    </Space>
                  </div>
                  <Button size="small" type="link" onClick={() => toggleExpand(clusterIndex)}>
                    {isExpanded ? t('clusterResult.collapse') : t('clusterResult.expand')}
                  </Button>
                </div>

                {!isExpanded && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      {cluster.time_distribution?.peak_hour !== 'N/A' && (
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          {t('clusterResult.peak')}: {cluster.time_distribution?.peak_hour}
                        </Text>
                      )}
                      {cluster.time_distribution?.range !== 'N/A' && (
                        <Text type="secondary" style={{ fontSize: 11, marginLeft: 8 }}>
                          {t('clusterResult.range')}: {cluster.time_distribution?.range}
                        </Text>
                      )}
                    </div>
                  </div>
                )}

                {isExpanded && cluster.sample_messages && cluster.sample_messages.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <Text type="secondary" style={{ fontSize: 11 }}>{t('clusterResult.typicalSamples')}</Text>
                    <div style={{ marginTop: 2 }}>
                      {cluster.sample_messages.slice(0, 3).map((msg, idx) => {
                        const isNormalized = msg.includes('<');
                        return (
                          <div
                            key={idx}
                            style={{
                              fontSize: 11,
                              fontFamily: isNormalized ? 'monospace' : 'inherit',
                              color: isNormalized ? '#1890ff' : '#666',
                              padding: '2px 6px',
                              background: isNormalized ? '#e6f7ff' : '#f5f5f5',
                              borderRadius: 2,
                              marginBottom: 2,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              borderLeft: isNormalized ? '2px solid #1890ff' : 'none',
                            }}
                            title={msg}
                          >
                            {msg}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {isExpanded && isLoading && (
                  <div style={{ textAlign: 'center', padding: 16 }}>
                    <Spin size="small" tip={t('clusterResult.loadingLogs')} />
                  </div>
                )}

                {isExpanded && !isLoading && matchedLines.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <Text type="secondary" style={{ fontSize: 11 }}>
                      {t('clusterResult.logEntryCount', { count: matchedLines.length })}
                      {cluster.count !== matchedLines.length && t('clusterResult.totalCount', { count: cluster.count })}
                      ):
                    </Text>
                    <Table
                      dataSource={matchedLines}
                      columns={matchedLinesColumns}
                      rowKey="id"
                      size="small"
                      pagination={{ pageSize: 10 }}
                      scroll={{ x: 800 }}
                    />
                  </div>
                )}

                {isExpanded && (
                  hasMatches ? (
                    <div style={{ marginTop: 8 }}>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        {t('clusterResult.matchedCases')}
                      </Text>
                      {cluster.matched_cases!.map((mc) => (
                        <MatchedCaseCard key={mc.case_id} matchedCase={mc} />
                      ))}
                    </div>
                  ) : (
                    <div style={{ marginTop: 8 }}>
                      <Tag color="warning">{t('clusterResult.noMatchedCases')}</Tag>
                    </div>
                  )
                )}
              </Card>
            ),
          };
        })}
      />
    </div>
  );
}
