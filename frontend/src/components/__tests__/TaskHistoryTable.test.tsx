import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

const mockGetTasks = vi.fn();
const mockNavigate = vi.fn();

vi.mock('../../api/taskApi', () => ({
  getTasks: (...args: unknown[]) => mockGetTasks(...args),
}));
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (_k: string, fallback?: string) => fallback ?? _k }),
}));

import TaskHistoryTable from '../TaskHistoryTable';

beforeEach(() => {
  mockGetTasks.mockReset();
  mockNavigate.mockReset();
});

describe('TaskHistoryTable', () => {
  it('shows empty state when list is empty', async () => {
    mockGetTasks.mockResolvedValue([]);
    render(<TaskHistoryTable />);
    await waitFor(() => {
      expect(screen.getByText(/no historical tasks/i)).toBeInTheDocument();
    });
  });

  it('renders rows and navigates on row click', async () => {
    mockGetTasks.mockResolvedValue([
      { task_id: 'abc-1', status: 'done', progress: { progress: 100, current_step: '分析完成', updated_at: '2026-06-01T10:00:00Z' } },
      { task_id: 'abc-2', status: 'scanning', progress: { progress: 50, current_step: '扫描中', updated_at: '2026-06-02T10:00:00Z' } },
    ]);
    render(<TaskHistoryTable />);
    await waitFor(() => {
      expect(screen.getByText('abc-1')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('abc-2'));
    expect(mockNavigate).toHaveBeenCalledWith('/analysis/abc-2');
  });

  it('shows error and triggers retry on failure', async () => {
    mockGetTasks.mockRejectedValueOnce(new Error('boom'));
    mockGetTasks.mockResolvedValueOnce([]);
    render(<TaskHistoryTable />);
    await waitFor(() => {
      expect(screen.getByText(/failed to load tasks/i)).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));
    await waitFor(() => {
      expect(mockGetTasks).toHaveBeenCalledTimes(2);
    });
  });
});
