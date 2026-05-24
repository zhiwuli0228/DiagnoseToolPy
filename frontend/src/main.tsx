import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import App from './App';
import { DiagnosisProvider } from './context/DiagnosisContext';

const theme = {
  token: {
    colorPrimary: '#1890ff',
  },
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider theme={theme}>
      <BrowserRouter>
        <DiagnosisProvider>
          <App />
        </DiagnosisProvider>
      </BrowserRouter>
    </ConfigProvider>
  </React.StrictMode>
);
