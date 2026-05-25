import { Card, Row, Col } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  FileSearchOutlined,
  FolderOutlined,
  SettingOutlined,
} from '@ant-design/icons';

const { Meta } = Card;

function DashboardPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const cardData = [
    {
      title: t('dashboard.analysisTasksCard'),
      description: t('dashboard.analysisTasksDesc'),
      icon: <FileSearchOutlined style={{ fontSize: 48, color: '#1890ff' }} />,
      path: '/analysis',
    },
    {
      title: t('dashboard.casebaseCard'),
      description: t('dashboard.casebaseDesc'),
      icon: <FolderOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
      path: '/cases',
    },
    {
      title: t('dashboard.settingsCard'),
      description: t('dashboard.settingsDesc'),
      icon: <SettingOutlined style={{ fontSize: 48, color: '#faad14' }} />,
      path: '/settings',
    },
  ];

  return (
    <div>
      <h1>{t('dashboard.title')}</h1>
      <Row gutter={[16, 16]}>
        {cardData.map((card) => (
          <Col xs={24} sm={12} md={8} key={card.path}>
            <Card
              hoverable
              onClick={() => navigate(card.path)}
              style={{ textAlign: 'center' }}
            >
              <div style={{ marginBottom: 16 }}>{card.icon}</div>
              <Meta title={card.title} description={card.description} />
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}

export default DashboardPage;
