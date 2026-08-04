/**
 * Hook: useIncidents — fetch recent incidents (UI 4.0)
 */
import { useState, useEffect, useCallback } from "react";
import { apiClient } from "../api/client";

export interface Incident {
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
  alerts: string[];
  assetId?: string;
}

export function useIncidents(limit: number = 10) {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIncidents = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<Incident[]>(
        `/incidents?limit=${limit}&sort=lastSeen&order=desc`
      );
      if (response.success && response.data) {
        setIncidents(response.data);
      } else {
        setError(response.error?.message || "Failed to fetch incidents");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch incidents");
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  return { incidents, loading, error, refetch: fetchIncidents };
}
