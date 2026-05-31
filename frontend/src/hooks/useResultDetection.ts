import { useState, useEffect, useCallback, useRef } from 'react';
import { message } from 'antd';
import { useTranslation } from 'react-i18next';

const POLLING_INTERVAL = 5000; // 5 seconds
const POLLING_TIMEOUT = 30 * 60 * 1000; // 30 minutes

interface UseResultDetectionOptions {
  workspaceDir: string | null;
  enabled?: boolean;
}

interface UseResultDetectionReturn {
  isPolling: boolean;
  lastCheck: Date | null;
  resultContent: string | null;
  setResultContent: (content: string | null) => void;
  startPolling: () => void;
  stopPolling: () => void;
  checkNow: () => Promise<string | null>;
  reset: () => void;
}

export function useResultDetection({
  workspaceDir,
  enabled = true,
}: UseResultDetectionOptions): UseResultDetectionReturn {
  const { t } = useTranslation();
  const [isPolling, setIsPolling] = useState(false);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const [resultContent, setResultContent] = useState<string | null>(null);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const startTimeRef = useRef<number | null>(null);

  // Persist polling state to localStorage
  const STORAGE_KEY = 'diagnose_result_polling';

  const savePollingState = useCallback((dir: string, startTime: number) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ workspaceDir: dir, startTime }));
    } catch {
      // Ignore localStorage errors
    }
  }, []);

  const loadPollingState = useCallback(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const { workspaceDir: dir, startTime } = JSON.parse(saved);
        return { dir, startTime };
      }
    } catch {
      // Ignore localStorage errors
    }
    return null;
  }, []);

  const clearPollingState = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // Ignore localStorage errors
    }
  }, []);

  const checkForResult = useCallback(async (): Promise<string | null> => {
    if (!workspaceDir) return null;

    try {
      // Use the backend API to check for result.md
      const response = await fetch(
        `/api/diagnosis/check-result?workspace_dir=${encodeURIComponent(workspaceDir)}`
      );

      if (response.ok) {
        const data = await response.json();
        if (data.exists && data.content) {
          return data.content;
        }
      }
    } catch {
      // Silently fail - polling continues
    }

    return null;
  }, [workspaceDir]);

  const checkNow = useCallback(async (): Promise<string | null> => {
    if (!workspaceDir) {
      message.warning(t('useResultDetection.pleaseExportWorkspaceFirst'));
      return null;
    }

    setLastCheck(new Date());
    const content = await checkForResult();

    if (content) {
      setResultContent(content);
      return content;
    }

    return null;
  }, [workspaceDir, checkForResult, t]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setIsPolling(false);
    clearPollingState();
  }, [clearPollingState]);

  const startPolling = useCallback(() => {
    if (!workspaceDir || !enabled) return;

    // Stop any existing polling
    stopPolling();

    setIsPolling(true);
    startTimeRef.current = Date.now();
    savePollingState(workspaceDir, startTimeRef.current);

    // Set up timeout
    timeoutRef.current = setTimeout(() => {
      stopPolling();
      message.warning(t('useResultDetection.resultDetectionTimeout'));
    }, POLLING_TIMEOUT);

    // Set up interval
    intervalRef.current = setInterval(async () => {
      const content = await checkForResult();
      if (content) {
        setResultContent(content);
        stopPolling();
        message.success(t('useResultDetection.detectedDiagnosisResult'));
      }
    }, POLLING_INTERVAL);

    // Also check immediately
    checkForResult().then(content => {
      if (content) {
        setResultContent(content);
        stopPolling();
        message.success(t('useResultDetection.detectedDiagnosisResult'));
      }
    });
  }, [workspaceDir, enabled, stopPolling, savePollingState, checkForResult, t]);

  const reset = useCallback(() => {
    stopPolling();
    setResultContent(null);
    setLastCheck(null);
  }, [stopPolling]);

  // Restore polling state on mount
  useEffect(() => {
    // Only restore if we have a valid workspaceDir
    if (!workspaceDir) {
      return;
    }

    const savedState = loadPollingState();
    if (savedState && savedState.dir === workspaceDir) {
      const elapsed = Date.now() - savedState.startTime;
      if (elapsed < POLLING_TIMEOUT) {
        // Resume polling
        startPolling();
      } else {
        // Timeout already expired
        clearPollingState();
      }
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceDir]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    isPolling,
    lastCheck,
    resultContent,
    setResultContent,
    startPolling,
    stopPolling,
    checkNow,
    reset,
  };
}
