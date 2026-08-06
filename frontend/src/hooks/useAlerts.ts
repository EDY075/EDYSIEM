/**
 * Hook: useAlerts — alertas reais do backend (Sprint 2.16)
 * Consome GET /api/v1/soc/alerts (lista persistida).
 * Sem fallback mock — erro vai para o estado `error` (UI mostra Empty/Retry).
 */
import { useState, useEffect, useCallback } from "react";
import { apiClient } from "../api/client";

export interface RecentAlert {
  id: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  status: "open" | "in_progress" | "resolved" | "closed" | "false_positive";
  source: string;
  host: string;
  user?: string;
  rule: string;
  firstSeen: string;
  riskScore: number;
  mitre: string[];
}

interface SocAlertDto {
  alert_id: string;
  title: string;
  rule_id: string;
  severity: string;
  status: string;
  risk_score: number;
  source: string;
  occurrences: number;
  iocs: string[];
  mitre: string[];
  created_at: string;
  sla: { state: string };
}

function toRecentAlert(a: SocAlertDto): RecentAlert {
  return {
    id: a.alert_id,
    title: a.title,
    severity: a.severity as RecentAlert["severity"],
    status: a.status as RecentAlert["status"],
    source: a.source,
    host: a.source,
    rule: a.rule_id,
    firstSeen: a.created_at,
    riskScore: a.risk_score,
    mitre: a.mitre,
  };
}

export function useAlerts(limit: number = 50) {
  const [alerts, setAlerts] = useState<RecentAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<{ total: number; items: unknown[] }>(
        `/soc/alerts?limit=${limit}`
      );
      if (response.success && response.data) {
        const items = (response.data.items || []).map((i) => toRecentAlert(i as SocAlertDto));
        setAlerts(items);
      } else {
        setError(response.error?.message || "Falha ao carregar alertas");
        setAlerts([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar alertas");
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  return { alerts, loading, error, refetch: fetchAlerts };
}