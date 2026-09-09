// frontend/src/services/api.ts
const API_BASE = '/api';

export interface DashboardData {
  stats: {
    total_assessments: number;
    running: number;
    completed: number;
    total_findings: number;
    critical_findings: number;
    high_findings: number;
    medium_findings: number;
    low_findings: number;
    total_evidence: number;
  };
  recent_assessments: AssessmentSummary[];
}

export interface AppSettings {
  app_name: string;
  app_version: string;
  app_env: string;
  tool_provider: string;
  llm_provider: string;
  llm_model: string;
  llm_base_url: string;
  llm_api_key_configured: boolean;
  hexstrike_base_url: string;
  hexstrike_api_key_configured: boolean;
  allowed_targets: string[];
  tool_timeout_seconds: number;
  llm_timeout_seconds: number;
  database_type: string;
  database_path: string;
  total_assessments: number;
  total_findings: number;
  total_evidence: number;
  execution_boundary: string;
  scope_constraint: string;
}

export interface ServiceHealth {
  backend: { status: string };
  hexstrike: { status: string; http_status?: number; error?: string };
  omniroute: { status: string; http_status?: number; error?: string; note?: string };
  tool_provider: string;
  llm_provider: string;
}

export interface AssessmentSummary {
  id: string;
  name: string;
  target: string;
  status: string;
  findings_count: number;
  validation_summary: string;
  execution_mode: string;
  created_at: string;
}

export interface AssessmentDetail {
  id: string;
  project_id: string;
  name: string;
  target: string;
  scope: string;
  description: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  recon_data: Record<string, any> | null;
  analysis_data: Record<string, any> | null;
  reasoning_data: Record<string, any> | null;
  findings_count: number;
  created_at: string;
}

export interface Evidence {
  id: string;
  assessment_id: string;
  finding_id: string | null;
  agent: string;
  action: string;
  evidence_type: string;
  content: string;
  source: string;
  source_type: string;
  timestamp: string;
}

export interface Finding {
  id: string;
  assessment_id: string;
  title: string;
  category: string;
  severity: string;
  confidence: number;
  endpoint: string;
  description: string;
  reasoning: string;
  recommendation: string;
  status: string;
  agent: string;
  finding_signature: string | null;
  evidence_data: any;
  evidence: Evidence[];
  created_at: string;
}

export interface ActivityItem {
  id: string;
  assessment_id: string;
  agent: string;
  message: string;
  log_type: string;
  timestamp: string;
}

export interface AgentInfo {
  name: string;
  role: string;
  description: string;
  status: string;
  last_action: string;
  actions_executed: number;
}

export interface ToolInfo {
  id: string;
  name: string;
  description: string;
  tool_type: string;
  safe: boolean;
}

export interface ReportData {
  id: string;
  assessment_id: string;
  report_type: string;
  content: string;
  findings_count: number;
  generated_at: string;
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || err.message || `API Error ${res.status}`);
  }
  const json = await res.json();
  return json.data ?? json;
}

export const api = {
  getDashboard: () => apiFetch<DashboardData>('/dashboard'),

  listAssessments: () => apiFetch<AssessmentSummary[]>('/assessments'),

  createAssessment: (data: { name: string; target: string; scope?: string; description?: string }) =>
    apiFetch<{ id: string; status: string }>('/assessments', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getAssessment: (id: string) => apiFetch<AssessmentDetail>(`/assessments/${id}`),

  startAssessment: (id: string) =>
    apiFetch<{ message: string }>(`/assessments/${id}/start`, { method: 'POST' }),

  getFindings: (assessmentId: string) => apiFetch<Finding[]>(`/assessments/${assessmentId}/findings`),

  getAllFindings: () => apiFetch<Finding[]>('/findings'),

  getActivity: (assessmentId: string) => apiFetch<ActivityItem[]>(`/assessments/${assessmentId}/activity`),

  getEvidence: (assessmentId: string) => apiFetch<Evidence[]>(`/assessments/${assessmentId}/evidence`),

  getAllEvidence: () => apiFetch<Evidence[]>('/evidence'),

  getReport: (assessmentId: string) => apiFetch<ReportData>(`/assessments/${assessmentId}/report`),

  getReportHtml: (assessmentId: string) => `${API_BASE}/assessments/${assessmentId}/report/html`,

  listAgents: () => apiFetch<AgentInfo[]>('/agents'),

  listTools: () => apiFetch<ToolInfo[]>('/tools'),

  getSettings: () => apiFetch<AppSettings>('/settings'),

  getSystemHealth: () => apiFetch<ServiceHealth>('/system/health'),

  checkHealth: async () => {
    try {
      const res = await fetch(`/health`);
      if (res.ok) {
        const data = await res.json();
        return data.status === 'healthy';
      }
      return false;
    } catch {
      return false;
    }
  },
};

export function createWebSocket(assessmentId: string): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return new WebSocket(`${protocol}//${window.location.host}/ws/${assessmentId}`);
}
