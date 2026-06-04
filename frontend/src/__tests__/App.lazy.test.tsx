/// <reference types="vite/client" />

import { describe, it, expect } from 'vitest';
import { render, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import App from '../App';
import { DiagnosisProvider } from '../context/DiagnosisContext';
import { server } from '../mocks/server';

// Use Vite's raw glob import to read App.tsx source
const appSourceGlob = import.meta.glob('../App.tsx', { query: '?raw', import: 'default', eager: true });
const appSource = appSourceGlob['../App.tsx'] as string;

describe('App.tsx — route lazy loading', () => {
  it('uses React.lazy for all 6 page components', () => {
    // Count occurrences of `lazy(() => import(` — should be exactly 6
    const matches = appSource.match(/lazy\(\s*\(\)\s*=>\s*import\(/g) || [];
    expect(matches.length).toBe(6);
  });

  it('has no static page imports', () => {
    // Static imports look like: import DashboardPage from './pages/...'
    const staticPageImport = /import\s+\w*Page\w*\s+from\s+['"]\.\.?\/pages\//;
    expect(staticPageImport.test(appSource)).toBe(false);
  });

  it('wraps the layout in a Suspense boundary', () => {
    expect(/Suspense[\s\S]+fallback=/.test(appSource)).toBe(true);
  });
});

describe('App — Suspense fallback (render)', () => {
  it('shows Spin fallback during lazy route transition, then the page', async () => {
    // Mock /api/config so SettingsPage can render without fetch errors
    server.use(
      http.get('/api/config', () =>
        HttpResponse.json({
          app: { name: 'DiagnoseToolPy', version: '0.1.0' },
          llm: { enabled: false, model: '', base_url: '', timeout: 60 },
          paths: { data_dir: '/data', allowed_input_roots: ['/logs'] },
        }),
      ),
    );

    render(
      <MemoryRouter initialEntries={['/settings']}>
        <DiagnosisProvider>
          <App />
        </DiagnosisProvider>
      </MemoryRouter>,
    );

    // Spin is rendered as fallback while SettingsPage chunk loads
    const spin = document.querySelector('.ant-spin-lg, .ant-spin-spinning');
    expect(spin).toBeTruthy();

    // After the chunk loads, the Settings page renders its content inside .ant-layout
    await waitFor(
      () => {
        // The .ant-layout div is the root of App's layout — if it's present,
        // the Suspense boundary has resolved and the page content is visible
        const layoutEl = document.querySelector('.ant-layout');
        expect(layoutEl).toBeTruthy();
      },
      { timeout: 3000 },
    );
  });
});
