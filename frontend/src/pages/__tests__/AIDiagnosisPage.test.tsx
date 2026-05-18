import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import AIDiagnosisPage from '../AIDiagnosisPage';
import * as diagnosisApi from '../../api/diagnosisApi';

vi.mock('../../api/diagnosisApi');

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
};

describe('AIDiagnosisPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders input and button', () => {
    renderWithRouter(<AIDiagnosisPage />);
    expect(screen.getByPlaceholderText(/enter task id/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /diagnose/i })).toBeInTheDocument();
  });

  it('button is disabled when input is empty', () => {
    renderWithRouter(<AIDiagnosisPage />);
    expect(screen.getByRole('button', { name: /diagnose/i })).toBeDisabled();
  });

  it('button is enabled when input has value', async () => {
    const user = userEvent.setup();
    renderWithRouter(<AIDiagnosisPage />);
    await user.type(screen.getByPlaceholderText(/enter task id/i), 'task-001');
    expect(screen.getByRole('button', { name: /diagnose/i })).toBeEnabled();
  });

  it('shows diagnosis result on successful diagnosis', async () => {
    const user = userEvent.setup();
    vi.mocked(diagnosisApi.diagnose).mockResolvedValue({
      case_id: 'task-001',
      diagnosis: 'Database connection pool exhausted.',
    });

    renderWithRouter(<AIDiagnosisPage />);
    await user.type(screen.getByPlaceholderText(/enter task id/i), 'task-001');
    await user.click(screen.getByRole('button', { name: /diagnose/i }));

    await waitFor(() => {
      expect(screen.getByText(/database connection pool exhausted/i)).toBeInTheDocument();
    });
  });

  it('shows error alert on diagnosis failure', async () => {
    const user = userEvent.setup();
    vi.mocked(diagnosisApi.diagnose).mockRejectedValue(new Error('Task not found'));

    renderWithRouter(<AIDiagnosisPage />);
    await user.type(screen.getByPlaceholderText(/enter task id/i), 'bad-task');
    await user.click(screen.getByRole('button', { name: /diagnose/i }));

    await waitFor(() => {
      expect(screen.getByText(/diagnosis failed/i)).toBeInTheDocument();
      expect(screen.getByText(/task not found/i)).toBeInTheDocument();
    });
  });

  it('shows disclaimer warning about AI diagnosis', async () => {
    const user = userEvent.setup();
    vi.mocked(diagnosisApi.diagnose).mockResolvedValue({
      case_id: 'task-001',
      diagnosis: 'Memory leak detected.',
    });

    renderWithRouter(<AIDiagnosisPage />);
    await user.type(screen.getByPlaceholderText(/enter task id/i), 'task-001');
    await user.click(screen.getByRole('button', { name: /diagnose/i }));

    await waitFor(() => {
      expect(screen.getByText(/preliminary ai diagnosis/i)).toBeInTheDocument();
    });
  });
});
