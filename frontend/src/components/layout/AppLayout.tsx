import { Layout, Menu } from 'antd';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  FileSearchOutlined,
  FolderOutlined,
  SettingOutlined,
  RobotOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import AIDiagnosisButton from '../AIDiagnosisButton';
import { useDiagnosis } from '../../context/DiagnosisContext';

const { Sider, Content, Header } = Layout;

function AppLayout() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { selections, removeSelection, clearSelections, loading } = useDiagnosis();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'nav.dashboard',
    },
    {
      key: '/analysis',
      icon: <FileSearchOutlined />,
      label: 'nav.analysisTasks',
    },
    {
      key: '/cases',
      icon: <FolderOutlined />,
      label: 'nav.casebase',
    },
    {
      key: '/diagnosis-studio',
      icon: <ThunderboltOutlined />,
      label: 'nav.diagnosisStudio',
    },
    {
      key: '/diagnosis',
      icon: <RobotOutlined />,
      label: 'nav.aiDiagnosis',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: 'nav.settings',
    },
  ].map(item => ({ ...item, label: t(item.label) }));

  const selectedKey = menuItems.find(
    (item) => location.pathname.startsWith(item.key) && item.key !== '/'
  )
    ? menuItems.find((item) => location.pathname.startsWith(item.key) && item.key !== '/')!.key
    : location.pathname === '/'
    ? '/'
    : '/';

  const handleDiagnose = () => {
    navigate('/diagnosis-studio?start=1');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider breakpoint="lg" collapsedWidth="0">
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: 18,
            fontWeight: 'bold',
          }}
        >
          DiagnoseToolPy
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: '#fff',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <AIDiagnosisButton
            selections={selections}
            onRemove={removeSelection}
            onClear={clearSelections}
            onDiagnose={handleDiagnose}
            loading={loading}
          />
        </Header>
        <Content style={{ margin: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}

export default AppLayout;
