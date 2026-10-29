export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  is_verified: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  repo_url?: string;
  repo_path?: string;
  branch: string;
  language?: string;
  framework?: string;
  status: string;
  is_analyzed: boolean;
  created_at: string;
}

export interface Analysis {
  id: string;
  project_id: string;
  status: string;
  analysis_type: string;
  result_json?: {
    summary?: string;
    files_analyzed?: number;
    issues_found?: number;
    security_score?: number;
    quality_score?: number;
  };
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  project_id?: string;
  model?: string;
  total_tokens: number;
  total_cost: number;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  model?: string;
  created_at: string;
}

export interface AgentInfo {
  name: string;
  type: string;
  status: 'active' | 'idle' | 'running' | 'error';
  description: string;
}

export interface JobInfo {
  id: string;
  name: string;
  job_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  project_id?: string;
  progress: number;
  error_message?: string;
  created_at: string;
}

export interface CostSummary {
  total_cost: number;
  total_tokens: number;
  by_provider: Record<string, number>;
  by_model: Record<string, number>;
  period: string;
  currency: string;
}

export interface ObservabilityMetrics {
  total_calls: number;
  tokens_used: number;
  average_latency_ms: number | null;
  error_rate: number;
  timestamp: string;
  cpu_usage?: number | null;
  memory_usage?: number | null;
  websocket_connections?: number;
  providers?: Record<string, number>;
}

export interface ProjectFileEntry {
  name: string;
  path: string;
  language: string;
  size: number;
  modified_at: string;
}

export interface ProjectFilesResponse {
  project_id: string;
  files: ProjectFileEntry[];
  stats: {
    total_files: number;
    total_lines: number;
    total_functions: number;
    total_classes: number;
    total_imports: number;
    language_counts: Record<string, number>;
    largest_files: Array<{ path: string; size: number }>;
  };
}

export interface KnowledgeGraphData {
  project_id: string;
  nodes: Array<{ id: string; label: string; type: string }>;
  edges: Array<{ source: string; target: string; relationship: string }>;
  stats: {
    total_files: number;
    total_functions: number;
    total_classes: number;
    total_imports: number;
  };
}

export interface MemoryEntry {
  id?: string;
  title: string;
  content: string;
  category?: string;
  created_at?: string;
}
