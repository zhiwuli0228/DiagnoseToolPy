import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

export interface TaskSummary {
  task_id: string;
  status: string | null;
  progress: Record<string, unknown>;
}

export interface TaskTextPayload {
  content: string | null;
}

export async function getTasks(): Promise<TaskSummary[]> {
  const response = await api.get<{ tasks: TaskSummary[] }>('/source/tasks');
  return response.data.tasks ?? [];
}

export async function getTaskProgress(taskId: string): Promise<Record<string, unknown> | null> {
  const response = await api.get<{ progress: Record<string, unknown> | null }>(
    `/source/task/${encodeURIComponent(taskId)}/progress`,
  );
  return response.data.progress;
}

export async function getTaskEvidencePack(taskId: string): Promise<string | null> {
  const response = await api.get<TaskTextPayload>(
    `/source/task/${encodeURIComponent(taskId)}/evidence-pack`,
  );
  return response.data.content;
}

export async function getTaskKeyLogs(taskId: string): Promise<string | null> {
  const response = await api.get<TaskTextPayload>(
    `/source/task/${encodeURIComponent(taskId)}/key-logs`,
  );
  return response.data.content;
}

export async function getTaskCaseDraft(taskId: string): Promise<string | null> {
  const response = await api.get<TaskTextPayload>(
    `/source/task/${encodeURIComponent(taskId)}/case-draft`,
  );
  return response.data.content;
}

export async function getTaskTestSuggestions(taskId: string): Promise<string | null> {
  const response = await api.get<TaskTextPayload>(
    `/source/task/${encodeURIComponent(taskId)}/test-suggestions`,
  );
  return response.data.content;
}
