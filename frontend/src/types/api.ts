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

export interface LogSearchResult {
  file_path: string;
  line_no: number;
  timestamp: string;
  level: string;
  thread: string;
  logger: string;
  message: string;
  raw: string;
  matched_keyword: string[] | null;
}

export interface LogSearchResponse {
  matched_count: number;
  total_scanned_lines: number;
  files_scanned: number;
  results: LogSearchResult[];
  truncated: boolean;
  aggregated?: AggregatedGroup[];
}

export interface AggregatedGroup {
  key: string;
  count: number;
  sample_message: string;
  sample_timestamp: string;
  sample_thread: string;
  sample_level: string;
  file_path: string;
  matched_lines: LogSearchResult[];
}

export interface LogSearchParams {
  path: string;
  time_start?: string;
  time_end?: string;
  thread?: string;
  keywords?: string[];
  exclude_keywords?: string[];
  max_lines?: number;
  aggregate?: boolean;
  include_thread?: boolean;
  include_time?: boolean;
  message_only?: boolean;
}
