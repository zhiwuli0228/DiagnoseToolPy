import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useResultDetection } from '../useResultDetection';
import { server } from '../../mocks/server';
import { http, HttpResponse } from 'msw';

// Mock message module
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd');
  return {
    ...actual,
    message: {
      ...actual.message,
      warning: vi.fn(),
      success: vi.fn(),
      info: vi.fn(),
    },
  };
});

describe('useResultDetection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock = {};
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => localStorageMock[key] || null,
      setItem: (key: string, value: string) => { localStorageMock[key] = value; },
      removeItem: (key: string) => { delete localStorageMock[key]; },
      clear: () => { localStorageMock = {}; },
    });
    server.resetHandlers();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  let localStorageMock: Record<string, string> = {};

  describe('initial state', () => {
    it('starts with polling false and no result content', () => {
      const { result } = renderHook(() => useResultDetection({
        workspaceDir: null,
        enabled: true,
      }));

      expect(result.current.isPolling).toBe(false);
      expect(result.current.resultContent).toBeNull();
      expect(result.current.lastCheck).toBeNull();
    });
  });

  describe('checkNow', () => {
    it('returns null when workspaceDir is null', async () => {
      const { result } = renderHook(() => useResultDetection({
        workspaceDir: null,
        enabled: true,
      }));

      const content = await result.current.checkNow();
      expect(content).toBeNull();
    });

    it('returns content when result.md exists and is valid', async () => {
      const validContent = '# Diagnosis Result\n\nDatabase timeout.';

      server.use(
        http.get('/api/diagnosis/check-result', () =>
          HttpResponse.json({
            exists: true,
            content: validContent,
            validation: {
              is_empty: false,
              is_too_short: false,
              is_prompt_template: false,
            },
          })
        )
      );

      const { result } = renderHook(() => useResultDetection({
        workspaceDir: '/test/workspace',
        enabled: true,
      }));

      await act(async () => {
        await result.current.checkNow();
      });

      expect(result.current.resultContent).toBe(validContent);
    });

    it('returns null when result.md does not exist', async () => {
      server.use(
        http.get('/api/diagnosis/check-result', () =>
          HttpResponse.json({ exists: false, content: null })
        )
      );

      const { result } = renderHook(() => useResultDetection({
        workspaceDir: '/test/workspace',
        enabled: true,
      }));

      await act(async () => {
        await result.current.checkNow();
      });

      expect(result.current.resultContent).toBeNull();
    });

    it('updates lastCheck timestamp on check', async () => {
      server.use(
        http.get('/api/diagnosis/check-result', () =>
          HttpResponse.json({ exists: false })
        )
      );

      const { result } = renderHook(() => useResultDetection({
        workspaceDir: '/test/workspace',
        enabled: true,
      }));

      expect(result.current.lastCheck).toBeNull();

      await act(async () => {
        await result.current.checkNow();
      });

      expect(result.current.lastCheck).not.toBeNull();
    });
  });

  describe('startPolling', () => {
    it('does nothing when workspaceDir is null', () => {
      const { result } = renderHook(() => useResultDetection({
        workspaceDir: null,
        enabled: true,
      }));

      act(() => {
        result.current.startPolling();
      });

      expect(result.current.isPolling).toBe(false);
    });

    it('sets isPolling to true when started', async () => {
      server.use(
        http.get('/api/diagnosis/check-result', () =>
          HttpResponse.json({ exists: false })
        )
      );

      const { result } = renderHook(() => useResultDetection({
        workspaceDir: '/test/workspace',
        enabled: true,
      }));

      act(() => {
        result.current.startPolling();
      });

      expect(result.current.isPolling).toBe(true);

      // Advance timers to let the initial check complete
      await act(async () => {
        await vi.runAllTimersAsync();
      });
    });

    it('stops existing polling before starting new one', async () => {
      let callCount = 0;
      server.use(
        http.get('/api/diagnosis/check-result', () => {
          callCount++;
          return HttpResponse.json({ exists: false });
        })
      );

      const { result } = renderHook(() => useResultDetection({
        workspaceDir: '/test/workspace',
        enabled: true,
      }));

      act(() => {
        result.current.startPolling();
      });

      act(() => {
        result.current.startPolling();
      });

      // Should have cleared first interval and started new one
      expect(result.current.isPolling).toBe(true);
    });
  });

  describe('stopPolling', () => {
    it('sets isPolling to false', async () => {
      server.use(
        http.get('/api/diagnosis/check-result', () =>
          HttpResponse.json({ exists: false })
        )
      );

      const { result } = renderHook(() => useResultDetection({
        workspaceDir: '/test/workspace',
        enabled: true,
      }));

      act(() => {
        result.current.startPolling();
      });

      expect(result.current.isPolling).toBe(true);

      act(() => {
        result.current.stopPolling();
      });

      expect(result.current.isPolling).toBe(false);
    });

    it('clears polling state from localStorage', async () => {
      server.use(
        http.get('/api/diagnosis/check-result', () =>
          HttpResponse.json({ exists: false })
        )
      );

      const { result } = renderHook(() => useResultDetection({
        workspaceDir: '/test/workspace',
        enabled: true,
      }));

      act(() => {
        result.current.startPolling();
      });

      expect(localStorageMock['diagnose_result_polling']).toBeDefined();

      act(() => {
        result.current.stopPolling();
      });

      expect(localStorageMock['diagnose_result_polling']).toBeUndefined();
    });
  });

  describe('reset', () => {
    it('clears result content and last check', async () => {
      server.use(
        http.get('/api/diagnosis/check-result', () =>
          HttpResponse.json({
            exists: true,
            content: '# Diagnosis',
            validation: { is_empty: false, is_too_short: false, is_prompt_template: false },
          })
        )
      );

      const { result } = renderHook(() => useResultDetection({
        workspaceDir: '/test/workspace',
        enabled: true,
      }));

      await act(async () => {
        await result.current.checkNow();
      });

      expect(result.current.resultContent).not.toBeNull();

      act(() => {
        result.current.reset();
      });

      expect(result.current.resultContent).toBeNull();
      expect(result.current.lastCheck).toBeNull();
    });
  });

  describe('result.md validation', () => {
    it('detects and returns valid result content', async () => {
      const validContent = '# Root Cause\n\nDatabase timeout.';
      server.use(
        http.get('/api/diagnosis/check-result', () =>
          HttpResponse.json({
            exists: true,
            content: validContent,
            validation: {
              is_empty: false,
              is_too_short: false,
              is_prompt_template: false,
            },
          })
        )
      );

      const { result } = renderHook(() => useResultDetection({
        workspaceDir: '/test/workspace',
        enabled: true,
      }));

      const content = await result.current.checkNow();
      expect(content).toBe(validContent);
    });

    it('handles empty result.md', async () => {
      server.use(
        http.get('/api/diagnosis/check-result', () =>
          HttpResponse.json({
            exists: true,
            content: null,
            validation: {
              is_empty: true,
              is_too_short: false,
              is_prompt_template: false,
            },
          })
        )
      );

      const { result } = renderHook(() => useResultDetection({
        workspaceDir: '/test/workspace',
        enabled: true,
      }));

      const content = await result.current.checkNow();
      expect(content).toBeNull();
    });

    it('handles prompt template result.md', async () => {
      server.use(
        http.get('/api/diagnosis/check-result', () =>
          HttpResponse.json({
            exists: true,
            content: null,
            validation: {
              is_empty: false,
              is_too_short: false,
              is_prompt_template: true,
            },
          })
        )
      );

      const { result } = renderHook(() => useResultDetection({
        workspaceDir: '/test/workspace',
        enabled: true,
      }));

      const content = await result.current.checkNow();
      expect(content).toBeNull();
    });

    it('handles too short content', async () => {
      server.use(
        http.get('/api/diagnosis/check-result', () =>
          HttpResponse.json({
            exists: true,
            content: null,
            validation: {
              is_empty: false,
              is_too_short: true,
              is_prompt_template: false,
            },
          })
        )
      );

      const { result } = renderHook(() => useResultDetection({
        workspaceDir: '/test/workspace',
        enabled: true,
      }));

      const content = await result.current.checkNow();
      expect(content).toBeNull();
    });
  });
});
