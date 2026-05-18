import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import AnalysisTasksPage from '../AnalysisTasksPage';
import * as sourceApi from '../../api/sourceApi';

vi.mock('../../api/sourceApi');

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
};

describe('AnalysisTasksPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders path input and both buttons', () => {
    renderWithRouter(<AnalysisTasksPage />);
    expect(screen.getByPlaceholderText(/enter directory path/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /check directory/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /scan directory/i })).toBeInTheDocument();
  });

  it('scan button is disabled when input is empty', () => {
    renderWithRouter(<AnalysisTasksPage />);
    expect(screen.getByRole('button', { name: /scan directory/i })).toBeDisabled();
  });

  it('shows success result when directory is allowed', async () => {
    const user = userEvent.setup();
    vi.mocked(sourceApi.checkSourceDirectory).mockResolvedValue({
      allowed: true,
      path: '/data/logs',
      name: 'logs',
    });

    renderWithRouter(<AnalysisTasksPage />);
    await user.type(screen.getByPlaceholderText(/enter directory path/i), '/data/logs');
    await user.click(screen.getByRole('button', { name: /check directory/i }));

    await waitFor(() => {
      expect(screen.getByText(/directory is allowed/i)).toBeInTheDocument();
    });
  });

  it('shows scan result statistics', async () => {
    const user = userEvent.setup();
    vi.mocked(sourceApi.scanSourceDirectory).mockResolvedValue({
      total_files: 42,
      total_bytes: 5242880,
      file_types: { '.log': 30, '.txt': 10, '.gz': 2 },
      error_count: 3,
      warn_count: 7,
    });

    renderWithRouter(<AnalysisTasksPage />);
    await user.type(screen.getByPlaceholderText(/enter directory path/i), '/data/logs');
    await user.click(screen.getByRole('button', { name: /scan directory/i }));

    await waitFor(() => {
      expect(screen.getByText('42')).toBeInTheDocument();
      // total_bytes is formatted as MB by AntD Statistic formatter
      expect(screen.getByText(/5\.00 MB/i)).toBeInTheDocument();
    });
  });

  it('shows error alert on check failure', async () => {
    const user = userEvent.setup();
    vi.mocked(sourceApi.checkSourceDirectory).mockRejectedValue({
      response: { data: { detail: 'Path not allowed' } },
    });

    renderWithRouter(<AnalysisTasksPage />);
    await user.type(screen.getByPlaceholderText(/enter directory path/i), '/forbidden');
    await user.click(screen.getByRole('button', { name: /check directory/i }));

    await waitFor(() => {
      expect(screen.getByText(/path not allowed/i)).toBeInTheDocument();
    });
  });
});
