import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

const mockSetSelections = vi.fn();
const mockGetThreadResults = vi.fn();

vi.mock('../../api/diagnosisApi', () => ({
  getThreadResults: (...args: unknown[]) => mockGetThreadResults(...args),
}));
vi.mock('../../context/DiagnosisContext', () => ({
  useDiagnosis: () => ({ selections: [], setSelections: mockSetSelections }),
}));
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (_k: string, fallback?: string) => fallback ?? _k }),
}));

import ThreadResultsPanel from '../ThreadResultsPanel';

beforeEach(() => {
  mockSetSelections.mockReset();
  mockGetThreadResults.mockReset();
});

describe('ThreadResultsPanel', () => {
  it('shows empty state when total_threads is 0', async () => {
    mockGetThreadResults.mockResolvedValue({
      task_id: 't1',
      total_threads: 0,
      status_counts: { FULL: 0, PARTIAL: 0, RAW: 0 },
      threads: [],
    });
    render(<ThreadResultsPanel taskId="t1" />);
    await waitFor(() => {
      expect(screen.getByText(/no thread results found/i)).toBeInTheDocument();
    });
  });

  it('renders thread rows and supports add-all with dedupe', async () => {
    mockGetThreadResults.mockResolvedValue({
      task_id: 't1',
      total_threads: 2,
      status_counts: { FULL: 2, PARTIAL: 0, RAW: 0 },
      threads: [
        { thread_ref: 'r1', thread_name: 'worker-1', thread_state: 'RUNNABLE', parse_status: 'FULL', frame_count: 5, lock_count: 0, frames_summary: [] },
        { thread_ref: 'r2', thread_name: 'worker-2', thread_state: 'BLOCKED', parse_status: 'FULL', frame_count: 3, lock_count: 1, frames_summary: [] },
      ],
    });
    render(<ThreadResultsPanel taskId="t1" />);
    await waitFor(() => {
      expect(screen.getByText('worker-1')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /add all/i }));
    const updater = mockSetSelections.mock.calls[0][0];
    // Empty basket: both threads added.
    expect(updater([])).toEqual([
      { type: 'thread', id: 'r1' },
      { type: 'thread', id: 'r2' },
    ]);
    // Basket already has r1: only r2 is added.
    expect(updater([{ type: 'thread', id: 'r1' }])).toEqual([
      { type: 'thread', id: 'r1' },
      { type: 'thread', id: 'r2' },
    ]);
  });

  it('does not call API when taskId is empty', async () => {
    render(<ThreadResultsPanel taskId="" />);
    // Wait a tick; mock should not have been called.
    await new Promise(r => setTimeout(r, 10));
    expect(mockGetThreadResults).not.toHaveBeenCalled();
  });
});
