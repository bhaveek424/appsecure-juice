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

export const REVIEW_DISPOSITIONS = [
  "Unreviewed",
  "True Positive",
  "False Positive",
  "Duplicate",
  "Needs Investigation",
] as const;

export type ReviewDisposition = (typeof REVIEW_DISPOSITIONS)[number];

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
  disposition: ReviewDisposition;
};

export type ScannerFindingDetail = {
  alert: string;
  description: string;
  remediation: string;
  confidence: string | null;
  evidence_excerpt: string | null;
};

export type FindingDetail = Finding & {
  review_run_id: string;
  scanner: ScannerFindingDetail | null;
};

export const SEVERITY_ORDER: Record<string, number> = {
  Critical: 0,
  High: 1,
  Medium: 2,
  Low: 3,
  Informational: 4,
};

export type SourceObservation = {
  finding_id: string;
  title: string;
  severity: string;
};

export type Hypothesis = {
  id: string;
  title: string;
  rationale: string;
  recommended_skill_id: string;
  recommended_skill_name: string;
  priority: string;
  source_observations: SourceObservation[];
};

export type ScanDetail = {
  id: string;
  status: string;
  progress: number | null;
  current_step: string;
  findings: Finding[];
  hypotheses: Hypothesis[];
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

async function requestJson<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return request<T>(path, { ...init, headers });
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

export function getFindingDetail(
  scanId: string,
  findingId: string,
): Promise<FindingDetail> {
  return request<FindingDetail>(`/api/scans/${scanId}/findings/${findingId}`);
}

export function updateFindingDisposition(
  findingId: string,
  disposition: ReviewDisposition,
): Promise<{ id: string; disposition: ReviewDisposition }> {
  return requestJson(`/api/findings/${findingId}/disposition`, {
    method: "PATCH",
    body: JSON.stringify({ disposition }),
  });
}
