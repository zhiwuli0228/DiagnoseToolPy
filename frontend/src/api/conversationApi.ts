import type {
  ConversationStartRequest,
  ConversationStartResponse,
  ConversationHistoryResponse,
  ConversationContinueRequest,
  SkipResponse,
  EndConversationResponse,
} from '../types/api';

const SESSION_KEY = 'diagnose_session_id';

function getSessionId(): string | null {
  return localStorage.getItem(SESSION_KEY);
}

async function fetchWithSession(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const sessionId = getSessionId();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(sessionId ? { 'X-Session-ID': sessionId } : {}),
    ...(options.headers as Record<string, string> || {}),
  };

  return fetch(url, {
    ...options,
    headers,
  });
}

export async function startConversation(
  request: ConversationStartRequest
): Promise<ConversationStartResponse> {
  const sessionId = getSessionId();
  const requestWithSession = {
    ...request,
    session_id: request.session_id || sessionId,
  };

  const response = await fetch('/api/diagnosis/conversation', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(sessionId ? { 'X-Session-ID': sessionId } : {}),
    },
    body: JSON.stringify(requestWithSession),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
    // Handle degraded response (LLM unavailable)
    if (response.status === 503 && err.degraded) {
      // Save session_id even on degraded response - the session was created in backend
      const degradedOptions = err.workspace_export_options || {};
      if (degradedOptions.session_id) {
        localStorage.setItem(SESSION_KEY, degradedOptions.session_id);
      }
      const degradedError = new Error(err.message || 'AI diagnosis temporarily unavailable');
      (degradedError as any).degraded = true;
      (degradedError as any).error_type = err.error_type || 'llm_unavailable';
      (degradedError as any).workspace_export_url = err.workspace_export_url;
      (degradedError as any).workspace_export_options = degradedOptions;
      throw degradedError;
    }
    throw new Error(err.detail || `HTTP ${response.status}`);
  }

  const data = await response.json();

  // Update session ID if new session was created
  if (data.session_id && data.is_new_session) {
    localStorage.setItem(SESSION_KEY, data.session_id);
  }

  return data;
}

export async function getConversation(
  sessionId: string
): Promise<ConversationHistoryResponse> {
  const response = await fetchWithSession(
    `/api/diagnosis/conversation/${sessionId}`
  );

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
    // Handle degraded response (LLM unavailable)
    if (response.status === 503 && err.degraded) {
      const degradedError = new Error(err.message || 'AI diagnosis temporarily unavailable');
      (degradedError as any).degraded = true;
      (degradedError as any).workspace_export_url = err.workspace_export_url;
      (degradedError as any).workspace_export_options = err.workspace_export_options;
      throw degradedError;
    }
    throw new Error(err.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function continueConversation(
  sessionId: string,
  request: ConversationContinueRequest
): Promise<ConversationStartResponse> {
  const response = await fetchWithSession(
    `/api/diagnosis/conversation/${sessionId}/continue`,
    {
      method: 'POST',
      body: JSON.stringify(request),
    }
  );

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
    // Handle degraded response (LLM unavailable)
    if (response.status === 503 && err.degraded) {
      const degradedError = new Error(err.message || 'AI diagnosis temporarily unavailable');
      (degradedError as any).degraded = true;
      (degradedError as any).workspace_export_url = err.workspace_export_url;
      (degradedError as any).workspace_export_options = err.workspace_export_options;
      throw degradedError;
    }
    throw new Error(err.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function skipFollowUp(
  sessionId: string
): Promise<SkipResponse> {
  const response = await fetchWithSession(
    `/api/diagnosis/conversation/${sessionId}/skip`,
    { method: 'POST' }
  );

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
    // Handle degraded response (LLM unavailable)
    if (response.status === 503 && err.degraded) {
      const degradedError = new Error(err.message || 'AI diagnosis temporarily unavailable');
      (degradedError as any).degraded = true;
      (degradedError as any).workspace_export_url = err.workspace_export_url;
      (degradedError as any).workspace_export_options = err.workspace_export_options;
      throw degradedError;
    }
    throw new Error(err.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function endConversation(
  sessionId: string
): Promise<EndConversationResponse> {
  const response = await fetchWithSession(
    `/api/diagnosis/conversation/${sessionId}/end`,
    { method: 'POST' }
  );

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
    // Handle degraded response (LLM unavailable)
    if (response.status === 503 && err.degraded) {
      const degradedError = new Error(err.message || 'AI diagnosis temporarily unavailable');
      (degradedError as any).degraded = true;
      (degradedError as any).workspace_export_url = err.workspace_export_url;
      (degradedError as any).workspace_export_options = err.workspace_export_options;
      throw degradedError;
    }
    throw new Error(err.detail || `HTTP ${response.status}`);
  }

  return response.json();
}
