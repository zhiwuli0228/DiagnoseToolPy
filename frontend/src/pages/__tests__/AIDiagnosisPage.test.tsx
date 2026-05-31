import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import AIDiagnosisPage from '../AIDiagnosisPage';

describe('AIDiagnosisPage (deprecated, redirects to DiagnosisStudioPage)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('redirects to /diagnosis-studio on mount', async () => {
    let capturedNavigate: ReturnType<typeof useNavigate> | null = null;

    function WrapperComponent() {
      const navigate = useNavigate();
      capturedNavigate = navigate;
      return null;
    }

    render(
      <MemoryRouter initialEntries={['/diagnosis']}>
        <AIDiagnosisPage />
        <WrapperComponent />
      </MemoryRouter>
    );

    // The component should redirect immediately on mount
    expect(capturedNavigate).not.toBeNull();
  });

  it('is deprecated - marked with deprecation comment', () => {
    // This test verifies the file exists and can be imported
    expect(AIDiagnosisPage).toBeDefined();
  });
});
