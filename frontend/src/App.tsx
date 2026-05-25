import { useLocation, useNavigate } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  FileSearchOutlined,
  FolderOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import AIDiagnosisButton from './components/AIDiagnosisButton';
import LanguageSwitcher from './components/LanguageSwitcher';
import { useDiagnosis } from './context/DiagnosisContext';
import DashboardPage from './pages/DashboardPage';
import AnalysisTasksPage from './pages/AnalysisTasksPage';
import CasebasePage from './pages/CasebasePage';
import AIDiagnosisPage from './pages/AIDiagnosisPage';
import DiagnosisStudioPage from './pages/DiagnosisStudioPage';
import SettingsPage from './pages/SettingsPage';

const { Sider, Content, Header } = Layout;

// Pages that need state preserved
const PRESERVE_STATE_PATHS = ['/analysis', '/diagnosis-studio', '/cases', '/diagnosis'];

// Wrapper that keeps component mounted but only renders when active
function TabContent({ path, children }: { path: string; children: React.ReactNode }) {
  const location = useLocation();
  const isActive = location.pathname === path || location.pathname.startsWith(path + '/');

  if (!isActive && PRESERVE_STATE_PATHS.includes(path)) {
    return (
      <div style={{ display: 'none', height: '100%' }}>
        {children}
      </div>
    );
  }

  if (isActive) {
    return <div style={{ height: '100%' }}>{children}</div>;
  }

  return null;
}

function App() {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const { selections, removeSelection, clearSelections, loading } = useDiagnosis();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: t('nav.dashboard'),
    },
    {
      key: '/analysis',
      icon: <FileSearchOutlined />,
      label: t('nav.analysisTasks'),
    },
    {
      key: '/cases',
      icon: <FolderOutlined />,
      label: t('nav.casebase'),
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: t('nav.settings'),
    },
  ];

  const currentPath = location.pathname;

  const selectedKey = menuItems.find(
    (item) => currentPath.startsWith(item.key) && item.key !== '/'
  )
    ? menuItems.find((item) => currentPath.startsWith(item.key) && item.key !== '/')!.key
    : currentPath === '/'
    ? '/'
    : '/';

  const handleDiagnose = () => {
    navigate('/diagnosis-studio?start=1');
  };

  const getBasePath = (path: string) => '/' + path.split('/')[1];

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
          <LanguageSwitcher />
          <AIDiagnosisButton
            selections={selections}
            onRemove={removeSelection}
            onClear={clearSelections}
            onDiagnose={handleDiagnose}
            loading={loading}
          />
        </Header>
        <Content style={{ margin: 24, height: 'calc(100vh - 112px)', overflow: 'auto' }}>
          {PRESERVE_STATE_PATHS.map(path => {
            const Component = {
              '/analysis': AnalysisTasksPage,
              '/diagnosis-studio': DiagnosisStudioPage,
              '/cases': CasebasePage,
              '/diagnosis': AIDiagnosisPage,
            }[path];

            return (
              <TabContent key={path} path={path}>
                {Component && <Component />}
              </TabContent>
            );
          })}
          {!PRESERVE_STATE_PATHS.includes(getBasePath(currentPath)) && (
            <div style={{ height: '100%' }}>
              {currentPath === '/' && <DashboardPage />}
              {currentPath === '/settings' && <SettingsPage />}
            </div>
          )}
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
