/**
 * Hook: useMetrics — métricas reais do backend (Sprint 2.16)
 * Consome GET /api/v1/soc/metrics (persistência + série temporal real).
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
  eventsSeries: { time: string; events: number }[];
}

interface SocMetricsDto {
  events_per_second: number;
  events_per_minute: number;
  events_last_24h: number;
  active_alerts: number;
  open_cases: number;
  mttr_seconds: number;
  avg_risk_score: number;
  events_series: { time: string; events: number }[];
}

const EMPTY: DashboardMetrics = {
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
  eventsSeries: [],
};

export function useMetrics(_timeRange: string = "1h") {
  const [metrics, setMetrics] = useState<DashboardMetrics>(EMPTY);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<{ metrics: Partial<SocMetricsDto> }>(`/soc/metrics`);
      if (response.success && response.data?.metrics) {
        const m = response.data.metrics;
        const series = m.events_series || [];
        setMetrics({
          eps: m.events_per_second || 0,
          activeAlerts: m.active_alerts || 0,
          openCases: m.open_cases || 0,
          eventsLastHour: series.length ? series[series.length - 1].events : 0,
          eventsLast24h: m.events_last_24h || 0,
          systemHealth: "healthy",
          ingestionStatus: "online",
          avgRiskScore: m.avg_risk_score || 0,
          mttr: Math.round((m.mttr_seconds || 0) / 60),
          mtta: 0,
          eventsSeries: series,
        });
      } else {
        setError(response.error?.message || "Falha ao carregar métricas");
        setMetrics(EMPTY);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar métricas");
      setMetrics(EMPTY);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  return { metrics, loading, error, refetch: fetchMetrics };
}