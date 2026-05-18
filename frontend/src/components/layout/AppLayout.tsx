import { Layout, Menu } from 'antd';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  FileSearchOutlined,
  FolderOutlined,
  SettingOutlined,
  RobotOutlined,
} from '@ant-design/icons';

const { Sider, Content } = Layout;

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

  const selectedKey = menuItems.find(
    (item) => location.pathname.startsWith(item.key) && item.key !== '/'
  )
    ? menuItems.find((item) => location.pathname.startsWith(item.key) && item.key !== '/')!.key
    : location.pathname === '/'
    ? '/'
    : '/';

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
        <Content style={{ margin: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}

export default AppLayout;
