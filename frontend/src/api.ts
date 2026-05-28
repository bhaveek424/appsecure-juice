const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const ACTIVE_REVIEW_RUN_STATUSES = new Set([
  "Queued",
  "Zapping",
  "Triaging",
  "Ready For Skills",
  "Probing",
]);

export type FindingCounts = {
  critical: number;
  high: number;
  medium: number;
  low: number;
  informational: number;
};

export type ScanSummary = {
  id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  current_step: string;
  finding_counts: FindingCounts;
};

export type Finding = {
  id: string;
  source: string;
  title: string;
  category: string;
  severity: string;
  endpoint: string;
  description: string;
  remediation: string;
  confidence: string | null;
  evidence_excerpt: string | null;
  discovered_at: string;
};

export const SEVERITY_ORDER: Record<string, number> = {
  Critical: 0,
  High: 1,
  Medium: 2,
  Low: 3,
  Informational: 4,
};

export type ScanDetail = {
  id: string;
  status: string;
  progress: number | null;
  current_step: string;
  findings: Finding[];
  hypotheses: unknown[];
  skill_runs: unknown[];
};

export type BackendConfig = {
  target_application_url: string;
  llm_provider: string;
  llm_configured: boolean;
};

export type HealthResponse = {
  status: "ok" | "degraded";
  dependencies: {
    target_application: { reachable: boolean };
    zap: { reachable: boolean };
  };
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, init);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function fetchConfig(): Promise<BackendConfig> {
  return request<BackendConfig>("/api/config");
}

export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export function listScans(): Promise<ScanSummary[]> {
  return request<ScanSummary[]>("/api/scans");
}

export function getScan(scanId: string): Promise<ScanDetail> {
  return request<ScanDetail>(`/api/scans/${scanId}`);
}

export function createScan(): Promise<{ id: string }> {
  return request<{ id: string }>("/api/scans", {
    method: "POST",
  });
}

export function isActiveReviewRun(status: string): boolean {
  return ACTIVE_REVIEW_RUN_STATUSES.has(status);
}
