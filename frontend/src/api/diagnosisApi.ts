import type { DiagnosisResponse, CustomDiagnosisRequest, CustomDiagnosisResponse, SelectionItem } from '../types/api';

export interface UserContextModel {
  phenomenon: string;
  stack: string;
  params: string;
}

export interface ExportWorkspaceRequest {
  task_id?: string;
  session_id?: string;
  cache_key?: string;
  workspace_dir: string;
  user_context?: UserContextModel;
  selections?: SelectionItem[];
}

export interface PreviewPromptRequest {
  task_id?: string;
  session_id?: string;
  cache_key?: string;
  user_context?: UserContextModel;
  selections?: SelectionItem[];
}

export interface PreviewPromptResponse {
  prompt: string;
}

export interface ExportWorkspaceResponse {
  success: boolean;
  workspace_dir: string;
  files_written: string[];
  detection_hint?: string;
}

export interface DegradedResponse {
  degraded: true;
  error_type: string;
  message: string;
  workspace_export_url: string;
  workspace_export_options: Record<string, unknown>;
}

export function isDegradedResponse(response: unknown): response is DegradedResponse {
  if (typeof response !== 'object' || response === null) return false;
  const obj = response as Record<string, unknown>;
  return (
    obj.degraded === true &&
    typeof obj.error_type === 'string' &&
    typeof obj.message === 'string' &&
    typeof obj.workspace_export_url === 'string'
  );
}

export async function diagnose(taskId: string): Promise<DiagnosisResponse | DegradedResponse> {
  const response = await fetch('/api/diagnosis', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task_id: taskId }),
  });
  const data = await response.json();
  if (!response.ok) {
    if (isDegradedResponse(data)) {
      return data;
    }
    throw new Error(data.detail || `HTTP ${response.status}`);
  }
  return data;
}

export async function diagnoseFromSearch(request: CustomDiagnosisRequest): Promise<CustomDiagnosisResponse | DegradedResponse> {
  const response = await fetch('/api/diagnosis/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  const data = await response.json();
  if (!response.ok) {
    if (isDegradedResponse(data)) {
      return data;
    }
    throw new Error(data.detail || `HTTP ${response.status}`);
  }
  return data;
}

export async function diagnoseFromCluster(request: CustomDiagnosisRequest): Promise<CustomDiagnosisResponse | DegradedResponse> {
  const response = await fetch('/api/diagnosis/cluster', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  const data = await response.json();
  if (!response.ok) {
    if (isDegradedResponse(data)) {
      return data;
    }
    throw new Error(data.detail || `HTTP ${response.status}`);
  }
  return data;
}

export async function exportWorkspace(request: ExportWorkspaceRequest): Promise<ExportWorkspaceResponse> {
  const response = await fetch('/api/diagnosis/export-workspace', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function previewPrompt(request: PreviewPromptRequest): Promise<PreviewPromptResponse> {
  const response = await fetch('/api/diagnosis/preview-prompt', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }
  return response.json();
}
