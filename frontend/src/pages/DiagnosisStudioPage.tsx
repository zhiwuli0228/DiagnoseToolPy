import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Row, Col, Card, Typography, Button, message, Alert, List, Tag, Space, Modal, ModalProps } from 'antd';
import { ThunderboltOutlined, DeleteOutlined, FolderOpenOutlined, CopyOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useSession } from '../hooks/useSession';
import { useResultDetection } from '../hooks/useResultDetection';
import {
  startConversation,
  continueConversation,
  skipFollowUp,
  endConversation,
  getConversation,
} from '../api/conversationApi';
import { exportWorkspace, previewPrompt, isDegradedResponse, type DegradedResponse } from '../api/diagnosisApi';
import type {
  ConversationTurn,
  ConversationStartResponse,
  SelectionItem,
} from '../types/api';
import { useDiagnosis } from '../context/DiagnosisContext';
import ConversationThread from '../components/ConversationThread';
import DiagnosisModeToggle from '../components/DiagnosisModeToggle';

const { Title, Text } = Typography;

function DiagnosisStudioPage() {
  const { t } = useTranslation();
  const { sessionId, createSession } = useSession();
  const [searchParams, setSearchParams] = useSearchParams();
  const { selections, userContext, setUserContext, loading, setLoading, removeSelection, clearSelections } = useDiagnosis();

  const [mode, setMode] = useState<'user-priority' | 'log-priority'>('user-priority');

  // Conversation state
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<string | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [diagnosisComplete, setDiagnosisComplete] = useState(false);
  const [showConversation, setShowConversation] = useState(false);

  // Workspace export state
  const [workspaceDir, setWorkspaceDir] = useState<string | null>(null);
  const [exportSuccess, setExportSuccess] = useState(false);
  const [exportedPrompt, setExportedPrompt] = useState<string | null>(null);
  const [degradedModalOpen, setDegradedModalOpen] = useState(false);
  const [degradedInfo, setDegradedInfo] = useState<DegradedResponse | null>(null);

  // Preview prompt state
  const [previewPromptModalOpen, setPreviewPromptModalOpen] = useState(false);
  const [previewPromptContent, setPreviewPromptContent] = useState<string | null>(null);

  // Directory picker ref and state
  const directoryInputRef = useRef<HTMLInputElement>(null);
  const [pendingExportType, setPendingExportType] = useState<'preview' | 'degraded' | null>(null);

  // Directory picker handler
  const handleDirectorySelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      // Get the directory path from the first file
      const dir = files[0].webkitRelativePath.split('/')[0];
      if (dir && pendingExportType) {
        if (pendingExportType === 'preview') {
          executePreviewPromptExport(dir);
        } else if (pendingExportType === 'degraded') {
          executeDegradedExport(dir);
        }
        setPendingExportType(null);
      }
    }
    // Reset input value so the same directory can be selected again
    e.target.value = '';
  };

  const triggerDirectoryPicker = (exportType: 'preview' | 'degraded') => {
    setPendingExportType(exportType);
    directoryInputRef.current?.click();
  };

  // Result detection
  const { isPolling, resultContent, setResultContent, startPolling, checkNow } = useResultDetection({
    workspaceDir,
    enabled: exportSuccess,
  });

  // Load existing conversation on mount
  useEffect(() => {
    if (sessionId) {
      loadConversation(sessionId);
    }
  }, [sessionId]);

  // Auto-start diagnosis when navigating from AIDiagnosisButton with start=1
  useEffect(() => {
    if (searchParams.get('start') === '1') {
      searchParams.delete('start');
      setSearchParams(searchParams, { replace: true });
      if (!showConversation && !loading && selections.length > 0) {
        handleStartDiagnosis();
      }
    }
  }, [searchParams]);

  // Handle result detection
  useEffect(() => {
    if (!resultContent) {
      return;
    }

    const showModal = () => {
      Modal.confirm({
        title: t('useResultDetection.detectedDiagnosisResult'),
        content: t('useResultDetection.detectedDiagnosisResult'),
        okText: t('analysisTasks.import'),
        cancelText: t('analysisTasks.ignore'),
        onOk: () => {
          handleImportResult(resultContent);
          resetResultDetection();
        },
        onCancel: () => {
          resetResultDetection();
        },
      });
    };

    // Delay to avoid React concurrent mode issues
    const timer = setTimeout(showModal, 0);
    return () => clearTimeout(timer);
  }, [resultContent]);

  const resetResultDetection = () => {
    setExportSuccess(false);
    setResultContent(null);
  };

  const loadConversation = async (sid: string) => {
    try {
      const history = await getConversation(sid);
      if (history.turns.length > 0) {
        setTurns(history.turns);
        setCurrentSessionId(sid);
        setShowConversation(true);
        const lastTurn = history.turns[history.turns.length - 1];
        if (lastTurn.ai_question && !lastTurn.ai_diagnosis) {
          setCurrentQuestion(lastTurn.ai_question);
        }
        if (lastTurn.ai_diagnosis) {
          setDiagnosisComplete(true);
        }
      }
    } catch (err) {
      // Session not found or error - clear stale session and reset state
      console.warn('Failed to load conversation:', err);
      if (err instanceof Error && err.message.includes('404')) {
        localStorage.removeItem('diagnose_session_id');
        setCurrentSessionId(null);
        setShowConversation(false);
        setTurns([]);
        setCurrentQuestion(null);
        setDiagnosisComplete(false);
      }
    }
  };

  const handleStartDiagnosis = async () => {
    if (!userContext.phenomenon.trim() && !userContext.stack.trim() && selections.length === 0) {
      message.warning(t('diagnosis.pleaseSelectEvidenceOrFillInfo'));
      return;
    }

    setLoading(true);

    try {
      const evidenceRefs = selections.map(sel => {
        if (sel.type === 'log' && sel.id) return sel.id;
        if (sel.type === 'group' && sel.group_key) return sel.group_key;
        if (sel.type === 'cluster' && sel.cluster_index !== undefined) return `cluster:${sel.cluster_index}`;
        return '';
      }).filter(Boolean);

      const result = await startConversation({
        session_id: currentSessionId || undefined,
        user_context: userContext,
        evidence_refs: evidenceRefs,
        mode,
        max_follow_up_rounds: 3,
      });

      // Check if degraded response
      if (isDegradedResponse(result)) {
        handleDegradedResponse(result);
        return;
      }

      setShowConversation(true);
      handleResponse(result);
    } catch (err: unknown) {
      if (isDegradedResponse(err)) {
        handleDegradedResponse(err);
      } else {
        message.error(err instanceof Error ? err.message : t('analysisTasks.diagnosisStartFailed'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDegradedResponse = (degraded: DegradedResponse) => {
    setDegradedInfo(degraded);
    setDegradedModalOpen(true);
  };

  const handlePreviewPrompt = async () => {
    if (!userContext.phenomenon.trim() && !userContext.stack.trim() && selections.length === 0) {
      message.warning(t('diagnosis.pleaseSelectEvidenceOrFillInfo'));
      return;
    }

    setLoading(true);

    try {
      const result = await previewPrompt({
        session_id: currentSessionId || undefined,
        user_context: userContext,
        selections,
      });

      setPreviewPromptContent(result.prompt);
      setPreviewPromptModalOpen(true);
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('analysisTasks.previewFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleExportFromPreview = () => {
    setPreviewPromptModalOpen(false);
    triggerDirectoryPicker('preview');
  };

  const executePreviewPromptExport = async (dir: string) => {
    setLoading(true);

    try {
      const evidenceRefs = selections.map(sel => {
        if (sel.type === 'log' && sel.id) return sel.id;
        if (sel.type === 'group' && sel.group_key) return sel.group_key;
        if (sel.type === 'cluster' && sel.cluster_index !== undefined) return `cluster:${sel.cluster_index}`;
        return '';
      }).filter(Boolean);

      const result = await exportWorkspace({
        session_id: currentSessionId || undefined,
        workspace_dir: dir,
        user_context: userContext,
        selections,
      });

      setWorkspaceDir(result.workspace_dir);
      setExportSuccess(true);
      message.success(t('analysisTasks.exportSuccess'));

      // Start polling for result
      startPolling();

    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('analysisTasks.exportFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleCopyPrompt = async () => {
    if (!exportedPrompt) {
      // Try to fetch the prompt.md content
      try {
        const response = await fetch(`/api/diagnosis/export-workspace?workspace_dir=${encodeURIComponent(workspaceDir || '')}`);
        // This won't work as-is, need a separate endpoint
      } catch {
        // Fallback - just show success
      }
    }
    message.info(t('analysisTasks.copyPromptManual'));
  };

  const handleCheckResult = async () => {
    const content = await checkNow();
    if (content) {
      handleImportResult(content);
    } else {
      message.info(t('analysisTasks.resultNotDetected'));
    }
  };

  const handleImportResult = (content: string) => {
    // For now, just show the result - in full implementation would save to case
    message.success(t('analysisTasks.importSuccess'));
    setExportSuccess(false);
  };

  const handleExportFromDegraded = () => {
    if (!degradedInfo) return;
    triggerDirectoryPicker('degraded');
  };

  const executeDegradedExport = async (dir: string) => {
    setLoading(true);
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

      // Start polling for result
      startPolling();

    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('analysisTasks.exportFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    setDegradedModalOpen(false);
    setDegradedInfo(null);
    handleStartDiagnosis();
  };

  const handleContinue = async (reply: string) => {
    if (!currentSessionId) return;

    setLoading(true);

    try {
      const result = await continueConversation(currentSessionId, {
        user_reply: reply,
      });

      // Check if degraded response
      if (isDegradedResponse(result)) {
        handleDegradedResponse(result);
        return;
      }

      handleResponse(result);
    } catch (err: unknown) {
      if (isDegradedResponse(err)) {
        handleDegradedResponse(err);
      } else {
        message.error(err instanceof Error ? err.message : t('analysisTasks.sendFailed'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = async () => {
    if (!currentSessionId) return;

    setLoading(true);

    try {
      const result = await skipFollowUp(currentSessionId);

      // Check if degraded response
      if (isDegradedResponse(result)) {
        handleDegradedResponse(result);
        return;
      }

      const newTurn: ConversationTurn = {
        turn_id: result.turn_id,
        user_context: userContext,
        evidence_refs: [],
        ai_diagnosis: result.disclaimer + '\n\n' + result.ai_diagnosis,
        mode,
        timestamp: new Date().toISOString(),
      };
      setTurns((prev) => [...prev, newTurn]);
      setCurrentQuestion(null);
      setDiagnosisComplete(true);
    } catch (err: unknown) {
      if (isDegradedResponse(err)) {
        handleDegradedResponse(err);
      } else {
        message.error(err instanceof Error ? err.message : t('analysisTasks.skipFailed'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleEnd = async () => {
    if (!currentSessionId) return;

    setLoading(true);

    try {
      const result = await endConversation(currentSessionId);
      message.success(
        result.is_draft
          ? t('diagnosis.endDiagnosisDraft', { score: result.quality_score?.total })
          : t('diagnosis.endDiagnosisCase', { score: result.quality_score?.total })
      );
      handleReset();
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : t('analysisTasks.endDiagnosisFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleResponse = (response: ConversationStartResponse) => {
    setCurrentSessionId(response.session_id);

    const evidenceRefs = selections.map(sel => {
      if (sel.type === 'log' && sel.id) return sel.id;
      if (sel.type === 'group' && sel.group_key) return sel.group_key;
      if (sel.type === 'cluster' && sel.cluster_index !== undefined) return `cluster:${sel.cluster_index}`;
      return '';
    }).filter(Boolean);

    const newTurn: ConversationTurn = {
      turn_id: response.turn_id,
      user_context: userContext,
      evidence_refs: evidenceRefs,
      ai_question: response.ai_question || undefined,
      ai_diagnosis: response.ai_diagnosis || undefined,
      mode,
      timestamp: new Date().toISOString(),
    };

    setTurns((prev) => [...prev, newTurn]);

    if (response.state === 'awaiting_user_reply') {
      setCurrentQuestion(response.ai_question || null);
      setDiagnosisComplete(false);
    } else if (response.state === 'diagnosis_complete' || response.state === 'skipped') {
      setCurrentQuestion(null);
      setDiagnosisComplete(true);
    }
  };

  const handleReset = () => {
    setTurns([]);
    setCurrentQuestion(null);
    setDiagnosisComplete(false);
    setCurrentSessionId(null);
    setExportSuccess(false);
    setWorkspaceDir(null);
    clearSelections();
    setShowConversation(false);
    createSession();
  };

  const getSelectionLabel = (sel: SelectionItem) => {
    if (sel.type === 'group' || sel.type === 'group_all') {
      return sel.group_key || t('diagnosis.evidence.unknownGroup');
    }
    if (sel.type === 'log') {
      return `${t('diagnosis.evidence.logEntryShort')} (${sel.id?.slice(0, 12)}...)`;
    }
    if (sel.type === 'cluster') {
      return `${t('diagnosis.evidence.cluster')} #${sel.cluster_index}`;
    }
    return t('diagnosis.evidence.unknown');
  };

  const getSelectionTypeTag = (sel: SelectionItem) => {
    const colorMap: Record<string, string> = {
      group: 'blue',
      group_all: 'cyan',
      log: 'green',
      cluster: 'purple',
    };
    const labelKeyMap: Record<string, string> = {
      group: 'diagnosis.evidence.group',
      group_all: 'diagnosis.evidence.allGroups',
      log: 'diagnosis.evidence.logEntry',
      cluster: 'diagnosis.evidence.cluster',
    };
    return <Tag color={colorMap[sel.type]}>{t(labelKeyMap[sel.type])}</Tag>;
  };

  return (
    <div style={{ padding: 24, height: '100%' }}>
      {/* Hidden directory picker */}
      <input
        ref={directoryInputRef}
        type="file"
        webkitdirectory="webkitdirectory"
        style={{ display: 'none' }}
        onChange={handleDirectorySelect}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>{t('app.title')}</Title>
        {showConversation && (
          <Button onClick={handleReset}>{t('analysisTasks.resetAndStart')}</Button>
        )}
      </div>

      {/* Degraded Response Modal */}
      <Modal
        title={t('analysisTasks.aiDiagnosisUnavailable')}
        open={degradedModalOpen}
        onCancel={() => setDegradedModalOpen(false)}
        footer={[
          <Button key="retry" type="primary" onClick={handleRetry}>
            {t('analysisTasks.retry')}
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
        <Text>
          {t('analysisTasks.openInOpenCode')}
        </Text>
      </Modal>

      {/* Export Success Modal */}
      <Modal
        title={t('analysisTasks.workspaceExportSuccess')}
        open={exportSuccess}
        onCancel={() => setExportSuccess(false)}
        footer={[
          <Button key="check" icon={<CheckCircleOutlined />} onClick={handleCheckResult}>
            {t('analysisTasks.viewDiagnosisResult')}
          </Button>,
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
              {isPolling && <p style={{ color: '#888' }}>{t('analysisTasks.detectingResult')}</p>}
            </div>
          }
          type="success"
          showIcon
        />
      </Modal>

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

      {!showConversation ? (
        // Pre-diagnosis: show evidence and context input
        <Row gutter={24}>
          <Col span={16}>
            <Card
              title={t('diagnosis.selectedEvidence')}
              extra={<Text type="secondary">{selections.length} {t('diagnosis.evidence.selectedCount', { count: 0 })}</Text>}
            >
              {selections.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 40, color: '#888' }}>
                  {t('analysisTasks.noEvidenceSelected')}
                </div>
              ) : (
                <List
                  size="small"
                  dataSource={selections.slice(0, 10)}
                  renderItem={(sel, index) => (
                    <List.Item
                      key={`${sel.type}-${sel.group_key || sel.id || sel.cluster_index}-${index}`}
                      extra={
                        <Button
                          type="text"
                          size="small"
                          danger
                          icon={<DeleteOutlined />}
                          onClick={() => removeSelection(sel)}
                        />
                      }
                    >
                      <Space>
                        {getSelectionTypeTag(sel)}
                        <span>{getSelectionLabel(sel)}</span>
                      </Space>
                    </List.Item>
                  )}
                />
              )}
              {selections.length > 10 && (
                <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                  {t('diagnosis.evidence.moreEvidence', { count: selections.length - 10 })}
                </Text>
              )}
            </Card>

            <Card title={t('diagnosis.diagnosisSettings')} style={{ marginTop: 16 }}>
              <DiagnosisModeToggle value={mode} onChange={setMode} />
            </Card>
          </Col>

          <Col span={8}>
            <Card title={t('diagnosis.problemPhenomenon')}>
              <div style={{ marginBottom: 16 }}>
                <Text strong style={{ fontSize: 13 }}>{t('diagnosis.problemPhenomenon')}</Text>
                <textarea
                  placeholder={t('diagnosis.problemPhenomenonPlaceholder')}
                  value={userContext.phenomenon}
                  onChange={e => setUserContext({ ...userContext, phenomenon: e.target.value })}
                  style={{
                    width: '100%',
                    marginTop: 8,
                    padding: 8,
                    border: '1px solid #d9d9d9',
                    borderRadius: 4,
                    minHeight: 60,
                    resize: 'vertical',
                  }}
                />
              </div>
              <div style={{ marginBottom: 16 }}>
                <Text strong style={{ fontSize: 13 }}>{t('diagnosis.stackInfo')}</Text>
                <textarea
                  placeholder={t('diagnosis.stackInfoPlaceholder')}
                  value={userContext.stack}
                  onChange={e => setUserContext({ ...userContext, stack: e.target.value })}
                  style={{
                    width: '100%',
                    marginTop: 8,
                    padding: 8,
                    border: '1px solid #d9d9d9',
                    borderRadius: 4,
                    minHeight: 80,
                    fontFamily: 'monospace',
                    fontSize: 11,
                    resize: 'vertical',
                  }}
                />
              </div>
              <div>
                <Text strong style={{ fontSize: 13 }}>{t('diagnosis.keyParams')}</Text>
                <textarea
                  placeholder={t('diagnosis.keyParamsPlaceholder')}
                  value={userContext.params}
                  onChange={e => setUserContext({ ...userContext, params: e.target.value })}
                  style={{
                    width: '100%',
                    marginTop: 8,
                    padding: 8,
                    border: '1px solid #d9d9d9',
                    borderRadius: 4,
                    minHeight: 40,
                    resize: 'vertical',
                  }}
                />
              </div>
            </Card>

            <Space direction="vertical" style={{ width: '100%' }} size={12}>
              <Button
                type="primary"
                size="large"
                icon={<ThunderboltOutlined />}
                onClick={handleStartDiagnosis}
                loading={loading}
                disabled={!userContext.phenomenon.trim() && !userContext.stack.trim() && selections.length === 0}
                style={{ width: '100%', height: 48 }}
              >
                {t('diagnosis.startDiagnosis')}
              </Button>
              <Button
                size="large"
                icon={<FolderOpenOutlined />}
                onClick={handlePreviewPrompt}
                loading={loading}
                disabled={!userContext.phenomenon.trim() && !userContext.stack.trim() && selections.length === 0}
                style={{ width: '100%', height: 48 }}
              >
                {t('diagnosis.previewPrompt')}
              </Button>
            </Space>
          </Col>
        </Row>
      ) : (
        // In-diagnosis: show conversation
        <>
          <Row gutter={24}>
            <Col span={8}>
              <Card title={t('diagnosis.summary')} size="small">
                <div style={{ fontSize: 12 }}>
                  <div style={{ marginBottom: 8 }}>
                    <strong>{t('analysisTasks.evidenceLabel')}：</strong> {selections.length} {t('diagnosis.evidence.selectedCount', { count: 0 })}
                  </div>
                  {userContext.phenomenon && (
                    <div style={{ marginBottom: 8 }}>
                      <strong>{t('analysisTasks.phenomenonLabel')}：</strong>
                      <div style={{ color: '#666', marginTop: 4 }}>{userContext.phenomenon}</div>
                    </div>
                  )}
                  {userContext.stack && (
                    <div style={{ marginBottom: 8 }}>
                      <strong>{t('analysisTasks.stackLabel')}：</strong>
                      <pre style={{ fontSize: 10, color: '#666', marginTop: 4, maxHeight: 80, overflow: 'auto' }}>
                        {userContext.stack}
                      </pre>
                    </div>
                  )}
                  {userContext.params && (
                    <div style={{ marginBottom: 8 }}>
                      <strong>{t('analysisTasks.paramsLabel')}：</strong>
                      <div style={{ color: '#666', marginTop: 4 }}>{userContext.params}</div>
                    </div>
                  )}
                </div>
              </Card>
            </Col>
            <Col span={16}>
              <ConversationThread
                turns={turns}
                currentQuestion={currentQuestion}
                onContinue={handleContinue}
                onSkip={handleSkip}
                onEnd={handleEnd}
                loading={loading}
              />
            </Col>
          </Row>

          {diagnosisComplete && (
            <Alert
              message={t('analysisTasks.diagnosisComplete')}
              description={t('analysisTasks.diagnosisDisclaimer')}
              type="warning"
              showIcon
              style={{ marginTop: 16 }}
            />
          )}
        </>
      )}
    </div>
  );
}

export default DiagnosisStudioPage;
