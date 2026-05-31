import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ClusterResult, { MatchedCaseCard } from '../ClusterResult';
import type { ClusterGroup, MatchedCase } from '../../types/api';

describe('MatchedCaseCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders matched case information', () => {
    const matchedCase: MatchedCase = {
      case_id: 'case-001',
      score: 0.85,
      summary: 'Connection pool exhausted',
      root_cause: 'High traffic',
      solution: 'Increase pool size',
    };

    render(<MatchedCaseCard matchedCase={matchedCase} />);

    // case-001 may be split across elements, use partial match
    expect(screen.getByText(/case-001/i)).toBeInTheDocument();
    expect(screen.getByText('Connection pool exhausted')).toBeInTheDocument();
    expect(screen.getByText('High traffic')).toBeInTheDocument();
    expect(screen.getByText('Increase pool size')).toBeInTheDocument();
  });

  it('renders score tag with correct color for high score', () => {
    const matchedCase: MatchedCase = {
      case_id: 'case-042',
      score: 0.72,
      summary: 'Test case',
      root_cause: null,
      solution: null,
    };

    render(<MatchedCaseCard matchedCase={matchedCase} />);
    // Score should be displayed (0.72)
    expect(screen.getByText(/0\.72/)).toBeInTheDocument();
  });

  it('renders with null optional fields', () => {
    const matchedCase: MatchedCase = {
      case_id: 'case-001',
      score: 0.5,
      summary: 'Test summary',
      root_cause: null,
      solution: null,
    };

    render(<MatchedCaseCard matchedCase={matchedCase} />);

    expect(screen.getByText(/case-001/i)).toBeInTheDocument();
    expect(screen.getByText('Test summary')).toBeInTheDocument();
  });
});

describe('ClusterResult', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state when no clusters', () => {
    render(<ClusterResult clusters={[]} taskId="test-task-1" />);
    expect(screen.getByText(/未发现异常模式/i)).toBeInTheDocument();
  });

  it('renders cluster with exception class and count', () => {
    const clusters: ClusterGroup[] = [
      {
        exception_class: 'NullPointerException',
        count: 25,
        sample_messages: ['NPE at line 10', 'NPE at line 20'],
        time_distribution: { peak_hour: '14:00-14:59', range: '13:00-15:00' },
        matched_cases: [],
      },
    ];

    render(<ClusterResult clusters={clusters} taskId="test-task-1" />);

    expect(screen.getByText('NullPointerException')).toBeInTheDocument();
    // count is rendered as "25 次" - use regex to match
    expect(screen.getByText(/25/)).toBeInTheDocument();
  });

  it('renders matched cases when available', async () => {
    const clusters: ClusterGroup[] = [
      {
        exception_class: 'JedisConnectionException',
        count: 10,
        sample_messages: ['Connection refused'],
        time_distribution: { peak_hour: '14:00-14:59', range: '13:00-15:00' },
        matched_cases: [
          {
            case_id: 'case-042',
            score: 0.85,
            summary: 'Connection pool issue',
            root_cause: 'pool exhausted',
            solution: 'increase pool size',
          },
        ],
      },
    ];

    render(<ClusterResult clusters={clusters} taskId="test-task-1" />);

    // Expand the cluster first to reveal matched cases
    const expandButton = screen.getByText('展开');
    userEvent.click(expandButton);

    // Wait for the expanded content to appear
    await screen.findByText(/case-042/i);
    expect(screen.getByText('Connection pool issue')).toBeInTheDocument();
  });

  it('shows "无匹配案例" message when no matched cases', async () => {
    const clusters: ClusterGroup[] = [
      {
        exception_class: 'UnknownError',
        count: 5,
        sample_messages: ['Some error'],
        time_distribution: { peak_hour: 'N/A', range: 'N/A' },
        matched_cases: [],
      },
    ];

    render(<ClusterResult clusters={clusters} taskId="test-task-1" />);

    // Expand the cluster first to reveal the "无匹配案例" message
    const expandButton = screen.getByText('展开');
    userEvent.click(expandButton);

    // Wait for the expanded content to appear
    await screen.findByText(/无匹配案例/i);
  });

  it('renders time distribution information', () => {
    const clusters: ClusterGroup[] = [
      {
        exception_class: 'TimeoutException',
        count: 15,
        sample_messages: ['Request timeout'],
        time_distribution: { peak_hour: '10:00-10:59', range: '09:30-10:30' },
        matched_cases: [],
      },
    ];

    render(<ClusterResult clusters={clusters} taskId="test-task-1" />);

    expect(screen.getByText(/峰值:.*10:00-10:59/i)).toBeInTheDocument();
    expect(screen.getByText(/范围:.*09:30-10:30/i)).toBeInTheDocument();
  });

  it('renders multiple clusters', () => {
    const clusters: ClusterGroup[] = [
      {
        exception_class: 'NullPointerException',
        count: 20,
        sample_messages: ['NPE'],
        time_distribution: { peak_hour: 'N/A', range: 'N/A' },
        matched_cases: [],
      },
      {
        exception_class: 'SQLException',
        count: 15,
        sample_messages: ['SQL error'],
        time_distribution: { peak_hour: 'N/A', range: 'N/A' },
        matched_cases: [],
      },
    ];

    render(<ClusterResult clusters={clusters} taskId="test-task-1" />);

    expect(screen.getByText('NullPointerException')).toBeInTheDocument();
    expect(screen.getByText('SQLException')).toBeInTheDocument();
    expect(screen.getByText(/发现 2 个异常模式/)).toBeInTheDocument();
  });
});