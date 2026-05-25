import { useState } from 'react';
import {
  Badge,
  Button,
  Drawer,
  List,
  Tag,
  Space,
  Typography,
  Input,
  Divider,
  message,
} from 'antd';
import {
  ThunderboltOutlined,
  ClearOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { SelectionItem } from '../types/api';
import { useDiagnosis } from '../context/DiagnosisContext';
import DiagnosisModeToggle from './DiagnosisModeToggle';

const { TextArea } = Input;
const { Text } = Typography;

interface AIDiagnosisButtonProps {
  selections: SelectionItem[];
  onRemove: (selection: SelectionItem) => void;
  onClear: () => void;
  onDiagnose: () => void;
  loading: boolean;
}

export default function AIDiagnosisButton({
  selections,
  onRemove,
  onClear,
  onDiagnose,
  loading,
}: AIDiagnosisButtonProps) {
  const { t } = useTranslation();
  const { userContext, setUserContext, drawerOpen, setDrawerOpen } = useDiagnosis();
  const [mode, setMode] = useState<'user-priority' | 'log-priority'>('user-priority');

  const getSelectionLabel = (sel: SelectionItem) => {
    if (sel.type === 'group' || sel.type === 'group_all') {
      return sel.group_key || t('diagnosis.evidence.unknownGroup');
    }
    if (sel.type === 'log') {
      return `${t('diagnosis.evidence.logEntry')} (${sel.id?.slice(0, 8)}...)`;
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

  const handleClear = () => {
    onClear();
    setUserContext({ phenomenon: '', stack: '', params: '' });
  };

  const handleClose = () => {
    setDrawerOpen(false);
  };

  const handleDiagnose = () => {
    if (!userContext.phenomenon.trim() && !userContext.stack.trim() && selections.length === 0) {
      message.warning(t('diagnosis.pleaseSelectEvidenceOrFillInfo'));
      return;
    }
    setDrawerOpen(false);
    onDiagnose();
  };

  return (
    <>
      <Badge count={selections.length} size="small" offset={[5, -5]}>
        <Button
          type="primary"
          shape="circle"
          size="large"
          icon={<RobotOutlined style={{ fontSize: 18 }} />}
          onClick={() => setDrawerOpen(true)}
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            border: 'none',
            boxShadow: '0 4px 20px rgba(102, 126, 234, 0.5)',
          }}
        />
      </Badge>

      <Drawer
        title={
          <Space>
            <RobotOutlined style={{ color: '#667eea' }} />
            <span style={{ fontWeight: 500 }}>{t('diagnosis.aiAssistant')}</span>
          </Space>
        }
        placement="right"
        onClose={handleClose}
        open={drawerOpen}
        width={400}
        styles={{
          body: { padding: 16 },
          header: { borderBottom: '1px solid #f0f0f0' },
        }}
      >
        <div style={{ padding: '8px 0' }}>
          {/* Evidence List */}
          <div style={{ marginBottom: 16 }}>
            <Text strong style={{ fontSize: 13 }}>{t('diagnosis.selectedEvidence')} ({selections.length})</Text>
            {selections.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '12px 0', color: '#888' }}>
                {t('diagnosis.evidence.clickToAddEvidence')}
              </div>
            ) : (
              <List
                size="small"
                dataSource={selections.slice(0, 5)}
                style={{ maxHeight: 120, overflow: 'auto', marginTop: 8 }}
                renderItem={(sel, index) => (
                  <List.Item
                    key={`${sel.type}-${sel.group_key || sel.id || sel.cluster_index}-${index}`}
                    style={{ padding: '4px 0' }}
                    extra={
                      <Button
                        type="text"
                        size="small"
                        danger
                        onClick={() => onRemove(sel)}
                      >
                        {t('diagnosis.evidence.delete')}
                      </Button>
                    }
                  >
                    <Space size={4}>
                      {getSelectionTypeTag(sel)}
                      <span style={{ fontSize: 12 }}>{getSelectionLabel(sel)}</span>
                    </Space>
                  </List.Item>
                )}
              />
            )}
            {selections.length > 5 && (
              <Text type="secondary" style={{ fontSize: 11 }}>
                {t('diagnosis.evidence.moreEvidence', { count: selections.length - 5 })}
              </Text>
            )}
          </div>

          <Divider style={{ margin: '12px 0' }} />

          {/* User Context */}
          <div style={{ marginBottom: 12 }}>
            <Text strong style={{ fontSize: 13 }}>{t('diagnosis.additionalContext')}</Text>
            <div style={{ marginTop: 8 }}>
              <label style={{ fontSize: 11, color: 'rgba(0,0,0,0.45)', display: 'block', marginBottom: 4 }}>
                {t('diagnosis.problemPhenomenon')}
              </label>
              <TextArea
                placeholder={t('diagnosis.problemPhenomenonPlaceholder')}
                value={userContext.phenomenon}
                onChange={e => setUserContext({ ...userContext, phenomenon: e.target.value })}
                rows={2}
                autoSize={{ minRows: 1, maxRows: 3 }}
              />
            </div>
            <div style={{ marginTop: 8 }}>
              <label style={{ fontSize: 11, color: 'rgba(0,0,0,0.45)', display: 'block', marginBottom: 4 }}>
                {t('diagnosis.stackInfo')}
              </label>
              <TextArea
                placeholder={t('diagnosis.stackInfoPlaceholder')}
                value={userContext.stack}
                onChange={e => setUserContext({ ...userContext, stack: e.target.value })}
                rows={2}
                autoSize={{ minRows: 1, maxRows: 3 }}
                style={{ fontSize: 11, fontFamily: 'monospace' }}
              />
            </div>
            <div style={{ marginTop: 8 }}>
              <label style={{ fontSize: 11, color: 'rgba(0,0,0,0.45)', display: 'block', marginBottom: 4 }}>
                {t('diagnosis.keyParams')}
              </label>
              <TextArea
                placeholder={t('diagnosis.keyParamsPlaceholder')}
                value={userContext.params}
                onChange={e => setUserContext({ ...userContext, params: e.target.value })}
                rows={1}
                autoSize={{ minRows: 1, maxRows: 2 }}
              />
            </div>
          </div>

          <Divider style={{ margin: '12px 0' }} />

          <DiagnosisModeToggle value={mode} onChange={setMode} />

          <Divider style={{ margin: '12px 0' }} />

          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <Button
              size="small"
              icon={<ClearOutlined />}
              onClick={handleClear}
              disabled={selections.length === 0 && !userContext.phenomenon && !userContext.stack && !userContext.params}
            >
              {t('diagnosis.clear')}
            </Button>
            <Button
              type="primary"
              size="small"
              icon={<ThunderboltOutlined />}
              onClick={handleDiagnose}
              loading={loading}
              disabled={!userContext.phenomenon.trim() && !userContext.stack.trim() && selections.length === 0}
            >
              {t('diagnosis.startButton')}
            </Button>
          </div>
        </div>
      </Drawer>
    </>
  );
}
