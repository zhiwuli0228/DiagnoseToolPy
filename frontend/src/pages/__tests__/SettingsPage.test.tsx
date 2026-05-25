import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SettingsPage from '../SettingsPage';

const mockConfig = {
  app: { name: 'TestApp', version: '2.0.0' },
  server: { host: '0.0.0.0', port: 18080 },
  paths: {
    allowed_input_roots: ['data/input', 'data/uploads'],
    data_dir: 'data',
  },
  llm: { enabled: true, model: 'test-model', base_url: 'https://test.com', timeout: 30 },
};

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
};

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('displays app name and version from API', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockConfig), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );

    renderWithRouter(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText('TestApp')).toBeInTheDocument();
    });
    expect(screen.getByText('2.0.0')).toBeInTheDocument();
  });

  it('displays LLM configuration as read-only', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockConfig), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );

    renderWithRouter(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText('test-model')).toBeInTheDocument();
    });
    expect(screen.getByText('https://test.com')).toBeInTheDocument();
    expect(screen.getByText('30s')).toBeInTheDocument();
  });

  it('displays allowed input roots list', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockConfig), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );

    renderWithRouter(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText('data/input')).toBeInTheDocument();
    });
    expect(screen.getByText('data/uploads')).toBeInTheDocument();
  });

  it('shows error and retry button when API fails', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(
      new Response('Internal Server Error', { status: 500 })
    );

    renderWithRouter(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText(/Failed to load configuration/i)).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });
});
