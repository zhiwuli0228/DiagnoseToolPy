import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useSession } from '../useSession';

const SESSION_KEY = 'diagnose_session_id';

describe('useSession', () => {
  let localStorageMock: Record<string, string>;

  beforeEach(() => {
    localStorageMock = {};
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => localStorageMock[key] || null,
      setItem: (key: string, value: string) => { localStorageMock[key] = value; },
      removeItem: (key: string) => { delete localStorageMock[key]; },
      clear: () => { localStorageMock = {}; },
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('creates a new session if none exists', () => {
    const { result } = renderHook(() => useSession());
    expect(result.current.sessionId).toBeTruthy();
    expect(result.current.sessionId).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
    );
    expect(result.current.isNewSession).toBe(true);
  });

  it('retrieves existing session from localStorage', () => {
    const existingSessionId = 'existing-session-123';
    localStorageMock[SESSION_KEY] = existingSessionId;

    const { result } = renderHook(() => useSession());
    expect(result.current.sessionId).toBe(existingSessionId);
    expect(result.current.isNewSession).toBe(false);
  });

  it('createSession generates new UUID and updates localStorage', () => {
    const { result } = renderHook(() => useSession());
    const initialSessionId = result.current.sessionId;

    let newSessionId: string = '';
    act(() => {
      newSessionId = result.current.createSession();
    });

    expect(result.current.sessionId).not.toBe(initialSessionId);
    expect(result.current.sessionId).toBe(newSessionId);
    expect(localStorageMock[SESSION_KEY]).toBe(newSessionId);
    expect(result.current.isNewSession).toBe(true);
  });

  it('clearSession removes session from localStorage', () => {
    const existingSessionId = 'existing-session-456';
    localStorageMock[SESSION_KEY] = existingSessionId;

    const { result } = renderHook(() => useSession());
    expect(result.current.sessionId).toBe(existingSessionId);

    act(() => {
      result.current.clearSession();
    });

    expect(result.current.sessionId).toBeNull();
    expect(result.current.isNewSession).toBe(false);
    expect(localStorageMock[SESSION_KEY]).toBeUndefined();
  });

  it('createSession returns the new session ID', () => {
    const { result } = renderHook(() => useSession());

    let returnedId: string = '';
    act(() => {
      returnedId = result.current.createSession();
    });

    expect(returnedId).toBe(result.current.sessionId);
    expect(returnedId).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
    );
  });
});
