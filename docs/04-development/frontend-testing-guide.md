# Frontend Testing Guide

## Overview

Frontend tests use **Vitest** as the test runner, **@testing-library/react** for component testing, and **MSW (Mock Service Worker)** for API mocking.

## Technology Stack

| Tool | Purpose |
|------|---------|
| **Vitest** | Test runner with Vite integration |
| **@testing-library/react** | DOM behavior testing |
| **@testing-library/user-event** | Simulates real user interactions |
| **MSW** | HTTP-level API mocking (node mode) |
| **jsdom** | DOM environment for Node.js |

## Running Tests

```bash
# Run all tests once
npm run test

# Run tests in watch mode (HMR)
npm run test:watch

# Run tests with coverage report
npm run test:coverage
```

## Test Structure

```
frontend/src/
├── api/
│   ├── __tests__/
│   │   ├── client.test.ts
│   │   ├── caseApi.test.ts
│   │   ├── diagnosisApi.test.ts
│   │   └── sourceApi.test.ts
│   ├── client.ts
│   ├── caseApi.ts
│   ├── diagnosisApi.ts
│   └── sourceApi.ts
├── components/
│   └── layout/
│       └── __tests__/
│           └── AppLayout.test.tsx
├── pages/
│   └── __tests__/
│       ├── AIDiagnosisPage.test.tsx
│       ├── AnalysisTasksPage.test.tsx
│       ├── CasebasePage.test.tsx
│       ├── DashboardPage.test.tsx
│       └── SettingsPage.test.tsx
└── mocks/
    ├── handlers.ts      # MSW request handlers
    ├── server.ts        # MSW server setup
    ├── setup.ts         # Vitest + MSW lifecycle
    └── mockServiceWorker.js
```

## Writing Tests

### Component Tests

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import MyPage from '../MyPage';

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
};

describe('MyPage', () => {
  it('renders input and button', () => {
    renderWithRouter(<MyPage />);
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
  });

  it('shows result on success', async () => {
    const user = userEvent.setup();
    renderWithRouter(<MyPage />);
    await user.type(screen.getByPlaceholderText(/enter/i), 'test');
    await user.click(screen.getByRole('button', { name: /submit/i }));
    expect(await screen.findByText(/success/i)).toBeInTheDocument();
  });
});
```

### API Tests (with MSW)

```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { server } from '../../mocks/server';
import { http, HttpResponse } from 'msw';
import { myApiFunction } from '../myApi';

describe('myApi', () => {
  beforeEach(() => server.listen({ onUnhandledRequest: 'error' }));
  afterEach(() => server.resetHandlers());

  it('returns data on success', async () => {
    const result = await myApiFunction('param');
    expect(result.data).toBeDefined();
  });

  it('throws on HTTP error', async () => {
    server.use(
      http.get('/api/resource', () => HttpResponse.json({ detail: 'Not found' }, { status: 404 }))
    );
    await expect(myApiFunction('bad')).rejects.toThrow('Not found');
  });
});
```

### Mocking API Functions

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MyPage from '../MyPage';
import * as api from '../api/myApi';

vi.mock('../api/myApi');

describe('MyPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('shows data on success', async () => {
    vi.mocked(api.myApiFunction).mockResolvedValue({ data: 'test' });
    // ... render and interact
  });

  it('shows error on failure', async () => {
    vi.mocked(api.myApiFunction).mockRejectedValue(new Error('API Error'));
    // ... render and interact
  });
});
```

## Mock Strategy

### MSW (Preferred)

MSW intercepts HTTP requests at the network layer. Use this for testing API client functions and page components that call real APIs.

```typescript
// mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/health', () => HttpResponse.json({ status: 'ok' })),
  http.post('/api/diagnosis', async ({ request }) => {
    const body = await request.json() as { task_id: string };
    return HttpResponse.json({ case_id: body.task_id, diagnosis: 'ok' });
  }),
];
```

### vi.mock (For Component Logic)

Use `vi.mock()` when you need to completely replace an API module, or when testing components that import APIs directly.

```typescript
vi.mock('../api/myApi', () => ({
  myApiFunction: vi.fn().mockResolvedValue({ data: 'mocked' }),
}));
```

## Coverage Targets

| Module | Target |
|--------|--------|
| API modules | 80%+ |
| Page components | 60%+ (interaction logic priority) |
| Shared components | 70%+ |

## CI Integration

Tests run automatically on GitHub Actions for every push and PR affecting `frontend/**`.

```yaml
# .github/workflows/frontend-test.yml
on:
  push:
    paths: ['frontend/**']
  pull_request:
    paths: ['frontend/**']
```

Coverage reports are uploaded as build artifacts (retained 14 days).

## Troubleshooting

### "Not wrapped in act(...)"

Wrap async updates in `waitFor`:
```typescript
await waitFor(() => {
  expect(screen.getByText(/result/i)).toBeInTheDocument();
});
```

### MSW: "unhandled request"

Ensure `server.listen({ onUnhandledRequest: 'error' })` is set in `setup.ts`, and all endpoints used in tests have handlers defined.

### Ant Design components fail to render

Add `window.matchMedia` polyfill in `setup.ts`:
```typescript
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
```
