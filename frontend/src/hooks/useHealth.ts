/**
 * Hook: useHealth — fetch system health status (UI 4.0)
 * Conecta ao endpoint real GET /api/v1/health
 */
import { useState, useEffect } from "react";
import { apiClient } from "../api/client";
import type {
  HealthResponse,
  HealthStatus,
  ComponentStatus,
} from "../api/client";

export interface IngestionHealthDetails {
  receiver: "edy-shield" | null;
  receiverState: "ready" | null;
  acceptedEvents: number | null;
  pendingEvents: number | null;
  lastReceivedAt: string | null;
  oldestPendingAt: string | null;
}

export interface SystemHealth {
  overall: HealthStatus;
  environment: string | null;
  ingestion: ComponentStatus;
  correlation: ComponentStatus;
  enrichment: ComponentStatus;
  detection: ComponentStatus;
  alerts: ComponentStatus;
  cases: ComponentStatus;
  storage: ComponentStatus;
  api: ComponentStatus;
  ingestionDetails: IngestionHealthDetails;
}

const emptyIngestionDetails: IngestionHealthDetails = {
  receiver: null,
  receiverState: null,
  acceptedEvents: null,
  pendingEvents: null,
  lastReceivedAt: null,
  oldestPendingAt: null,
};

function componentStatus(value: ComponentStatus | "healthy" | undefined, fallback: ComponentStatus): ComponentStatus {
  return value === "healthy" ? "online" : value || fallback;
}

function nonNegativeNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isInteger(value) && value >= 0 ? value : null;
}

function nullableString(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function ingestionDetails(response: HealthResponse): IngestionHealthDetails {
  const details = response.components.ingestion?.details;
  if (!details) return emptyIngestionDetails;
  return {
    receiver: details.receiver === "edy-shield" ? "edy-shield" : null,
    receiverState: details.receiver_state === "ready" ? "ready" : null,
    acceptedEvents: nonNegativeNumber(details.accepted_events),
    pendingEvents: nonNegativeNumber(details.pending_events),
    lastReceivedAt: nullableString(details.last_received_at),
    oldestPendingAt: nullableString(details.oldest_pending_at),
  };
}

const initialHealth: SystemHealth = {
  overall: "critical",
  environment: null,
  ingestion: "offline",
  correlation: "offline",
  enrichment: "offline",
  detection: "offline",
  alerts: "offline",
  cases: "offline",
  storage: "offline",
  api: "offline",
  ingestionDetails: emptyIngestionDetails,
};

interface HealthHookState {
  health: SystemHealth;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

let sharedState: HealthHookState = {
  health: initialHealth,
  loading: true,
  error: null,
  lastUpdated: null,
};
let inFlight: Promise<void> | null = null;
const listeners = new Set<(state: HealthHookState) => void>();

function publish(patch: Partial<HealthHookState>) {
  sharedState = { ...sharedState, ...patch };
  listeners.forEach((listener) => listener(sharedState));
}

async function fetchSharedHealth(): Promise<void> {
  if (inFlight) return inFlight;
  inFlight = (async () => {
    publish({ loading: true });
    try {
      const response = await apiClient.get<HealthResponse>("/health");
      if (response.success && response.data) {
        const components = response.data.components;
        publish({
          health: {
            overall: response.data.status,
            environment: response.data.environment || null,
            ingestion: componentStatus(components.ingestion?.status, "offline"),
            correlation: componentStatus(components.correlation?.status, "offline"),
            enrichment: componentStatus(components.enrichment?.status, "offline"),
            detection: componentStatus(components.detection?.status, "offline"),
            alerts: componentStatus(components.alerts?.status, "offline"),
            cases: componentStatus(components.cases?.status, "offline"),
            storage: componentStatus(components.storage?.status, "offline"),
            api: componentStatus(components.api?.status, "online"),
            ingestionDetails: ingestionDetails(response.data),
          },
          error: null,
          lastUpdated: new Date(),
        });
      } else {
        publish({ error: response.error?.message || "Failed to fetch health" });
      }
    } catch (err) {
      publish({ error: err instanceof Error ? err.message : "Failed to fetch health" });
    } finally {
      publish({ loading: false });
    }
  })().finally(() => {
    inFlight = null;
  });
  return inFlight;
}

export function useHealth() {
  const [state, setState] = useState<HealthHookState>(sharedState);

  useEffect(() => {
    listeners.add(setState);
    setState(sharedState);
    if (sharedState.lastUpdated === null && !inFlight) void fetchSharedHealth();
    return () => {
      listeners.delete(setState);
    };
  }, []);

  return { ...state, refetch: fetchSharedHealth };
}
