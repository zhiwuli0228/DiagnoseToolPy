import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { I18nextProvider } from 'react-i18next';
import App from './App';
import { DiagnosisProvider } from './context/DiagnosisContext';
import i18n from './i18n';

const theme = {
  token: {
    colorPrimary: '#1890ff',
  },
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <I18nextProvider i18n={i18n}>
      <ConfigProvider theme={theme}>
        <BrowserRouter>
          <DiagnosisProvider>
            <App />
          </DiagnosisProvider>
        </BrowserRouter>
      </ConfigProvider>
    </I18nextProvider>
  </React.StrictMode>
);
