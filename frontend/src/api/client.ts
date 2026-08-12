/**
 * API Client central (UI 4.0)
 *
 * - Base URL por variável de ambiente (VITE_API_URL)
 * - Timeout configurável (default 10s)
 * - Retry simples (default 2 tentativas, backoff 300ms)
 * - Tratamento global de erro estruturado
 * - Tipos TypeScript para respostas da API real
 *
 * Docs: https://edysiem.local/api-docs
 */

// ─────────────────────────────────────────────────────────────────────────────
// Types — alinhados aos schemas Pydantic do backend (src/edysiem/api/schemas.py)
// ─────────────────────────────────────────────────────────────────────────────

export type Severity = "critical" | "high" | "medium" | "low" | "info";

export type HealthStatus = "healthy" | "degraded" | "critical";

export type ComponentStatus = "online" | "degraded" | "offline" | "error";

// Health
export interface HealthComponent {
  status: ComponentStatus;
  details?: Record<string, unknown>;
}
export interface HealthResponse {
  status: HealthStatus;
  version: string;
  environment: string;
  components: Record<string, HealthComponent>;
}

// Version
export interface VersionResponse {
  name: string;
  version: string;
  environment: string;
}

// Metrics
export interface MetricsResponse {
  metrics: Record<string, number>;
  components: Record<string, unknown>;
}

// Alerts (POST /alerts)
export interface AlertCreateRequest {
  rule_id: string;
  title: string;
  event_ids?: string[];
  severity?: Severity;
  confidence?: number;
  risk_score?: number;
  tags?: string[];
}
export interface AlertCreateResponse {
  alert_id: string;
  rule_id: string;
  severity: string;
  occurrences: number;
  kind: "created" | "deduplicated";
}

// Incidents (POST /incidents)
export interface AlertPayload {
  alert_id: string;
  rule_id?: string;
  title?: string;
  severity?: Severity;
  risk_score?: number;
  confidence?: number;
  asset_id?: string;
  user?: string;
  fingerprint_hash?: string;
  mitre?: string[];
  ioc_ids?: string[];
}
export interface IncidentCreateRequest {
  alerts: AlertPayload[];
  title?: string;
}
export interface IncidentCreateResponse {
  incident_id: string;
  alerts_count: number;
  kind: "created" | "deduplicated" | "no_group";
}

// Cases (POST /cases)
export interface CaseCreateRequest {
  incident_id: string;
  title?: string;
  owner?: string;
}
export interface CaseCreateResponse {
  case_id: string;
  title: string;
  status: string;
}

// Response wrapper
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: { code: string; message: string; status: number };
}

// ─────────────────────────────────────────────────────────────────────────────
// Configuração (vars de ambiente via .env.local)
//
// Default: "/api/v1" (caminho relativo) — em dev o Vite faz proxy para o
// backend via vite.config.ts, eliminando CORS. Em produção, use VITE_API_URL
// apontando para o backend (mesma origem ou com CORS habilitado).
// ─────────────────────────────────────────────────────────────────────────────

const BASE_URL = (import.meta.env.VITE_API_URL || "/api/v1").replace(/\/+$/, "");
const TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT) || 10000;
const MAX_RETRIES = Number(import.meta.env.VITE_API_RETRIES) || 2;

// ─────────────────────────────────────────────────────────────────────────────
// Cliente HTTP
// ─────────────────────────────────────────────────────────────────────────────

interface RequestOptions {
  method?: string;
  body?: unknown;
  signal?: AbortSignal;
}

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function request<T = unknown>(
  method: string,
  path: string,
  options: RequestOptions = {},
): Promise<ApiResponse<T>> {
  const url = `${BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;

  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= MAX_RETRIES + 1; attempt++) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

    try {
      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: options.body ? JSON.stringify(options.body) : undefined,
        signal: options.signal ?? controller.signal,
      });

      clearTimeout(timeoutId);

      const contentType = res.headers.get("content-type");
      const json =
        contentType && contentType.includes("application/json")
          ? await res.json()
          : null;

      if (!res.ok) {
        // Erro HTTP — extrair mensagem do backend
        const message =
          json && typeof json === "object" && "detail" in json
            ? String(json.detail)
            : res.statusText || `HTTP ${res.status}`;

        return {
          success: false,
          error: {
            code: String(res.status),
            message,
            status: res.status,
          },
        };
      }

      // Sucesso — extrair dados
      if (json && typeof json === "object" && "data" in json && json.data !== undefined) {
        return { success: true, data: json.data as T };
      }

      return { success: true, data: json as T };
    } catch (err) {
      clearTimeout(timeoutId);

      const isAbort = err instanceof DOMException && err.name === "AbortError";

      lastError = err instanceof Error ? err : new Error("Unknown error");

      // Se for timeout, não retry (retry pode conflitar)
      if (isAbort && attempt === 1) {
        return {
          success: false,
          error: {
            code: "TIMEOUT",
            message: `Request timed out after ${TIMEOUT_MS}ms`,
            status: 408,
          },
        };
      }

      // Retry apenas em falhas de rede (não em erros HTTP)
      if (attempt <= MAX_RETRIES) {
        await delay(300 * attempt);
        continue;
      }

      return {
        success: false,
        error: {
          code: "NETWORK_ERROR",
          message: lastError.message,
          status: 0,
        },
      };
    }
  }

  // Nunca deve chegar aqui, mas cobertura de segurança
  return {
    success: false,
    error: {
      code: "UNEXPECTED",
      message: lastError?.message || "Unexpected error",
      status: 0,
    },
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Métodos exportados
// ─────────────────────────────────────────────────────────────────────────────

export const apiClient = {
  get: <T = unknown>(path: string, options?: RequestOptions) => request<T>("GET", path, options),
  post: <T = unknown>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>("POST", path, { ...options, body }),
  put: <T = unknown>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>("PUT", path, { ...options, body }),
  delete: <T = unknown>(path: string, options?: RequestOptions) => request<T>("DELETE", path, options),
};
