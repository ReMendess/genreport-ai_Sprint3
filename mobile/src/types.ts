/** Tipos dos contratos JSON da API (Etapa 1). */

export interface HealthResponse {
  status: string;
}

export interface StatusResponse {
  service: string;
  status: 'ok' | 'degraded' | 'error';
  started_at: string;
  uptime_seconds: number;
  report: {
    found: boolean;
    name?: string;
    size_bytes?: number;
    modified_at?: string;
    fingerprint?: string;
    error?: string;
  };
  index: {
    valid: boolean;
    files?: string[];
    modified_at?: string | null;
    embedding_model?: string;
    reason?: string;
  };
  consent: { required: boolean; granted: boolean };
  logging: {
    retention_days: number;
    app_log_bytes: number;
    audit_log_bytes: number;
  };
}

export interface AncestryItem {
  origin: string;
  percentage: number;
}

export interface RiskCard {
  condition: string;
  category: string;
  risk_level_id: string;
  risk_display: string;
  description: string;
  recommendations: string[];
  ai_summary: string | null;
  risk_color: string;
  risk_badge_color: string;
  risk_icon: string;
  risk_short_description: string;
}

export interface ReportResponse {
  report: {
    patient: { name: string | null; age: string | null; exam_date: string | null };
    summary: {
      increased: number;
      moderate: number;
      no_relevant_change: number;
      total: number;
    };
    findings: unknown[];
    risk_cards: RiskCard[];
    ancestry: AncestryItem[];
    has_ancestry: boolean;
  };
  disclaimers: string[];
}

export interface ChatResponse {
  answer: string;
  sources: string[];
  refused: boolean;
  refusal_reason: string | null;
  groundedness: number | null;
}

export interface ConsentResponse {
  required: boolean;
  granted: boolean;
  policy_version: string | null;
  current_policy_version: string;
  granted_at: string | null;
}

export interface ReprocessResponse {
  status: string;
  report_name: string;
  fingerprint: string;
}

export interface MetricsResponse {
  started_at: string;
  uptime_seconds: number;
  http: {
    requests_total: number;
    errors_client_total: number;
    errors_server_total: number;
    by_status: Record<string, number>;
    by_path: Record<
      string,
      { count: number; avg_ms: number; min_ms: number | null; max_ms: number; p95_ms: number | null }
    >;
  };
  chat: {
    turns_total: number;
    refusals_total: number;
    refusals_by_reason: Record<string, number>;
    groundedness_avg: number | null;
    avg_duration_ms: number | null;
  };
}
