import { useLocation, useNavigate } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  FileSearchOutlined,
  FolderOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { lazy, Suspense } from 'react';
import { Spin } from 'antd';
import AIDiagnosisButton from './components/AIDiagnosisButton';
import LanguageSwitcher from './components/LanguageSwitcher';
import { useDiagnosis } from './context/DiagnosisContext';

const DashboardPage       = lazy(() => import('./pages/DashboardPage'));
const AnalysisTasksPage   = lazy(() => import('./pages/AnalysisTasksPage'));
const TaskDetailPage      = lazy(() => import('./pages/TaskDetailPage'));
const CasebasePage        = lazy(() => import('./pages/CasebasePage'));
const AIDiagnosisPage     = lazy(() => import('./pages/AIDiagnosisPage'));
const DiagnosisStudioPage = lazy(() => import('./pages/DiagnosisStudioPage'));
const SettingsPage        = lazy(() => import('./pages/SettingsPage'));

const { Sider, Content, Header } = Layout;

// Pages that need state preserved
const PRESERVE_STATE_PATHS = ['/analysis', '/diagnosis-studio', '/cases', '/diagnosis'];

// Wrapper that keeps component mounted but only renders when active
function TabContent({ path, children, currentPath }: { path: string; children: React.ReactNode; currentPath?: string }) {
  const location = useLocation();
  const pathForCheck = currentPath ?? location.pathname;
  const isActive = pathForCheck === path || pathForCheck.startsWith(path + '/');

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
    <Suspense
      fallback={
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
          <Spin size="large" />
        </div>
      }
    >
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
            <TabContent path="/analysis" currentPath={currentPath}>
              {currentPath === '/analysis' ? <AnalysisTasksPage /> : <TaskDetailPage />}
            </TabContent>
            {PRESERVE_STATE_PATHS.filter(p => p !== '/analysis').map(path => {
              const Component = {
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
    </Suspense>
  );
}

export default App;
