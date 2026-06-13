import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

const mockGetTaskMonitorSuggestions = vi.fn();

vi.mock('../../api/taskApi', () => ({
  getTaskMonitorSuggestions: (...args: unknown[]) => mockGetTaskMonitorSuggestions(...args),
}));
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (_k: string, fallback?: string) => fallback ?? _k }),
}));

import MonitorSuggestionsPanel from '../MonitorSuggestionsPanel';

beforeEach(() => {
  mockGetTaskMonitorSuggestions.mockReset();
});

const SAMPLE_MD = `## Metrics
### Monitor: JVM Heap Usage
- **Type**: jmx
- **Target**: java.lang:type=Memory/HeapMemoryUsage.used
- **Condition**: > 80% for 5min
- **Action**: page oncall

## Alerts
### Monitor: Error Rate Spike
- **Type**: prometheus-alertmanager
- **Target**: rate(http_errors_total[5m])
- **Condition**: 3x baseline
- **Action**: slack + ticket
`;

describe('MonitorSuggestionsPanel', () => {
  it('renders empty state when file is missing', async () => {
    mockGetTaskMonitorSuggestions.mockResolvedValue(null);
    render(<MonitorSuggestionsPanel taskId="t1" />);
    await waitFor(() => {
      expect(screen.getByText(/no monitor suggestions yet/i)).toBeInTheDocument();
    });
  });

  it('renders parsed monitor cards when file exists', async () => {
    mockGetTaskMonitorSuggestions.mockResolvedValue(SAMPLE_MD);
    render(<MonitorSuggestionsPanel taskId="t1" />);
    await waitFor(() => {
      expect(screen.getByText('JVM Heap Usage')).toBeInTheDocument();
    });
    expect(screen.getByText('jmx')).toBeInTheDocument();
    expect(screen.getByText(/HeapMemoryUsage\.used/)).toBeInTheDocument();
    expect(screen.getByText(/80% for 5min/)).toBeInTheDocument();
    expect(screen.getByText('Error Rate Spike')).toBeInTheDocument();
    expect(screen.getByText('prometheus-alertmanager')).toBeInTheDocument();
  });

  it('calls copy to clipboard when Copy button is clicked', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      configurable: true,
      writable: true,
    });

    mockGetTaskMonitorSuggestions.mockResolvedValue(SAMPLE_MD);
    render(<MonitorSuggestionsPanel taskId="t1" />);
    await waitFor(() => {
      expect(screen.getByText('JVM Heap Usage')).toBeInTheDocument();
    });

    const copyButtons = screen.getAllByTestId('copy-monitor-target');
    fireEvent.click(copyButtons[0]);
    expect(writeText).toHaveBeenCalled();
    const target = writeText.mock.calls[0][0];
    expect(target).toContain('HeapMemoryUsage');
  });

  it('shows error state on load failure', async () => {
    mockGetTaskMonitorSuggestions.mockRejectedValue(new Error('boom'));
    render(<MonitorSuggestionsPanel taskId="t1" />);
    await waitFor(() => {
      expect(screen.getByText('boom')).toBeInTheDocument();
    });
  });

  it('shows empty state when parsing finds no ### Monitor: headings', async () => {
    mockGetTaskMonitorSuggestions.mockResolvedValue('## Section\njust text');
    render(<MonitorSuggestionsPanel taskId="t1" />);
    await waitFor(() => {
      expect(screen.getByText(/empty or could not be parsed/i)).toBeInTheDocument();
    });
  });
});
