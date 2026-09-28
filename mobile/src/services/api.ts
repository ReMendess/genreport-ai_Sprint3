import { API_PREFIX } from '../config';
import type {
  ChatResponse,
  ConsentResponse,
  HealthResponse,
  MetricsResponse,
  ReprocessResponse,
  ReportResponse,
  StatusResponse,
} from '../types';

const DEFAULT_TIMEOUT_MS = 60000;

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST';
  body?: unknown;
  timeoutMs?: number;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, timeoutMs = DEFAULT_TIMEOUT_MS } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_PREFIX}${path}`, {
      method,
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });

    const text = await response.text();
    const payload: unknown = text.length > 0 ? JSON.parse(text) : null;

    if (!response.ok) {
      const detail =
        typeof payload === 'object' && payload !== null && 'detail' in payload
          ? String((payload as { detail: unknown }).detail)
          : response.statusText;
      throw new ApiError(response.status, detail);
    }

    return payload as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(0, 'Falha de conexão com a API. Verifique o endereço em config.ts.');
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  health: () => request<HealthResponse>('/health'),
  status: () => request<StatusResponse>('/status'),
  report: () => request<ReportResponse>('/report'),
  metrics: () => request<MetricsResponse>('/metrics'),
  chat: (question: string) =>
    request<ChatResponse>('/chat', { method: 'POST', body: { question } }),
  reprocess: () => request<ReprocessResponse>('/reprocess', { method: 'POST' }),
  getConsent: () => request<ConsentResponse>('/consent'),
  setConsent: (granted: boolean, policyVersion?: string) =>
    request<ConsentResponse>('/consent', {
      method: 'POST',
      body: { granted, policy_version: policyVersion },
    }),
};
