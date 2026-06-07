import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import TaskOverview from '../TaskOverview';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (_k: string, fallback?: string) => fallback ?? _k }),
}));

describe('TaskOverview', () => {
  it('renders not-produced state when progress is null', () => {
    render(<TaskOverview taskId="t1" progress={null} />);
    expect(screen.getByText(/no progress recorded for this task/i)).toBeInTheDocument();
  });

  it('renders status, step, and updated_at when progress is full', () => {
    render(
      <TaskOverview
        taskId="t1"
        progress={{
          status: 'done',
          progress: 100,
          current_step: '分析完成',
          updated_at: '2026-06-01T10:00:00Z',
        }}
      />,
    );
    expect(screen.getByText('done')).toBeInTheDocument();
    expect(screen.getByText('分析完成')).toBeInTheDocument();
    expect(screen.getByText('2026-06-01T10:00:00Z')).toBeInTheDocument();
  });

  it('renders failure message in error color when present', () => {
    render(
      <TaskOverview
        taskId="t1"
        progress={{ status: 'failed', failure_message: 'kaboom' }}
      />,
    );
    expect(screen.getByText('kaboom')).toBeInTheDocument();
  });
});
