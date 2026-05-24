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

// Custom diagnosis from search/cluster results
export interface SelectionItem {
  type: 'group' | 'group_all' | 'log' | 'cluster';
  group_key?: string;
  id?: string;
  cluster_index?: number;
}

export interface CompressionOptions {
  include_stack: boolean;
  include_timeline: boolean;
  max_tokens: number;
}

export interface CustomDiagnosisRequest {
  cache_key: string;
  selections: SelectionItem[];
  options: CompressionOptions;
}

export interface CustomDiagnosisResponse {
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
  cache_key?: string;
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
  include_stack?: boolean;
}

// Cluster analysis types
export interface MatchedCase {
  case_id: string;
  score: number;
  summary: string;
  root_cause: string | null;
  solution: string | null;
}

export interface LogEvent {
  timestamp: string;
  level: string;
  thread: string;
  message: string;
  raw: string;
  file_path: string;
  line_no: number;
}

export interface CachedLogEntry {
  id: string;
  group_key: string;
  event: LogEvent;
  context_before: LogEvent[];
  context_after: LogEvent[];
}

export interface ClusterGroup {
  exception_class: string;
  count: number;
  sample_messages: string[];
  time_distribution: {
    peak_hour: string;
    range: string;
  };
  matched_cases: MatchedCase[];
  matched_lines?: CachedLogEntry[];
}

export interface ClusterStatusResponse {
  status: 'scanning' | 'aggregating' | 'matching' | 'done';
  progress: number;
  current_step: string;
  clusters: ClusterGroup[] | null;
}

export interface ClusterResponse {
  task_id: string;
}

// Conversation diagnosis types
export interface UserContextModel {
  phenomenon: string;
  stack: string;
  params: string;
}

export interface ConversationStartRequest {
  session_id?: string;
  user_context: UserContextModel;
  evidence_refs: string[];
  mode: 'user-priority' | 'log-priority';
  max_follow_up_rounds?: number;
}

export interface ConversationStartResponse {
  session_id: string;
  is_new_session: boolean;
  turn_id: string;
  state: 'waiting_for_input' | 'awaiting_user_reply' | 'diagnosis_complete' | 'skipped';
  ai_question?: string;
  ai_diagnosis?: string;
  disclaimer?: string;
}

export interface ConversationTurn {
  turn_id: string;
  user_context: UserContextModel;
  evidence_refs: string[];
  ai_question?: string;
  ai_diagnosis?: string;
  mode: string;
  timestamp: string;
}

export interface ConversationHistoryResponse {
  session_id: string;
  status: string;
  mode: string;
  turns: ConversationTurn[];
  current_state: string;
}

export interface ConversationContinueRequest {
  user_reply: string;
}

export interface SkipResponse {
  session_id: string;
  turn_id: string;
  state: string;
  ai_diagnosis: string;
  disclaimer: string;
}

export interface QualityScore {
  total: number;
  conversation_rounds: number;
  user_questions: number;
  completeness: number;
  ai_confidence: number;
  breakdown: Record<string, unknown>;
  recommendation: 'auto_promote' | 'draft';
}

export interface EndConversationResponse {
  session_id: string;
  quality_score?: QualityScore;
  case_id?: string;
  is_draft: boolean;
  diagnosis: string;
}

// Degraded response when LLM is unavailable
export interface DegradedResponse {
  degraded: true;
  error_type: string;
  message: string;
  workspace_export_url: string;
  workspace_export_options: Record<string, unknown>;
}

// Export workspace types
export interface ExportWorkspaceRequest {
  task_id?: string;
  session_id?: string;
  cache_key?: string;
  workspace_dir: string;
  user_context?: UserContextModel;
  selections?: SelectionItem[];
}

export interface ExportWorkspaceResponse {
  success: boolean;
  workspace_dir: string;
  files_written: string[];
  detection_hint?: string;
}
