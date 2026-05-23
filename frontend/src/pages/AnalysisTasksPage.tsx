import { useState } from 'react';
import { Input, Button, Result, Spin, Alert, Card, Statistic, Row, Col, Collapse, Tag, Table, Tabs, Checkbox, ExpandableConfig } from 'antd';
import { FileSearchOutlined, CheckCircleOutlined, CloseCircleOutlined, SearchOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { checkSourceDirectory, scanSourceDirectory, searchLogContent } from '../api/sourceApi';
import type { SourceCheckResponse, ScanResult, LogSearchResponse, LogSearchResult, AggregatedGroup } from '../types/api';

function AnalysisTasksPage() {
  const [path, setPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [checkResult, setCheckResult] = useState<SourceCheckResponse | null>(null);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Search state
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<LogSearchResponse | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [timeStart, setTimeStart] = useState('');
  const [timeEnd, setTimeEnd] = useState('');
  const [thread, setThread] = useState('');
  const [keywords, setKeywords] = useState<string[]>([]);
  const [keywordInput, setKeywordInput] = useState('');
  const [excludeKeywords, setExcludeKeywords] = useState<string[]>([]);
  const [excludeKeywordInput, setExcludeKeywordInput] = useState('');
  const [aggregate, setAggregate] = useState(false);
  const [includeThread, setIncludeThread] = useState(false);
  const [includeTime, setIncludeTime] = useState(false);
  const [messageOnly, setMessageOnly] = useState(false);

  const handleCheck = async () => {
    if (!path.trim()) return;
    setLoading(true);
    setError(null);
    setCheckResult(null);
    setScanResult(null);

    try {
      const result = await checkSourceDirectory(path);
      setCheckResult(result);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || 'Failed to check directory');
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async () => {
    if (!path.trim()) return;
    setLoading(true);
    setError(null);
    setScanResult(null);

    try {
      const result = await scanSourceDirectory(path);
      setScanResult(result);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || 'Failed to scan directory');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!path.trim()) return;
    setSearchLoading(true);
    setSearchError(null);
    setSearchResults(null);

    try {
      const result = await searchLogContent({
        path,
        time_start: timeStart || undefined,
        time_end: timeEnd || undefined,
        thread: thread || undefined,
        keywords: keywords.length > 0 ? keywords : undefined,
        exclude_keywords: excludeKeywords.length > 0 ? excludeKeywords : undefined,
        aggregate,
        include_thread: includeThread,
        include_time: includeTime,
        message_only: messageOnly,
      });
      setSearchResults(result);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setSearchError(axiosError.response?.data?.detail || 'Failed to search logs');
    } finally {
      setSearchLoading(false);
    }
  };

  const addKeyword = (value: string, setter: (v: string[]) => void, currentList: string[]) => {
    const trimmed = value.trim();
    if (trimmed && !currentList.includes(trimmed)) {
      setter([...currentList, trimmed]);
    }
  };

  const removeKeyword = (kw: string, setter: (v: string[]) => void) => {
    setter(keywords.filter((k) => k !== kw));
  };

  const resultColumns: ColumnsType<LogSearchResult> = [
    { title: 'File', dataIndex: 'file_path', key: 'file_path', width: 200, ellipsis: true },
    { title: 'Line', dataIndex: 'line_no', key: 'line_no', width: 60 },
    { title: 'Time', dataIndex: 'timestamp', key: 'timestamp', width: 180 },
    { title: 'Level', dataIndex: 'level', key: 'level', width: 70 },
    { title: 'Thread', dataIndex: 'thread', key: 'thread', width: 120, ellipsis: true },
    { title: 'Message', dataIndex: 'message', key: 'message', ellipsis: true },
  ];

  return (
    <div>
      <h1>Analysis Tasks</h1>
      <Card style={{ marginBottom: 24 }}>
        <Input
          size="large"
          placeholder="Enter directory path (e.g., /data/diagnose/input)"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          style={{ marginBottom: 16 }}
        />
        <div style={{ display: 'flex', gap: 8 }}>
          <Button
            type="primary"
            icon={<CheckCircleOutlined />}
            onClick={handleCheck}
            loading={loading}
          >
            Check Directory
          </Button>
          <Button
            icon={<FileSearchOutlined />}
            onClick={handleScan}
            loading={loading}
            disabled={!path.trim()}
          >
            Scan Directory
          </Button>
        </div>
      </Card>

      {loading && (
        <div style={{ textAlign: 'center', margin: 24 }}>
          <Spin size="large" tip="Processing..." />
        </div>
      )}

      {error && (
        <Alert
          message="Error"
          description={error}
          type="error"
          showIcon
          closable
          style={{ marginBottom: 24 }}
        />
      )}

      {checkResult && !scanResult && (
        <Result
          status={checkResult.allowed ? 'success' : 'error'}
          icon={checkResult.allowed ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
          title={checkResult.allowed ? 'Directory is allowed' : 'Directory is not allowed'}
          subTitle={`Path: ${checkResult.path}`}
        />
      )}

      {scanResult && (
        <>
          <Card title="Scan Results" style={{ marginBottom: 24 }}>
            <Row gutter={[16, 16]}>
              <Col xs={12} sm={6}>
                <Statistic title="Total Files" value={scanResult.total_files} />
              </Col>
              <Col xs={12} sm={6}>
                <Statistic
                  title="Total Size"
                  value={scanResult.total_bytes}
                  formatter={(value) => `${(Number(value) / 1024 / 1024).toFixed(2)} MB`}
                />
              </Col>
              <Col xs={12} sm={6}>
                <Statistic title="Error Count" value={scanResult.error_count} valueStyle={{ color: '#cf1322' }} />
              </Col>
              <Col xs={12} sm={6}>
                <Statistic title="Warning Count" value={scanResult.warn_count} valueStyle={{ color: '#faad14' }} />
              </Col>
            </Row>
          </Card>

          <Collapse
            style={{ marginBottom: 24 }}
            items={[
              {
                key: 'search',
                label: <span><SearchOutlined /> Log Content Search</span>,
                children: (
                  <div>
                    <Row gutter={[8, 8]} style={{ marginBottom: 8 }}>
                      <Col xs={24} sm={12}>
                        <label>Time Start: </label>
                        <Input
                          type="datetime-local"
                          value={timeStart}
                          onChange={(e) => setTimeStart(e.target.value)}
                          style={{ width: '100%' }}
                        />
                      </Col>
                      <Col xs={24} sm={12}>
                        <label>Time End: </label>
                        <Input
                          type="datetime-local"
                          value={timeEnd}
                          onChange={(e) => setTimeEnd(e.target.value)}
                          style={{ width: '100%' }}
                        />
                      </Col>
                      <Col xs={24} sm={12}>
                        <label>Thread: </label>
                        <Input
                          placeholder="e.g. worker-1"
                          value={thread}
                          onChange={(e) => setThread(e.target.value)}
                          style={{ width: '100%' }}
                        />
                      </Col>
                    </Row>
                    <div style={{ marginBottom: 8 }}>
                      <label>Keywords (AND): </label>
                      <Input
                        placeholder="Enter keyword, press Enter to add"
                        value={keywordInput}
                        onChange={(e) => setKeywordInput(e.target.value)}
                        onPressEnter={() => { addKeyword(keywordInput, setKeywords, keywords); setKeywordInput(''); }}
                        onBlur={() => { if (keywordInput.trim()) addKeyword(keywordInput, setKeywords, keywords); }}
                        style={{ marginBottom: 4 }}
                      />
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                        {keywords.map((kw) => (
                          <Tag key={kw} closable onClose={() => removeKeyword(kw, setKeywords)}>{kw}</Tag>
                        ))}
                      </div>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <label>Exclude Keywords: </label>
                      <Input
                        placeholder="Enter keyword to exclude, press Enter"
                        value={excludeKeywordInput}
                        onChange={(e) => setExcludeKeywordInput(e.target.value)}
                        onPressEnter={() => { addKeyword(excludeKeywordInput, setExcludeKeywords, excludeKeywords); setExcludeKeywordInput(''); }}
                        onBlur={() => { if (excludeKeywordInput.trim()) addKeyword(excludeKeywordInput, setExcludeKeywords, excludeKeywords); }}
                        style={{ marginBottom: 4 }}
                      />
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                        {excludeKeywords.map((kw) => (
                          <Tag key={kw} closable color="red" onClose={() => removeKeyword(kw, setExcludeKeywords)}>{kw}</Tag>
                        ))}
                      </div>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <Checkbox checked={aggregate} onChange={(e) => setAggregate(e.target.checked)}>
                        Enable Aggregation
                      </Checkbox>
                      {aggregate && (
                        <div style={{ marginLeft: 20, marginTop: 4 }}>
                          <Checkbox checked={includeThread} onChange={(e) => setIncludeThread(e.target.checked)} style={{ marginRight: 12 }}>
                            Include Thread in grouping
                          </Checkbox>
                          <Checkbox checked={includeTime} onChange={(e) => setIncludeTime(e.target.checked)} style={{ marginRight: 12 }}>
                            Include Time in grouping
                          </Checkbox>
                          <Checkbox checked={messageOnly} onChange={(e) => setMessageOnly(e.target.checked)}>
                            Message only (no thread/time)
                          </Checkbox>
                        </div>
                      )}
                    </div>
                    <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch} loading={searchLoading}>
                      Search
                    </Button>
                  </div>
                ),
              },
            ]}
          />

          {searchError && (
            <Alert message="Search Error" description={searchError} type="error" showIcon closable style={{ marginBottom: 24 }} />
          )}

          {searchResults && (
            <Card title={`Search Results (${searchResults.matched_count} matches, scanned ${searchResults.total_scanned_lines} lines in ${searchResults.files_scanned} files)${searchResults.truncated ? ' [TRUNCATED]' : ''}`}>
              {searchResults.aggregated && searchResults.aggregated.length > 0 ? (
                <Tabs
                  items={[
                    {
                      key: 'raw',
                      label: 'Raw Results',
                      children: (
                        <Table
                          dataSource={searchResults.results}
                          columns={resultColumns}
                          rowKey={(_, i) => `${_.file_path}-${_.line_no}-${i}`}
                          size="small"
                          scroll={{ x: 900 }}
                          pagination={{ pageSize: 50 }}
                        />
                      ),
                    },
                    {
                      key: 'aggregated',
                      label: `Aggregated (${searchResults.aggregated.length} groups)`,
                      children: (
                        <Table
                          dataSource={searchResults.aggregated}
                          columns={[
                            { title: 'Count', dataIndex: 'count', key: 'count', width: 80, render: (v) => <b style={{ color: v > 1 ? '#cf1322' : undefined }}>{v}</b> },
                            { title: 'Key', dataIndex: 'key', key: 'key', ellipsis: true },
                            { title: 'Sample', dataIndex: 'sample_message', key: 'sample_message', ellipsis: true },
                          ]}
                          rowKey={(_, i) => `agg-${_.key}-${i}`}
                          size="small"
                          expandable={{
                            expandedRowRender: (record: AggregatedGroup) => (
                              <Table
                                dataSource={record.matched_lines}
                                columns={resultColumns}
                                rowKey={(_, idx) => `exp-${_.file_path}-${_.line_no}-${idx}`}
                                size="small"
                                pagination={false}
                                scroll={{ x: 900 }}
                              />
                            ),
                            rowExpandable: () => true,
                          } as ExpandableConfig<AggregatedGroup>}
                          pagination={{ pageSize: 20 }}
                        />
                      ),
                    },
                  ]}
                />
              ) : (
                <Table
                  dataSource={searchResults.results}
                  columns={resultColumns}
                  rowKey={(_, i) => `${_.file_path}-${_.line_no}-${i}`}
                  size="small"
                  scroll={{ x: 900 }}
                  pagination={{ pageSize: 50 }}
                />
              )}
            </Card>
          )}
        </>
      )}
    </div>
  );
}

export default AnalysisTasksPage;
