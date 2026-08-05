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

export function useHealth() {
  const [health, setHealth] = useState<SystemHealth>({
    ingestion: "online",
    correlation: "online",
    enrichment: "online",
    detection: "online",
    alerts: "online",
    cases: "online",
    storage: "online",
    api: "online",
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
          ingestion: components.enrichment?.status || "online",
          correlation: components.correlation?.status || "online",
          enrichment: components.enrichment?.status || "online",
          detection: components.detection?.status || "online",
          alerts: components.alerts?.status || "online",
          cases: components.cases?.status || "online",
          storage: components.storage?.status || "online",
          api: components.api?.status || "online",
        });
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

  return { health, loading, error, refetch: fetchHealth };
}