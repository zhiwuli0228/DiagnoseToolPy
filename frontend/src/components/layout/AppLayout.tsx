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
import AIDiagnosisButton from '../AIDiagnosisButton';
import { useDiagnosis } from '../../context/DiagnosisContext';

const { Sider, Content, Header } = Layout;

const menuItems = [
  {
    key: '/',
    icon: <DashboardOutlined />,
    label: 'Dashboard',
  },
  {
    key: '/analysis',
    icon: <FileSearchOutlined />,
    label: 'Analysis Tasks',
  },
  {
    key: '/cases',
    icon: <FolderOutlined />,
    label: 'Casebase',
  },
  {
    key: '/diagnosis-studio',
    icon: <ThunderboltOutlined />,
    label: '诊断工作室',
  },
  {
    key: '/diagnosis',
    icon: <RobotOutlined />,
    label: 'AI Diagnosis',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: 'Settings',
  },
];

function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { selections, removeSelection, clearSelections, loading } = useDiagnosis();

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
