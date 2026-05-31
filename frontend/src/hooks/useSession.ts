import { useState, useEffect, useCallback } from 'react';

const SESSION_KEY = 'diagnose_session_id';

export interface UseSessionReturn {
  sessionId: string | null;
  isNewSession: boolean;
  createSession: () => string;
  clearSession: () => void;
}

export function useSession(): UseSessionReturn {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isNewSession, setIsNewSession] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(SESSION_KEY);
    if (stored) {
      setSessionId(stored);
      setIsNewSession(false);
    } else {
      const newId = crypto.randomUUID();
      localStorage.setItem(SESSION_KEY, newId);
      setSessionId(newId);
      setIsNewSession(true);
    }
  }, []);

  const createSession = useCallback(() => {
    const newId = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, newId);
    setSessionId(newId);
    setIsNewSession(true);
    return newId;
  }, []);

  const clearSession = useCallback(() => {
    localStorage.removeItem(SESSION_KEY);
    setSessionId(null);
    setIsNewSession(false);
  }, []);

  return {
    sessionId,
    isNewSession,
    createSession,
    clearSession,
  };
}
