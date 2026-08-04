/**
 * Hook: useMetrics — fetch dashboard metrics (UI 4.0)
 */
import { useState, useEffect, useCallback } from "react";
import { apiClient } from "../api/client";

export interface DashboardMetrics {
  eps: number;
  activeAlerts: number;
  openCases: number;
  eventsLastHour: number;
  eventsLast24h: number;
  systemHealth: "healthy" | "degraded" | "critical";
  ingestionStatus: "online" | "degraded" | "offline";
  avgRiskScore: number;
  mttr: number;
  mtta: number;
}

export function useMetrics(timeRange: string = "1h") {
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    eps: 0,
    activeAlerts: 0,
    openCases: 0,
    eventsLastHour: 0,
    eventsLast24h: 0,
    systemHealth: "healthy",
    ingestionStatus: "online",
    avgRiskScore: 0,
    mttr: 0,
    mtta: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<DashboardMetrics>(`/metrics?range=${timeRange}`);
      if (response.success && response.data) {
        setMetrics(response.data);
      } else {
        setError(response.error?.message || "Failed to fetch metrics");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch metrics");
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  return { metrics, loading, error, refetch: fetchMetrics };
}
