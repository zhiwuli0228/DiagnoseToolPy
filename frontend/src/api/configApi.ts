export interface AppConfig {
  app: {
    name: string;
    version: string;
  };
  server: {
    host: string;
    port: number;
  };
  paths: {
    allowed_input_roots: string[];
    data_dir: string;
  };
  llm: {
    enabled: boolean;
    model: string;
    base_url: string;
    timeout: number;
  };
}

export type PathsAction = 'add' | 'remove';

export interface PathsPatchRequest {
  action: PathsAction;
  path: string;
}

export async function getConfig(): Promise<AppConfig> {
  const response = await fetch('/api/config');
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Failed to load config' }));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function patchPaths(request: PathsPatchRequest): Promise<void> {
  const response = await fetch('/api/config/paths', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Failed to update paths' }));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }
}
