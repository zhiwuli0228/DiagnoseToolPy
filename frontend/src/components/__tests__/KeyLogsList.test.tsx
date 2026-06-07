import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import KeyLogsList from '../KeyLogsList';

const mockSetSelections = vi.fn();
vi.mock('../../context/DiagnosisContext', () => ({
  useDiagnosis: () => ({ selections: [], setSelections: mockSetSelections }),
}));
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (_k: string, fallback?: string) => fallback ?? _k }),
}));

describe('KeyLogsList', () => {
  it('renders empty state when content is null', () => {
    render(<KeyLogsList taskId="t1" content={null} />);
    expect(screen.getByText(/no key logs in this task/i)).toBeInTheDocument();
  });

  it('renders key logs in a pre block when content is present', () => {
    render(<KeyLogsList taskId="t1" content={'[error] foo\n[warn] bar\n'} />);
    const pre = screen.getByTestId('key-logs-pre');
    expect(pre.textContent).toContain('[error] foo');
    expect(pre.textContent).toContain('[warn] bar');
  });

  it('adds all to evidence basket on click', () => {
    render(<KeyLogsList taskId="t1" content={'line1\nline2\n'} />);
    fireEvent.click(screen.getByRole('button', { name: /add all to evidence basket/i }));
    expect(mockSetSelections).toHaveBeenCalled();
    const updater = mockSetSelections.mock.calls[0][0];
    const next = updater([]);
    expect(next).toEqual([
      { type: 'log', id: 'key-logs:t1', group_key: 'key-logs:t1' },
    ]);
  });

  it('does not duplicate when basket already contains the key-logs item', () => {
    render(<KeyLogsList taskId="t1" content={'line1\n'} />);
    fireEvent.click(screen.getByRole('button', { name: /add all to evidence basket/i }));
    const updater = mockSetSelections.mock.calls[0][0];
    const next = updater([{ type: 'log', id: 'key-logs:t1', group_key: 'key-logs:t1' }]);
    expect(next).toEqual([{ type: 'log', id: 'key-logs:t1', group_key: 'key-logs:t1' }]);
  });
});
