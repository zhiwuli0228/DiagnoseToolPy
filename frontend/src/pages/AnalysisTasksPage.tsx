import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input, Button, Result, Spin, Alert, Card, Statistic, Row, Col, Collapse, Tag, Table, Tabs, Checkbox, message, Drawer, Space, Modal } from 'antd';
import { FileSearchOutlined, CheckCircleOutlined, CloseCircleOutlined, SearchOutlined, ClusterOutlined, FullscreenOutlined, ThunderboltOutlined, FolderOpenOutlined, CopyOutlined, DeleteOutlined, CheckCircleOutlined as CheckCircleFilled } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { ColumnsType } from 'antd/es/table';
import { checkSourceDirectory, scanSourceDirectory, searchLogContent, deleteTempDir } from '../api/sourceApi';
import { createClusterTask, pollClusterTask } from '../api/clusterApi';
import { diagnoseFromCluster, exportWorkspace, previewPrompt, isDegradedResponse, type DegradedResponse } from '../api/diagnosisApi';
import type { SourceCheckResponse, ScanResult, LogSearchResponse, LogSearchResult, AggregatedGroup, ClusterStatusResponse, SelectionItem } from '../types/api';
import { useDiagnosis } from '../context/DiagnosisContext';
import ClusterProgress from '../components/ClusterProgress';
import ClusterResultComponent from '../components/ClusterResult';

function AnalysisTasksPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { selections, setSelections } = useDiagnosis();
  const [path, setPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [checkResult, setCheckResult] = useState<SourceCheckResponse | null>(null);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [zipTaskId, setZipTaskId] = useState<string | null>(null);

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
  const [includeStack, setIncludeStack] = useState(true);

  // Cluster analysis state
  const [clusterTaskId, setClusterTaskId] = useState<string | null>(null);
  const [clusterStatus, setClusterStatus] = useState<ClusterStatusResponse | null>(null);
  const [clusterLoading, setClusterLoading] = useState(false);

  // Diagnosis drawer state
  const [diagnosisLoading, setDiagnosisLoading] = useState(false);
  const [diagnosisResult, setDiagnosisResult] = useState<string | undefined>(undefined);
  const [drawerVisible, setDrawerVisible] = useState(false);

  // Workspace export state
  const [workspaceDir, setWorkspaceDir] = useState<string | null>(null);
  const [exportSuccess, setExportSuccess] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);

  // Preview prompt state
  const [previewPromptModalOpen, setPreviewPromptModalOpen] = useState(false);
  const [previewPromptContent, setPreviewPromptContent] = useState<string | null>(null);
  const [previewExportType, setPreviewExportType] = useState<'search' | 'cluster' | null>(null);

  // Directory picker state
  const directoryInputRef = useRef<HTMLInputElement>(null);
  const [pendingExportType, setPendingExportType] = useState<'search' | 'cluster' | 'degraded' | null>(null);

  // Directory picker handlers
  const handleDirectorySelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const dir = files[0].webkitRelativePath.split('/')[0];
      if (dir && pendingExportType) {
        if (pendingExportType === 'search') {
          executeSearchExport(dir);
        } else if (pendingExportType === 'cluster') {
          executeClusterExport(dir);
        } else if (pendingExportType === 'degraded') {
          executeDegradedExport(dir);
        }
        setPendingExportType(null);
      }
    }
    e.target.value = '';
  };

  const triggerDirectoryPicker = (exportType: 'search' | 'cluster' | 'degraded') => {
    setPendingExportType(exportType);
    directoryInputRef.current?.click();
  };

  // Degraded modal state
  const [degradedModalOpen, setDegradedModalOpen] = useState(false);
  const [degradedInfo, setDegradedInfo] = useState<DegradedResponse | null>(null);

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
      // If ZIP was extracted, update path to the extracted directory for subsequent operations
      if (result.extracted_path) {
        setPath(result.extracted_path);
        setZipTaskId(result.zip_task_id || null);
      }
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
        include_stack: includeStack,
      });
      setSearchResults(result);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setSearchError(axiosError.response?.data?.detail || 'Failed to search logs');
    } finally {
      setSearchLoading(false);
    }
  };

  const handleClusterAnalysis = async () => {
    if (!path.trim()) return;
    setClusterLoading(true);
    setClusterStatus(null);
    setClusterTaskId(null);

    try {
      const result = await createClusterTask(path);
      setClusterTaskId(result.task_id);
      // Start polling
      pollClusterStatus(result.task_id);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      message.error(axiosError.response?.data?.detail || 'Failed to start cluster analysis');
      setClusterLoading(false);
    }
  };

  const pollClusterStatus = async (taskId: string) => {
    try {
      const status = await pollClusterTask(taskId);
      setClusterStatus(status);
      if (status.status === 'done') {
        setClusterLoading(false);
      } else {
        // Poll again after 2 seconds
        setTimeout(() => pollClusterStatus(taskId), 2000);
      }
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      message.error(axiosError.response?.data?.detail || 'Failed to poll cluster status');
      setClusterLoading(false);
    }
  };

  // Evidence basket handlers
  const isSelected = (sel: SelectionItem) => {
    return selections.some(s => {
      if (s.type !== sel.type) return false;
      if (sel.type === 'log' && s.id !== sel.id) return false;
      if (sel.type === 'cluster' && s.cluster_index !== sel.cluster_index) return false;
      if ((sel.type === 'group' || sel.type === 'group_all') && s.group_key !== sel.group_key) return false;
      return true;
    });
  };

  const toggleSelection = (sel: SelectionItem) => {
    if (isSelected(sel)) {
      setSelections(prev => prev.filter(s =>
        !(s.type === sel.type &&
          s.group_key === sel.group_key &&
          s.id === sel.id &&
          s.cluster_index === sel.cluster_index)
      ));
    } else {
      setSelections(prev => [...prev, sel]);
    }
  };

  // Select all logs in raw results
  const selectAllLogs = () => {
    const allLogSelections = searchResults?.results.map((record, idx) => ({
      type: 'log' as const,
      id: `${record.file_path}:${record.line_no}:${idx}`,
    })) || [];
    setSelections(prev => {
      const existingLogs = prev.filter(s => s.type === 'log');
      return [...prev.filter(s => s.type !== 'log'), ...allLogSelections.filter(
        newSel => !existingLogs.some(oldSel => oldSel.id === newSel.id)
      )];
    });
  };

  // Deselect all logs
  const deselectAllLogs = () => {
    setSelections(prev => prev.filter(s => s.type !== 'log'));
  };

  // Invert log selection
  const invertLogSelection = () => {
    if (!searchResults?.results) return;
    const currentLogSelections = selections.filter(s => s.type === 'log');
    const allLogSelections = searchResults.results.map((record, idx) => ({
      type: 'log' as const,
      id: `${record.file_path}:${record.line_no}:${idx}`,
    }));
    const currentLogIds = new Set(currentLogSelections.map(s => s.id));
    const newLogSelections = allLogSelections.filter(s => !currentLogIds.has(s.id));
    setSelections(prev => [...prev.filter(s => s.type !== 'log'), ...newLogSelections]);
  };

  const handleClusterDiagnose = async () => {
    if (!clusterTaskId) {
      message.error('No cluster task available');
      return;
    }

    // Filter selections to only include cluster selections
    const clusterSelections = selections.filter(s => s.type === 'cluster');
    if (clusterSelections.length === 0) {
      message.error('No cluster selected');
      return;
    }

    setDiagnosisLoading(true);
    setDiagnosisResult(undefined);

    try {
      const result = await diagnoseFromCluster({
        cache_key: clusterTaskId,
        selections: clusterSelections,
        options: {
          include_stack: true,
          include_timeline: true,
          max_tokens: 2000,
        },
      });

      // Check if degraded response
      if (isDegradedResponse(result)) {
        setDegradedInfo(result);
        setDegradedModalOpen(true);
        return;
      }

      setDiagnosisResult(result.diagnosis);
      setDrawerVisible(true);
    } catch (err: unknown) {
      if (isDegradedResponse(err)) {
        setDegradedInfo(err);
        setDegradedModalOpen(true);
      } else {
        message.error(err instanceof Error ? err.message : 'Diagnosis failed');
      }
    } finally {
      setDiagnosisLoading(false);
    }
  };

  const handlePreviewPromptSearch = async () => {
    if (!path.trim()) {
      message.warning(t('analysisTasks.pleaseSelectLogDir'));
      return;
    }

    setExportLoading(true);

    try {
      const result = await previewPrompt({
        cache_key: searchResults ? `search-${Date.now()}` : undefined,
        selections: selections.filter(s => s.type === 'log' || s.type === 'group' || s.type === 'group_all'),
      });

      setPreviewExportType('search');
      setPreviewPromptContent(result.prompt);
      setPreviewPromptModalOpen(true);
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('analysisTasks.previewFailed'));
    } finally {
      setExportLoading(false);
    }
  };

  const handleExportFromPreview = () => {
    setPreviewPromptModalOpen(false);
    // Use the preview export type to determine which export function to use
    const exportType = previewExportType || 'search';
    triggerDirectoryPicker(exportType);
  };

  const executeSearchExport = async (dir: string) => {
    setExportLoading(true);

    try {
      const result = await exportWorkspace({
        cache_key: searchResults ? `search-${Date.now()}` : undefined,
        workspace_dir: dir,
        selections: selections.filter(s => s.type === 'log' || s.type === 'group' || s.type === 'group_all'),
      });

      setWorkspaceDir(result.workspace_dir);
      setExportSuccess(true);
      message.success(t('analysisTasks.exportSuccess'));
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('analysisTasks.exportFailed'));
    } finally {
      setExportLoading(false);
    }
  };

  const handlePreviewPromptCluster = async () => {
    if (!clusterTaskId) {
      message.warning(t('analysisTasks.pleaseRunClusteringFirst'));
      return;
    }

    setExportLoading(true);

    try {
      const result = await previewPrompt({
        cache_key: clusterTaskId,
        selections: selections.filter(s => s.type === 'cluster'),
      });

      setPreviewExportType('cluster');
      setPreviewPromptContent(result.prompt);
      setPreviewPromptModalOpen(true);
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('analysisTasks.previewFailed'));
    } finally {
      setExportLoading(false);
    }
  };

  const handleExportFromPreviewCluster = () => {
    setPreviewPromptModalOpen(false);
    triggerDirectoryPicker('cluster');
  };

  const executeClusterExport = async (dir: string) => {
    setExportLoading(true);

    try {
      const result = await exportWorkspace({
        cache_key: clusterTaskId,
        workspace_dir: dir,
        selections: selections.filter(s => s.type === 'cluster'),
      });

      setWorkspaceDir(result.workspace_dir);
      setExportSuccess(true);
      message.success(t('analysisTasks.exportSuccess'));
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('analysisTasks.exportFailed'));
    } finally {
      setExportLoading(false);
    }
  };

  const handleCopyPrompt = async () => {
    message.info(t('analysisTasks.copyPromptManual'));
  };

  const handleExportFromDegraded = () => {
    if (!degradedInfo) return;
    triggerDirectoryPicker('degraded');
  };

  const executeDegradedExport = async (dir: string) => {
    setExportLoading(true);
    setDegradedModalOpen(false);

    try {
      const options = degradedInfo.workspace_export_options;
      const result = await exportWorkspace({
        session_id: options.session_id as string | undefined,
        task_id: options.task_id as string | undefined,
        cache_key: options.cache_key as string | undefined,
        workspace_dir: dir,
        user_context: options.user_context as any,
        selections: options.selections as SelectionItem[] | undefined,
      });

      setWorkspaceDir(result.workspace_dir);
      setExportSuccess(true);
      message.success(t('analysisTasks.exportSuccess'));
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('analysisTasks.exportFailed'));
    } finally {
      setExportLoading(false);
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

  const handleCleanup = async () => {
    if (!zipTaskId) {
      message.warning('No temp files to clean');
      return;
    }
    try {
      await deleteTempDir(zipTaskId);
      setZipTaskId(null);
      message.success('Temp files cleaned');
    } catch {
      message.error('Failed to clean temp files');
    }
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
      {/* Hidden directory picker */}
      <input
        ref={directoryInputRef}
        type="file"
        webkitdirectory="webkitdirectory"
        style={{ display: 'none' }}
        onChange={handleDirectorySelect}
      />

      {/* Preview Prompt Modal */}
      <Modal
        title={t('analysisTasks.diagnosisPromptPreview')}
        open={previewPromptModalOpen}
        onCancel={() => setPreviewPromptModalOpen(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setPreviewPromptModalOpen(false)}>
            {t('analysisTasks.close')}
          </Button>,
          <Button key="export" type="primary" icon={<FolderOpenOutlined />} onClick={handleExportFromPreview}>
            {t('analysisTasks.exportFromPreview')}
          </Button>,
        ]}
      >
        <div style={{ maxHeight: '60vh', overflow: 'auto' }}>
          <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: 12 }}>
            {previewPromptContent}
          </pre>
        </div>
      </Modal>

      <h1>{t('analysisTasks.title')}</h1>
      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<ThunderboltOutlined />}
          onClick={() => navigate('/diagnosis-studio?start=1')}
        >
          {t('analysisTasks.startDiagnosis')}
        </Button>
      </div>
      <Card style={{ marginBottom: 24 }}>
        <Input
          size="large"
          placeholder="Enter directory path (e.g., /data/logs or /data/logs/app.zip)"
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
          <Button
            icon={<ClusterOutlined />}
            onClick={handleClusterAnalysis}
            loading={clusterLoading}
            disabled={!path.trim() || !!clusterTaskId}
          >
            {t('analysisTasks.anomalyClustering')}
          </Button>
          <Button
            icon={<DeleteOutlined />}
            onClick={handleCleanup}
            disabled={!zipTaskId}
          >
            Clean Temp Files
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
                    <div style={{ marginBottom: 8 }}>
                      <Checkbox checked={includeStack} onChange={(e) => setIncludeStack(e.target.checked)}>
                        Include Stack Traces
                      </Checkbox>
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
            <Card
              title={`Search Results (${searchResults.matched_count} matches, scanned ${searchResults.total_scanned_lines} lines in ${searchResults.files_scanned} files)${searchResults.truncated ? ' [TRUNCATED]' : ''}`}
              extra={
                <Space>
                  <span style={{ fontSize: 12, color: '#666' }}>
                    {t('diagnosis.evidence.selectedCount', { count: selections.length })}
                  </span>
                  <Button
                    size="small"
                    icon={<FolderOpenOutlined />}
                    onClick={handlePreviewPromptSearch}
                    loading={exportLoading}
                  >
                    {t('analysisTasks.previewPrompt')}
                  </Button>
                  <Button
                    size="small"
                    type="primary"
                    icon={<ThunderboltOutlined />}
                    onClick={() => {
                      window.location.href = `/diagnosis-studio?path=${encodeURIComponent(path)}`;
                    }}
                  >
                    {t('nav.diagnosisStudio')}
                  </Button>
                </Space>
              }
            >
              {searchResults.aggregated && searchResults.aggregated.length > 0 ? (
                <Tabs
                  items={[
                    {
                      key: 'raw',
                      label: 'Raw Results',
                      children: (
                        <div>
                          <div style={{ marginBottom: 8, display: 'flex', gap: 8 }}>
                            <Button size="small" onClick={selectAllLogs}>{t('diagnosis.evidence.selectAll')}</Button>
                            <Button size="small" onClick={deselectAllLogs}>{t('diagnosis.evidence.deselectAll')}</Button>
                            <Button size="small" onClick={invertLogSelection}>{t('diagnosis.evidence.invertSelection')}</Button>
                          </div>
                          <Table
                            dataSource={searchResults.results}
                            columns={[
                              {
                                title: (
                                  <Checkbox
                                    checked={searchResults.results.length > 0 && selections.filter(s => s.type === 'log').length === searchResults.results.length}
                                    indeterminate={selections.filter(s => s.type === 'log').length > 0 && selections.filter(s => s.type === 'log').length < searchResults.results.length}
                                    onChange={(e) => e.target.checked ? selectAllLogs() : deselectAllLogs()}
                                  />
                                ),
                                key: 'selection',
                                width: 60,
                                render: (_, record: LogSearchResult, index: number) => {
                                  const logId = `${record.file_path}:${record.line_no}:${index}`;
                                  return (
                                    <Checkbox
                                      checked={isSelected({ type: 'log', id: logId })}
                                      onChange={() => toggleSelection({ type: 'log', id: logId })}
                                    />
                                  );
                                },
                              },
                              ...resultColumns,
                            ]}
                            rowKey={(_, i) => `${_.file_path}-${_.line_no}-${i}`}
                            size="small"
                            scroll={{ x: 900 }}
                            pagination={{ pageSize: 50 }}
                          />
                        </div>
                      ),
                    },
                    {
                      key: 'aggregated',
                      label: `Aggregated (${searchResults.aggregated.length} groups)`,
                      children: (
                        <Table
                          dataSource={searchResults.aggregated}
                          columns={[
                            {
                              title: 'Select',
                              key: 'selection',
                              width: 80,
                              render: (_, record: AggregatedGroup) => (
                                <Checkbox
                                  checked={isSelected({ type: 'group', group_key: record.key })}
                                  onChange={() => toggleSelection({ type: 'group', group_key: record.key })}
                                />
                              ),
                            },
                            { title: 'Count', dataIndex: 'count', key: 'count', width: 80, render: (v) => <b style={{ color: v > 1 ? '#cf1322' : undefined }}>{v}</b> },
                            { title: 'Key', dataIndex: 'key', key: 'key', ellipsis: true },
                            { title: 'Sample', dataIndex: 'sample_message', key: 'sample_message', ellipsis: true },
                          ]}
                          rowKey={(_, i) => `agg-${_.key}-${i}`}
                          size="small"
                          expandable={{
                            expandedRowRender: (record: AggregatedGroup) => (
                              <div>
                                <div style={{ marginBottom: 8 }}>
                                  <Button
                                    size="small"
                                    type="link"
                                    onClick={() => toggleSelection({ type: 'group_all', group_key: record.key })}
                                  >
                                    Select All in Group ({record.count})
                                  </Button>
                                </div>
                                <Table
                                  dataSource={record.matched_lines}
                                  columns={[
                                    {
                                      title: 'Select',
                                      key: 'selection',
                                      width: 60,
                                      render: (_, log: LogSearchResult, idx: number) => {
                                        const logId = `${log.file_path}:${log.line_no}:${idx}`;
                                        return (
                                          <Checkbox
                                            checked={isSelected({ type: 'log', id: logId })}
                                            onChange={() => toggleSelection({ type: 'log', id: logId })}
                                          />
                                        );
                                      },
                                    },
                                    ...resultColumns,
                                  ]}
                                  rowKey={(_, i) => `exp-${_.file_path}-${_.line_no}-${i}`}
                                  size="small"
                                  pagination={false}
                                  scroll={{ x: 900 }}
                                />
                              </div>
                            ),
                            rowExpandable: () => true,
                          } as object}
                          pagination={{ pageSize: 20 }}
                        />
                      ),
                    },
                  ]}
                />
              ) : (
                <div>
                  <div style={{ marginBottom: 8, display: 'flex', gap: 8 }}>
                    <Button size="small" onClick={selectAllLogs}>{t('diagnosis.evidence.selectAll')}</Button>
                    <Button size="small" onClick={deselectAllLogs}>{t('diagnosis.evidence.deselectAll')}</Button>
                    <Button size="small" onClick={invertLogSelection}>{t('diagnosis.evidence.invertSelection')}</Button>
                  </div>
                  <Table
                    dataSource={searchResults.results}
                    columns={[
                      {
                        title: (
                          <Checkbox
                            checked={searchResults.results.length > 0 && selections.filter(s => s.type === 'log').length === searchResults.results.length}
                            indeterminate={selections.filter(s => s.type === 'log').length > 0 && selections.filter(s => s.type === 'log').length < searchResults.results.length}
                            onChange={(e) => e.target.checked ? selectAllLogs() : deselectAllLogs()}
                          />
                        ),
                        key: 'selection',
                        width: 60,
                        render: (_, record: LogSearchResult, index: number) => {
                          const logId = `${record.file_path}:${record.line_no}:${index}`;
                          return (
                            <Checkbox
                              checked={isSelected({ type: 'log', id: logId })}
                              onChange={() => toggleSelection({ type: 'log', id: logId })}
                            />
                          );
                        },
                      },
                      ...resultColumns,
                    ]}
                    rowKey={(_, i) => `${_.file_path}-${_.line_no}-${i}`}
                    size="small"
                    scroll={{ x: 900 }}
                    pagination={{ pageSize: 50 }}
                  />
                </div>
              )}
            </Card>
          )}
        </>
      )}

      {/* Cluster Analysis Results */}
      {clusterStatus && (
        <Card title={t('analysisTasks.clusterAnalysis')} style={{ marginTop: 24 }}
          extra={
            <Space>
              <Button
                size="small"
                icon={<FolderOpenOutlined />}
                onClick={handlePreviewPromptCluster}
                loading={exportLoading}
              >
                {t('analysisTasks.previewPrompt')}
              </Button>
              <Button
                type="primary"
                size="small"
                disabled={!selections.some(s => s.type === 'cluster')}
                onClick={handleClusterDiagnose}
                loading={diagnosisLoading}
              >
                {t('analysisTasks.diagnoseSelectedClusters')}
              </Button>
            </Space>
          }
        >
          {clusterStatus.status !== 'done' && (
            <ClusterProgress
              status={clusterStatus.status}
              progress={clusterStatus.progress}
              currentStep={clusterStatus.current_step}
            />
          )}
          {clusterStatus.status === 'done' && clusterStatus.clusters && (
            <ClusterResultComponent
              clusters={clusterStatus.clusters}
              taskId={clusterTaskId || ''}
              onSelect={toggleSelection}
              selectedItems={selections}
            />
          )}
        </Card>
      )}

      {/* Diagnosis Result Drawer */}
      <Drawer
        title={t('analysisTasks.aiDiagnosisResult')}
        placement="right"
        width={600}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        extra={
          <Space>
            <Button
              size="small"
              icon={<FullscreenOutlined />}
              onClick={() => {
                // Open in new window
                const newWindow = window.open('', '_blank', 'width=800,height=600');
                if (newWindow) {
                  newWindow.document.write(`
                    <html>
                      <head><title>${t('analysisTasks.aiDiagnosisResult')}</title></head>
                      <body style="padding: 20px; font-family: monospace; white-space: pre-wrap;">
                        ${diagnosisResult}
                      </body>
                    </html>
                  `);
                  newWindow.document.close();
                }
              }}
            >
              {t('analysisTasks.newWindow')}
            </Button>
          </Space>
        }
      >
        {diagnosisResult ? (
          <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: 13 }}>
            {diagnosisResult}
          </pre>
        ) : (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin tip={t('analysisTasks.generatingDiagnosis')} />
          </div>
        )}
      </Drawer>

      {/* Degraded Response Modal */}
      <Modal
        title={t('analysisTasks.aiDiagnosisUnavailable')}
        open={degradedModalOpen}
        onCancel={() => setDegradedModalOpen(false)}
        footer={[
          <Button key="retry" type="primary" onClick={() => setDegradedModalOpen(false)}>
            {t('analysisTasks.close')}
          </Button>,
          <Button key="export" icon={<FolderOpenOutlined />} onClick={handleExportFromDegraded}>
            {t('analysisTasks.exportWorkspace')}
          </Button>,
        ]}
      >
        <Alert
          message={t('analysisTasks.llmServiceUnavailable')}
          description={degradedInfo?.message || t('analysisTasks.llmServiceUnavailableDesc')}
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      </Modal>

      {/* Export Success Modal */}
      <Modal
        title={t('analysisTasks.workspaceExportSuccess')}
        open={exportSuccess}
        onCancel={() => setExportSuccess(false)}
        footer={[
          <Button key="copy" icon={<CopyOutlined />} onClick={handleCopyPrompt}>
            {t('analysisTasks.copyPrompt')}
          </Button>,
        ]}
      >
        <Alert
          message={t('analysisTasks.exportSuccessDesc')}
          description={
            <div>
              <p>{t('analysisTasks.workspaceDir')}: {workspaceDir}</p>
              <p>{t('analysisTasks.openInOpenCode')}</p>
            </div>
          }
          type="success"
          showIcon
        />
      </Modal>

      {/* Floating button to show diagnosis result when drawer is closed */}
      {diagnosisResult && !drawerVisible && (
        <Button
          type="primary"
          icon={<FileSearchOutlined />}
          style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 1001 }}
          onClick={() => setDrawerVisible(true)}
        >
          {t('analysisTasks.viewDiagnosisResult')}
        </Button>
      )}
    </div>
  );
}

export default AnalysisTasksPage;
