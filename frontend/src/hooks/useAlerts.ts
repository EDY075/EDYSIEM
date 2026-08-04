/**
 * Hook: useAlerts — fetch recent alerts (UI 4.0)
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
}

export function useAlerts(limit: number = 10) {
  const [alerts, setAlerts] = useState<RecentAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<RecentAlert[]>(
        `/alerts?limit=${limit}&sort=lastSeen&order=desc`
      );
      if (response.success && response.data) {
        setAlerts(response.data);
      } else {
        setError(response.error?.message || "Failed to fetch alerts");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch alerts");
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  return { alerts, loading, error, refetch: fetchAlerts };
}
