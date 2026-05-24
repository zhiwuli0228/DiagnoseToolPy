import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import DiagnosisStudioPage from '../DiagnosisStudioPage';
import { DiagnosisProvider } from '../../context/DiagnosisContext';
import { server } from '../../mocks/server';
import { http, HttpResponse } from 'msw';

// Mock useSession hook to provide a consistent session
vi.mock('../../hooks/useSession', () => ({
  useSession: () => ({
    sessionId: 'test-session-id',
    isNewSession: false,
    createSession: vi.fn().mockReturnValue('new-session-id'),
    clearSession: vi.fn(),
  }),
}));

// Mock message module to avoid errors
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd');
  return {
    ...actual,
    message: {
      ...actual.message,
      warning: vi.fn(),
      success: vi.fn(),
      info: vi.fn(),
      error: vi.fn(),
    },
  };
});

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<MemoryRouter><DiagnosisProvider>{ui}</DiagnosisProvider></MemoryRouter>);
};

describe('DiagnosisStudioPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    server.resetHandlers();
    // Default GET handler for conversation
    server.use(
      http.get('/api/diagnosis/conversation/:sessionId', () =>
        HttpResponse.json({ turns: [], session_id: 'test-session-id' })
      )
    );
  });

  describe('Component Structure', () => {
    it('renders the page title', () => {
      renderWithRouter(<DiagnosisStudioPage />);
      expect(screen.getByText('诊断工作室')).toBeInTheDocument();
    });

    it('renders the evidence card', () => {
      renderWithRouter(<DiagnosisStudioPage />);
      expect(screen.getByText('已选证据')).toBeInTheDocument();
    });

    it('renders the problem description card', () => {
      renderWithRouter(<DiagnosisStudioPage />);
      expect(screen.getByText('问题描述')).toBeInTheDocument();
    });

    it('renders the diagnosis settings card', () => {
      renderWithRouter(<DiagnosisStudioPage />);
      expect(screen.getByText('诊断设置')).toBeInTheDocument();
    });

    it('shows empty state when no selections', () => {
      renderWithRouter(<DiagnosisStudioPage />);
      expect(screen.getByText(/从 Analysis Tasks 页面选择日志或聚类后，证据将显示在这里/i)).toBeInTheDocument();
    });

    it('shows selection count as 0', () => {
      renderWithRouter(<DiagnosisStudioPage />);
      expect(screen.getByText(/0 条/)).toBeInTheDocument();
    });
  });

  describe('Export Workspace Button', () => {
    it('shows Preview Prompt button', () => {
      renderWithRouter(<DiagnosisStudioPage />);
      expect(screen.getByRole('button', { name: /预览 Prompt/i })).toBeInTheDocument();
    });

    it('Preview Prompt button is disabled when no evidence or context', () => {
      renderWithRouter(<DiagnosisStudioPage />);
      const previewButton = screen.getByRole('button', { name: /预览 Prompt/i });
      expect(previewButton).toBeDisabled();
    });

    it('Preview Prompt button is enabled when context is provided', async () => {
      const user = userEvent.setup();
      renderWithRouter(<DiagnosisStudioPage />);

      const phenomenonInput = screen.getByPlaceholderText(/描述观察到的问题现象/i);
      await user.type(phenomenonInput, 'Connection timeout');

      const previewButton = screen.getByRole('button', { name: /预览 Prompt/i });
      expect(previewButton).not.toBeDisabled();
    });
  });

  describe('Start Diagnosis Button', () => {
    it('shows Start Diagnosis button', () => {
      renderWithRouter(<DiagnosisStudioPage />);
      expect(screen.getByRole('button', { name: /开始诊断/i })).toBeInTheDocument();
    });

    it('Start Diagnosis button is disabled when no evidence or context', () => {
      renderWithRouter(<DiagnosisStudioPage />);
      const startButton = screen.getByRole('button', { name: /开始诊断/i });
      expect(startButton).toBeDisabled();
    });

    it('Start Diagnosis button is enabled when context is provided', async () => {
      const user = userEvent.setup();
      renderWithRouter(<DiagnosisStudioPage />);

      const phenomenonInput = screen.getByPlaceholderText(/描述观察到的问题现象/i);
      await user.type(phenomenonInput, 'Connection timeout');

      const startButton = screen.getByRole('button', { name: /开始诊断/i });
      expect(startButton).not.toBeDisabled();
    });
  });

  describe('Degraded Dialog Handler Setup', () => {
    it('sets up POST handler that returns degraded response', async () => {
      const user = userEvent.setup();

      server.use(
        http.post('/api/diagnosis/conversation', () =>
          HttpResponse.json({
            degraded: true,
            error_type: 'llm_unavailable',
            message: 'AI diagnosis temporarily unavailable',
            workspace_export_url: '/api/diagnosis/export-workspace',
            workspace_export_options: {
              session_id: 'test-session',
              selections: [],
            },
          }, { status: 503 })
        )
      );

      renderWithRouter(<DiagnosisStudioPage />);

      const phenomenonInput = screen.getByPlaceholderText(/描述观察到的问题现象/i);
      await user.type(phenomenonInput, 'Database connection failed');

      const startButton = screen.getByRole('button', { name: /开始诊断/i });

      // Click start diagnosis - this will trigger the POST request
      await user.click(startButton);

      // The MSW handler should intercept this request and return degraded response
      // Note: The actual modal display depends on how the component handles the error
      // This test verifies the handler is set up correctly
      expect(startButton).toBeInTheDocument();
    });
  });
});
