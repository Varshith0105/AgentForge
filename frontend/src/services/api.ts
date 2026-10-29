import axios from 'axios';
import { User, TokenResponse, Project, Analysis, ChatSession, ChatMessage, AgentInfo, JobInfo, CostSummary, ObservabilityMetrics, KnowledgeGraphData, MemoryEntry, ProjectFilesResponse } from '../types/api';

const API_BASE = '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('agentforge_token');
  if (token && config.headers) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('agentforge_refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post<TokenResponse>(`${API_BASE}/auth/refresh`, { refresh_token: refreshToken });
          localStorage.setItem('agentforge_token', res.data.access_token);
          localStorage.setItem('agentforge_refresh_token', res.data.refresh_token);
          originalRequest.headers.Authorization = `Bearer ${res.data.access_token}`;
          return apiClient(originalRequest);
        } catch {
          localStorage.removeItem('agentforge_token');
          localStorage.removeItem('agentforge_refresh_token');
          localStorage.removeItem('agentforge_user');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export interface FileTreeNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  language?: string;
  size?: number;
  children?: FileTreeNode[];
}

export const api = {
  auth: {
    login: async (formData: URLSearchParams) => {
      const res = await axios.post<TokenResponse>(`${API_BASE}/auth/login`, formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      return res.data;
    },
    register: async (payload: { email: string; name: string; password: string; role?: string }) => {
      const res = await apiClient.post<User>('/auth/register', payload);
      return res.data;
    },
    me: async () => { const res = await apiClient.get<User>('/auth/me'); return res.data; },
    logout: async () => { const res = await apiClient.post('/auth/logout'); return res.data; },
  },
  projects: {
    list: async () => { const res = await apiClient.get<Project[]>('/projects'); return res.data; },
    create: async (payload: { name: string; description?: string; repo_url?: string; branch?: string }) => {
      const res = await apiClient.post<Project>('/projects', payload); return res.data;
    },
    get: async (id: string) => { const res = await apiClient.get<Project>(`/projects/${id}`); return res.data; },
    summary: async (id: string) => { const res = await apiClient.get(`/projects/${id}/summary`); return res.data; },
    files: async (id: string) => { const res = await apiClient.get<ProjectFilesResponse>(`/projects/${id}/files`); return res.data; },
    delete: async (id: string) => { const res = await apiClient.delete(`/projects/${id}`); return res.data; },
  },
  files: {
    getContent: async (projectId: string, filePath: string) => {
      const res = await apiClient.get<{ project_id: string; path: string; name: string; language: string; content: string; size: number; lines: number; }>(
        `/files/${projectId}/content`, { params: { path: filePath } }
      );
      return res.data;
    },
    getTree: async (projectId: string) => {
      const res = await apiClient.get<{ project_id: string; tree: FileTreeNode[]; total_files: number; }>(`/files/${projectId}/tree`);
      return res.data;
    },
  },
  github: {
    clone: async (payload: { repo_url: string; branch?: string; access_token?: string }) => {
      const res = await apiClient.post('/github/clone', payload); return res.data;
    },
    repoInfo: async (repoUrl: string) => {
      const res = await apiClient.get(`/github/repo-info?repo_url=${encodeURIComponent(repoUrl)}`); return res.data;
    },
  },
  git: {
    status: async (repoPath?: string) => {
      const query = repoPath ? `?repo_path=${encodeURIComponent(repoPath)}` : '';
      const res = await apiClient.get(`/git/status${query}`); return res.data;
    },
    commit: async (message: string, repoPath?: string) => {
      const res = await apiClient.post('/git/commit', { message, repo_path: repoPath }); return res.data;
    },
  },
  analysis: {
    start: async (projectId: string, analysisType = 'full') => {
      const res = await apiClient.post('/analysis/start', { project_id: projectId, analysis_type: analysisType }); return res.data;
    },
    status: async (analysisId: string) => {
      const res = await apiClient.get(`/analysis/status/${analysisId}`); return res.data;
    },
  },
  chats: {
    list: async () => { const res = await apiClient.get<ChatSession[]>('/chats'); return res.data; },
    create: async (payload: { project_id?: string; title?: string; model?: string }) => {
      const res = await apiClient.post<ChatSession>('/chats', payload); return res.data;
    },
    messages: async (chatId: string) => { const res = await apiClient.get<ChatMessage[]>(`/chats/${chatId}/messages`); return res.data; },
    sendMessage: async (chatId: string, payload: { content: string; stream?: boolean; model?: string; provider?: string }) => {
      return fetch(`${API_BASE}/chats/${chatId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('agentforge_token') || ''}` },
        body: JSON.stringify(payload),
      });
    },
  },
  agents: {
    status: async () => { const res = await apiClient.get<{ agents: AgentInfo[]; total: number; active: number }>('/agents/status'); return res.data; },
    run: async (payload: { project_id?: string; task: string; agent_type?: string }) => {
      const res = await apiClient.post('/agents/run', payload); return res.data;
    },
    runStream: (payload: { project_id?: string; task: string; agent_type?: string }) => {
      return fetch(`${API_BASE}/agents/run/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('agentforge_token') || ''}` },
        body: JSON.stringify(payload),
      });
    },
  },
  jobs: {
    list: async () => { const res = await apiClient.get<JobInfo[]>('/jobs'); return res.data; },
    cancel: async (jobId: string) => { const res = await apiClient.post(`/jobs/${jobId}/cancel`); return res.data; },
  },
  knowledgeEngine: {
    graph: async (projectId: string) => { const res = await apiClient.get<KnowledgeGraphData>(`/knowledge-engine/graph/${projectId}`); return res.data; },
    memory: async (projectId: string) => { const res = await apiClient.get<{ memories: MemoryEntry[] }>(`/knowledge-engine/memory/${projectId}`); return res.data; },
    index: async (projectId: string) => { const res = await apiClient.post(`/knowledge-engine/index/${projectId}`); return res.data; },
  },
  observability: {
    metrics: async () => { const res = await apiClient.get<ObservabilityMetrics>('/observability/metrics'); return res.data; },
  },
  costs: {
    summary: async () => { const res = await apiClient.get<CostSummary>('/costs/summary'); return res.data; },
  },
  settings: {
    getConfig: async () => { const res = await apiClient.get('/ai-os/config'); return res.data; },
    getProviders: async () => { const res = await apiClient.get<{ providers: string[]; configured: Record<string, boolean> }>('/ai-os/providers'); return res.data; },
    updateConfig: async (config: Record<string, unknown>) => { const res = await apiClient.put('/ai-os/config', config); return res.data; },
  },
  terminal: {
    execute: async (command: string, cwd?: string) => {
      const res = await apiClient.post<{ stdout: string; stderr: string; returncode: number }>('/terminal/execute', { command, cwd }); return res.data;
    },
  },
};
