/**
 * Hook: useHealth — fetch system health status (UI 4.0)
 * Conecta ao endpoint real GET /api/v1/health
 */
import { useState, useEffect, useCallback } from "react";
import { apiClient } from "../api/client";
import type { HealthStatus, ComponentStatus } from "../api/client";

export interface SystemHealth {
  ingestion: ComponentStatus;
  correlation: ComponentStatus;
  enrichment: ComponentStatus;
  detection: ComponentStatus;
  alerts: ComponentStatus;
  cases: ComponentStatus;
  storage: ComponentStatus;
  api: ComponentStatus;
}

function componentStatus(value: ComponentStatus | "healthy" | undefined, fallback: ComponentStatus): ComponentStatus {
  return value === "healthy" ? "online" : value || fallback;
}

export function useHealth() {
  const [health, setHealth] = useState<SystemHealth>({
    ingestion: "offline",
    correlation: "offline",
    enrichment: "offline",
    detection: "offline",
    alerts: "offline",
    cases: "offline",
    storage: "offline",
    api: "offline",
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchHealth = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<{ status: HealthStatus; version: string; components: Record<string, { status: ComponentStatus }> }>(
        "/health"
      );
      if (response.success && response.data) {
        const components = response.data.components;
        setHealth({
          ingestion: componentStatus(components.ingestion?.status, "offline"),
          correlation: componentStatus(components.correlation?.status, "offline"),
          enrichment: componentStatus(components.enrichment?.status, "offline"),
          detection: componentStatus(components.detection?.status, "offline"),
          alerts: componentStatus(components.alerts?.status, "offline"),
          cases: componentStatus(components.cases?.status, "offline"),
          storage: componentStatus(components.storage?.status, "offline"),
          api: componentStatus(components.api?.status, "online"),
        });
        setLastUpdated(new Date());
      } else {
        setError(response.error?.message || "Failed to fetch health");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch health");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  return { health, loading, error, lastUpdated, refetch: fetchHealth };
}
