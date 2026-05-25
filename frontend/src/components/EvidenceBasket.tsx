import { useState } from 'react';
import {
  Badge,
  Button,
  List,
  Popover,
  Tag,
  Spin,
  Empty,
  Space,
  Typography,
  Input,
  Divider,
  message,
} from 'antd';
import {
  ThunderboltOutlined,
  ClearOutlined,
  CloseOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { SelectionItem, UserContextModel } from '../types/api';
import DiagnosisModeToggle from './DiagnosisModeToggle';

const { TextArea } = Input;
const { Text } = Typography;

interface EvidenceBasketProps {
  selections: SelectionItem[];
  onRemove: (selection: SelectionItem) => void;
  onClear: () => void;
  onDiagnose: (context: UserContextModel) => void;
  loading: boolean;
}

export default function EvidenceBasket({
  selections,
  onRemove,
  onClear,
  onDiagnose,
  loading,
}: EvidenceBasketProps) {
  const { t } = useTranslation();
  const [showPreview, setShowPreview] = useState(false);
  const [phenomenon, setPhenomenon] = useState('');
  const [stack, setStack] = useState('');
  const [params, setParams] = useState('');
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
    setPhenomenon('');
    setStack('');
    setParams('');
  };

  const handleRemove = (sel: SelectionItem) => {
    onRemove(sel);
  };

  const handleDiagnose = () => {
    if (!phenomenon.trim() && !stack.trim() && selections.length === 0) {
      message.warning(t('diagnosis.pleaseSelectEvidenceOrFillInfo'));
      return;
    }
    onDiagnose({ phenomenon, stack, params });
  };

  const handleClose = () => {
    setShowPreview(false);
  };

  const renderPreviewContent = () => {
    if (loading) {
      return (
        <div style={{ textAlign: 'center', padding: 24 }}>
          <Spin tip={t('analysisTasks.generatingDiagnosis')} />
        </div>
      );
    }

    return (
      <div style={{ width: 380 }}>
        {/* Evidence List Section */}
        <div style={{ marginBottom: 16 }}>
          <Text strong style={{ fontSize: 13 }}>{t('evidenceBasket.selectedEvidence')} ({selections.length})</Text>
          {selections.length === 0 ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={t('evidenceBasket.noEvidence')}
              style={{ margin: '12px 0', fontSize: 12 }}
            />
          ) : (
            <List
              size="small"
              dataSource={selections.slice(0, 5)}
              style={{ maxHeight: 120, overflow: 'auto', marginTop: 8 }}
              renderItem={(sel, index) => (
                <List.Item
                  key={`${sel.type}-${sel.group_key || sel.id || sel.cluster_index}-${index}`}
                  style={{ padding: '4px 0' }}
                  actions={[
                    <Button
                      key="delete"
                      type="text"
                      size="small"
                      danger
                      icon={<CloseOutlined />}
                      onClick={() => handleRemove(sel)}
                    >
                      {t('diagnosis.evidence.delete')}
                    </Button>
                  ]}
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

        {/* User Context Section */}
        <div style={{ marginBottom: 12 }}>
          <Text strong style={{ fontSize: 13 }}>{t('evidenceBasket.additionalContext')}</Text>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 11, color: 'rgba(0,0,0,0.45)', display: 'block', marginBottom: 4 }}>
              {t('evidenceBasket.problemPhenomenon')}
            </label>
            <TextArea
              placeholder={t('diagnosis.problemPhenomenonPlaceholder')}
              value={phenomenon}
              onChange={e => setPhenomenon(e.target.value)}
              rows={2}
              autoSize={{ minRows: 1, maxRows: 3 }}
              style={{ fontSize: 12 }}
            />
          </div>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 11, color: 'rgba(0,0,0,0.45)', display: 'block', marginBottom: 4 }}>
              {t('evidenceBasket.stackInfo')}
            </label>
            <TextArea
              placeholder={t('diagnosis.stackInfoPlaceholder')}
              value={stack}
              onChange={e => setStack(e.target.value)}
              rows={2}
              autoSize={{ minRows: 1, maxRows: 3 }}
              style={{ fontSize: 11, fontFamily: 'monospace' }}
            />
          </div>
          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 11, color: 'rgba(0,0,0,0.45)', display: 'block', marginBottom: 4 }}>
              {t('evidenceBasket.keyParams')}
            </label>
            <TextArea
              placeholder={t('diagnosis.keyParamsPlaceholder')}
              value={params}
              onChange={e => setParams(e.target.value)}
              rows={1}
              autoSize={{ minRows: 1, maxRows: 2 }}
              style={{ fontSize: 12 }}
            />
          </div>
        </div>

        <Divider style={{ margin: '12px 0' }} />

        {/* Mode Toggle */}
        <DiagnosisModeToggle value={mode} onChange={setMode} />

        <Divider style={{ margin: '12px 0' }} />

        {/* Actions */}
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Button
            size="small"
            icon={<ClearOutlined />}
            onClick={handleClear}
            disabled={selections.length === 0 && !phenomenon && !stack && !params}
          >
            {t('evidenceBasket.clear')}
          </Button>
          <Button
            type="primary"
            size="small"
            icon={<ThunderboltOutlined />}
            onClick={handleDiagnose}
            disabled={!phenomenon.trim() && !stack.trim() && selections.length === 0}
          >
            {t('evidenceBasket.startDiagnosis')}
          </Button>
        </div>
      </div>
    );
  };

  const badgeContent = (
    <Badge count={selections.length} size="small" offset={[2, -2]}>
      <div
        onClick={() => setShowPreview(!showPreview)}
        style={{
          width: 48,
          height: 48,
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          boxShadow: '0 4px 20px rgba(102, 126, 234, 0.5), 0 0 40px rgba(102, 126, 234, 0.3)',
          transition: 'all 0.3s ease',
          border: '2px solid rgba(255,255,255,0.3)',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'scale(1.1)';
          e.currentTarget.style.boxShadow = '0 6px 30px rgba(102, 126, 234, 0.7), 0 0 60px rgba(102, 126, 234, 0.4)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'scale(1)';
          e.currentTarget.style.boxShadow = '0 4px 20px rgba(102, 126, 234, 0.5), 0 0 40px rgba(102, 126, 234, 0.3)';
        }}
      >
        <RobotOutlined style={{ fontSize: 22, color: '#fff' }} />
      </div>
    </Badge>
  );

  return (
    <div style={{ position: 'fixed', top: 80, right: 24, zIndex: 1000 }}>
      <Popover
        content={renderPreviewContent}
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space>
              <RobotOutlined style={{ color: '#667eea' }} />
              <span style={{ fontWeight: 500 }}>{t('evidenceBasket.title')}</span>
            </Space>
            <Button
              type="text"
              size="small"
              icon={<CloseOutlined />}
              onClick={handleClose}
            />
          </div>
        }
        trigger="click"
        open={showPreview}
        onOpenChange={setShowPreview}
        placement="bottomRight"
      >
        {badgeContent}
      </Popover>
    </div>
  );
}
