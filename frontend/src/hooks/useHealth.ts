/**
 * Hook: useHealth — fetch system health status (UI 4.0)
 */
import { useState, useEffect, useCallback } from "react";
import { apiClient } from "../api/client";

export interface SystemHealth {
  ingestion: "healthy" | "degraded" | "critical";
  correlation: "healthy" | "degraded" | "critical";
  enrichment: "healthy" | "degraded" | "critical";
  detection: "healthy" | "degraded" | "critical";
  alerts: "healthy" | "degraded" | "critical";
  cases: "healthy" | "degraded" | "critical";
  storage: "healthy" | "degraded" | "critical";
  api: "healthy" | "degraded" | "critical";
}

export function useHealth() {
  const [health, setHealth] = useState<SystemHealth>({
    ingestion: "healthy",
    correlation: "healthy",
    enrichment: "healthy",
    detection: "healthy",
    alerts: "healthy",
    cases: "healthy",
    storage: "healthy",
    api: "healthy",
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<SystemHealth>("/health");
      if (response.success && response.data) {
        setHealth(response.data);
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
