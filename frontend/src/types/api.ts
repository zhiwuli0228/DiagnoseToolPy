export interface SourcePathRequest {
  path: string;
}

export interface SourceCheckResponse {
  allowed: boolean;
  path: string;
  name: string;
}

export interface ScanResult {
  total_files: number;
  total_bytes: number;
  file_types: Record<string, number>;
  error_count: number;
  warn_count: number;
}

export interface HealthResponse {
  status: string;
  app: string;
}

export interface ApiError {
  detail: string;
}

export interface DiagnosisResponse {
  case_id: string;
  diagnosis: string;
}
