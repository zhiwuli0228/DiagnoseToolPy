import { useEffect, useState } from 'react';
import { Card, Descriptions, Empty, List, Button, Input, message, Spin, Alert, Typography } from 'antd';
import { DeleteOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { getConfig, patchPaths, type AppConfig } from '../api/configApi';

const { Text } = Typography;

function SettingsPage() {
  const { t } = useTranslation();
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newPath, setNewPath] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadConfig = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getConfig();
      setConfig(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const handleAddPath = async () => {
    const path = newPath.trim();
    if (!path) {
      message.error('Path cannot be empty');
      return;
    }
    if (config?.paths.allowed_input_roots.includes(path)) {
      message.error('Path already configured');
      return;
    }
    setSubmitting(true);
    try {
      await patchPaths({ action: 'add', path });
      setNewPath('');
      await loadConfig();
      message.success('Path added successfully');
    } catch (err) {
      message.error(err instanceof Error ? err.message : 'Failed to add path');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemovePath = async (path: string) => {
    if (config?.paths.allowed_input_roots.length === 1) {
      message.error('At least one root must remain');
      return;
    }
    setSubmitting(true);
    try {
      await patchPaths({ action: 'remove', path });
      await loadConfig();
      message.success('Path removed successfully');
    } catch (err) {
      message.error(err instanceof Error ? err.message : 'Failed to remove path');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <h1>{t('settings.title')}</h1>
        <Alert
          message="Failed to load configuration"
          description={error}
          type="error"
          showIcon
          action={<Button icon={<ReloadOutlined />} onClick={loadConfig}>Retry</Button>}
        />
      </div>
    );
  }

  if (!config) {
    return null;
  }

  return (
    <div>
      <h1>{t('settings.title')}</h1>

      <Card title="Application Configuration" style={{ marginBottom: 24 }}>
        <Descriptions column={1}>
          <Descriptions.Item label="Application Name">{config.app.name}</Descriptions.Item>
          <Descriptions.Item label="Version">{config.app.version}</Descriptions.Item>
          <Descriptions.Item label="Data Directory">{config.paths.data_dir}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="LLM Configuration" style={{ marginBottom: 24 }}>
        <Descriptions column={1}>
          <Descriptions.Item label="Enabled">
            <Text type={config.llm.enabled ? 'success' : 'secondary'}>
              {config.llm.enabled ? 'true' : 'false'}
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label="Model">{config.llm.model}</Descriptions.Item>
          <Descriptions.Item label="Base URL">{config.llm.base_url}</Descriptions.Item>
          <Descriptions.Item label="Timeout">{config.llm.timeout}s</Descriptions.Item>
        </Descriptions>
        <Text type="secondary" style={{ fontSize: 12 }}>
          LLM settings can be configured in config/app.yaml or via environment variables.
        </Text>
      </Card>

      <Card
        title="Allowed Input Roots"
        style={{ marginBottom: 24 }}
        extra={
          <Text type="secondary" style={{ fontSize: 12 }}>
            Paths can also be configured directly in config/app.yaml
          </Text>
        }
      >
        {config.paths.allowed_input_roots.length === 0 ? (
          <Empty description="No input roots configured." />
        ) : (
          <List
            size="small"
            bordered
            dataSource={config.paths.allowed_input_roots}
            renderItem={(path) => (
              <List.Item
                actions={[
                  <Button
                    key="remove"
                    type="text"
                    danger
                    size="small"
                    icon={<DeleteOutlined />}
                    onClick={() => handleRemovePath(path)}
                    disabled={submitting || config.paths.allowed_input_roots.length === 1}
                  >
                    Remove
                  </Button>
                ]}
              >
                {path}
              </List.Item>
            )}
          />
        )}
        <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
          <Input
            placeholder="Enter directory path"
            value={newPath}
            onChange={(e) => setNewPath(e.target.value)}
            onPressEnter={handleAddPath}
            disabled={submitting}
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAddPath}
            loading={submitting}
          >
            Add
          </Button>
        </div>
      </Card>
    </div>
  );
}

export default SettingsPage;
