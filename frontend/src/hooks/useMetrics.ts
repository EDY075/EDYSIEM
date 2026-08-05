/**
 * Hook: useMetrics — fetch dashboard metrics (UI 4.0)
 * Conecta ao endpoint real GET /api/v1/metrics
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
      setError(null);
      const response = await apiClient.get(`/metrics?range=${timeRange}`);
      if (response.success && response.data) {
        const raw = response.data as { metrics: Record<string, number>; components: Record<string, unknown> };
        const m = raw.metrics || {};

        // Mapeia os campos do backend para os campos esperados pelo frontend
        setMetrics({
          eps: m.events_per_second || m.eps || 0,
          activeAlerts: m.active_alerts || 0,
          openCases: m.open_cases || 0,
          eventsLastHour: m.events_last_hour || m.eventsLastHour || 0,
          eventsLast24h: m.events_last_24h || m.eventsLast24h || 0,
          systemHealth: (m.system_health || "healthy") as DashboardMetrics["systemHealth"],
          ingestionStatus: (m.ingestion_status || "online") as DashboardMetrics["ingestionStatus"],
          avgRiskScore: m.avg_risk_score || m.risk_score || 0,
          mttr: m.mttr || 0,
          mtta: m.mtta || 0,
        });
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