import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

const mockGetTaskTestSuggestions = vi.fn();

vi.mock('../../api/taskApi', () => ({
  getTaskTestSuggestions: (...args: unknown[]) => mockGetTaskTestSuggestions(...args),
}));
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (_k: string, fallback?: string) => fallback ?? _k }),
}));

import TestSuggestionsPanel from '../TestSuggestionsPanel';

beforeEach(() => {
  mockGetTaskTestSuggestions.mockReset();
});

const SAMPLE_MD = `## Reproduction
### Test: POST /api/users
- **Type**: curl
- **Goal**: Reproduce the 500 error on the users endpoint
- **Code**:
  \`\`\`sh
  curl -X POST http://localhost:8080/api/users -H 'Content-Type: application/json' -d '{"name":"test"}'
  \`\`\`
- **Expected**: HTTP 500 returned

## Verification
### Test: Check database
- **Type**: python
- **Goal**: Verify the user was not persisted
- **Code**:
  \`\`\`python
  from app.models import db, User
  assert User.query.filter_by(name='test').count() == 0
  \`\`\`
- **Expected**: No user with name "test" found
`;

describe('TestSuggestionsPanel', () => {
  it('renders empty state when file is missing', async () => {
    mockGetTaskTestSuggestions.mockResolvedValue(null);
    render(<TestSuggestionsPanel taskId="t1" />);
    await waitFor(() => {
      expect(screen.getByText(/no test suggestions yet/i)).toBeInTheDocument();
    });
  });

  it('renders parsed test cards when file exists', async () => {
    mockGetTaskTestSuggestions.mockResolvedValue(SAMPLE_MD);
    render(<TestSuggestionsPanel taskId="t1" />);
    await waitFor(() => {
      expect(screen.getByText('POST /api/users')).toBeInTheDocument();
    });
    expect(screen.getByText('curl')).toBeInTheDocument();
    expect(screen.getByText(/POST http:\/\/localhost:8080/)).toBeInTheDocument();
    expect(screen.getByText(/HTTP 500 returned/)).toBeInTheDocument();
    expect(screen.getByText('Check database')).toBeInTheDocument();
  });

  it('calls copy to clipboard when Copy button is clicked', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    // jsdom does not provide navigator.clipboard; mock it globally.
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      configurable: true,
      writable: true,
    });

    mockGetTaskTestSuggestions.mockResolvedValue(SAMPLE_MD);
    render(<TestSuggestionsPanel taskId="t1" />);
    await waitFor(() => {
      expect(screen.getByText('POST /api/users')).toBeInTheDocument();
    });

    const copyButtons = screen.getAllByTestId('copy-test-code');
    fireEvent.click(copyButtons[0]);
    expect(writeText).toHaveBeenCalled();
    const code = writeText.mock.calls[0][0];
    expect(code).toContain('curl');
    expect(code).toContain('/api/users');
  });

  it('shows error state on load failure', async () => {
    mockGetTaskTestSuggestions.mockRejectedValue(new Error('boom'));
    render(<TestSuggestionsPanel taskId="t1" />);
    await waitFor(() => {
      expect(screen.getByText('boom')).toBeInTheDocument();
    });
  });

  it('shows empty state when parsing finds no ### Test: headings', async () => {
    mockGetTaskTestSuggestions.mockResolvedValue('## Section\njust text');
    render(<TestSuggestionsPanel taskId="t1" />);
    await waitFor(() => {
      expect(screen.getByText(/empty or could not be parsed/i)).toBeInTheDocument();
    });
  });
});
