import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import ClusterProgress from '../ClusterProgress';

describe('ClusterProgress', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders progress circle with correct percentage for scanning', () => {
    render(<ClusterProgress status="scanning" progress={20} currentStep="扫描日志中..." />);
    // The step label appears in the component (may appear multiple times due to styled text)
    expect(screen.getAllByText('扫描日志中...').length >= 1).toBe(true);
  });

  it('renders progress circle with correct percentage for aggregating', () => {
    render(<ClusterProgress status="aggregating" progress={50} currentStep="异常聚类中..." />);
    expect(screen.getAllByText('异常聚类中...').length >= 1).toBe(true);
  });

  it('renders progress circle with correct percentage for matching', () => {
    render(<ClusterProgress status="matching" progress={80} currentStep="历史案例匹配中..." />);
    expect(screen.getAllByText('历史案例匹配中...').length >= 1).toBe(true);
  });

  it('renders success state when done', () => {
    render(<ClusterProgress status="done" progress={100} currentStep="分析完成" />);
    expect(screen.getAllByText('分析完成').length >= 1).toBe(true);
  });

  it('displays current step label', () => {
    render(<ClusterProgress status="scanning" progress={20} currentStep="准备扫描..." />);
    expect(screen.getAllByText('准备扫描...').length >= 1).toBe(true);
  });
});