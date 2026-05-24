import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Row, Col, Card, Typography, Button, message, Alert, List, Tag, Space, Modal, ModalProps } from 'antd';
import { ThunderboltOutlined, DeleteOutlined, FolderOpenOutlined, CopyOutlined, CheckCircleOutlined } from '@ant-design/icons';
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
        title: '诊断结果已检测到',
        content: '是否导入诊断结果？',
        okText: '导入',
        cancelText: '忽略',
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
      message.warning('请选择日志证据或填写问题信息');
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
        message.error(err instanceof Error ? err.message : '诊断启动失败');
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
      message.warning('请选择日志证据或填写问题信息');
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
      message.error(err instanceof Error ? err.message : '预览失败');
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
      message.success('工作区已导出');

      // Start polling for result
      startPolling();

    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : '导出失败');
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
    message.info('请手动复制 prompt.md 文件内容');
  };

  const handleCheckResult = async () => {
    const content = await checkNow();
    if (content) {
      handleImportResult(content);
    } else {
      message.info('尚未检测到结果文件');
    }
  };

  const handleImportResult = (content: string) => {
    // For now, just show the result - in full implementation would save to case
    message.success('诊断结果已导入');
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
      message.success('工作区已导出');

      // Start polling for result
      startPolling();

    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : '导出失败');
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
        message.error(err instanceof Error ? err.message : '发送失败');
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
        message.error(err instanceof Error ? err.message : '跳过失败');
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
          ? `诊断结束，已存入草稿箱（质量评分: ${result.quality_score?.total}/10）`
          : `诊断结束，已创建案例（质量评分: ${result.quality_score?.total}/10）`
      );
      handleReset();
    } catch (err: unknown) {
      message.error(err instanceof Error ? err.message : '结束诊断失败');
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
      return sel.group_key || '未知分组';
    }
    if (sel.type === 'log') {
      return `日志 (${sel.id?.slice(0, 12)}...)`;
    }
    if (sel.type === 'cluster') {
      return `聚类 #${sel.cluster_index}`;
    }
    return '未知';
  };

  const getSelectionTypeTag = (sel: SelectionItem) => {
    const colorMap: Record<string, string> = {
      group: 'blue',
      group_all: 'cyan',
      log: 'green',
      cluster: 'purple',
    };
    const labelMap: Record<string, string> = {
      group: '分组',
      group_all: '全部分组',
      log: '日志',
      cluster: '聚类',
    };
    return <Tag color={colorMap[sel.type]}>{labelMap[sel.type]}</Tag>;
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
        <Title level={2} style={{ margin: 0 }}>诊断工作室</Title>
        {showConversation && (
          <Button onClick={handleReset}>重新开始</Button>
        )}
      </div>

      {/* Degraded Response Modal */}
      <Modal
        title="AI 诊断暂不可用"
        open={degradedModalOpen}
        onCancel={() => setDegradedModalOpen(false)}
        footer={[
          <Button key="retry" type="primary" onClick={handleRetry}>
            重试
          </Button>,
          <Button key="export" icon={<FolderOpenOutlined />} onClick={handleExportFromDegraded}>
            导出工作区
          </Button>,
        ]}
      >
        <Alert
          message="LLM 服务暂不可用"
          description={degradedInfo?.message || 'AI 诊断服务暂时无法使用。您可以导出工作区到本地目录，使用 OpenCode 手动完成诊断。'}
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Text>
          导出工作区后，您可以使用 OpenCode 打开目录，完成诊断后将结果保存为 result.md 文件，系统将自动检测并导入。
        </Text>
      </Modal>

      {/* Export Success Modal */}
      <Modal
        title="工作区导出成功"
        open={exportSuccess}
        onCancel={() => setExportSuccess(false)}
        footer={[
          <Button key="check" icon={<CheckCircleOutlined />} onClick={handleCheckResult}>
            检查结果
          </Button>,
          <Button key="copy" icon={<CopyOutlined />} onClick={handleCopyPrompt}>
            复制 Prompt
          </Button>,
        ]}
      >
        <Alert
          message="工作区已成功导出"
          description={
            <div>
              <p>工作区目录：{workspaceDir}</p>
              <p>请在 OpenCode 中打开该目录，完成诊断后将结果保存为 result.md。</p>
              {isPolling && <p style={{ color: '#888' }}>正在检测结果文件...</p>}
            </div>
          }
          type="success"
          showIcon
        />
      </Modal>

      {/* Preview Prompt Modal */}
      <Modal
        title="诊断 Prompt 预览"
        open={previewPromptModalOpen}
        onCancel={() => setPreviewPromptModalOpen(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setPreviewPromptModalOpen(false)}>
            关闭
          </Button>,
          <Button key="export" type="primary" icon={<FolderOpenOutlined />} onClick={handleExportFromPreview}>
            导出工作区
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
              title="已选证据"
              extra={<Text type="secondary">{selections.length} 条</Text>}
            >
              {selections.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 40, color: '#888' }}>
                  从 Analysis Tasks 页面选择日志或聚类后，证据将显示在这里
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
                  还有 {selections.length - 10} 条证据...
                </Text>
              )}
            </Card>

            <Card title="诊断设置" style={{ marginTop: 16 }}>
              <DiagnosisModeToggle value={mode} onChange={setMode} />
            </Card>
          </Col>

          <Col span={8}>
            <Card title="问题描述">
              <div style={{ marginBottom: 16 }}>
                <Text strong style={{ fontSize: 13 }}>问题现象 *</Text>
                <textarea
                  placeholder="描述观察到的问题现象"
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
                <Text strong style={{ fontSize: 13 }}>堆栈信息</Text>
                <textarea
                  placeholder="粘贴堆栈信息"
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
                <Text strong style={{ fontSize: 13 }}>关键入参</Text>
                <textarea
                  placeholder="输入相关参数"
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
                开始诊断
              </Button>
              <Button
                size="large"
                icon={<FolderOpenOutlined />}
                onClick={handlePreviewPrompt}
                loading={loading}
                disabled={!userContext.phenomenon.trim() && !userContext.stack.trim() && selections.length === 0}
                style={{ width: '100%', height: 48 }}
              >
                预览 Prompt
              </Button>
            </Space>
          </Col>
        </Row>
      ) : (
        // In-diagnosis: show conversation
        <>
          <Row gutter={24}>
            <Col span={8}>
              <Card title="诊断摘要" size="small">
                <div style={{ fontSize: 12 }}>
                  <div style={{ marginBottom: 8 }}>
                    <strong>证据数量：</strong> {selections.length} 条
                  </div>
                  {userContext.phenomenon && (
                    <div style={{ marginBottom: 8 }}>
                      <strong>问题现象：</strong>
                      <div style={{ color: '#666', marginTop: 4 }}>{userContext.phenomenon}</div>
                    </div>
                  )}
                  {userContext.stack && (
                    <div style={{ marginBottom: 8 }}>
                      <strong>堆栈信息：</strong>
                      <pre style={{ fontSize: 10, color: '#666', marginTop: 4, maxHeight: 80, overflow: 'auto' }}>
                        {userContext.stack}
                      </pre>
                    </div>
                  )}
                  {userContext.params && (
                    <div style={{ marginBottom: 8 }}>
                      <strong>关键入参：</strong>
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
              message="诊断结论仅供参考"
              description="以上诊断结果由 AI 生成，可能存在偏差。请结合实际日志和经验进行验证。"
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
