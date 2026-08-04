/**
 * Hook: useCases — fetch recent cases (UI 4.0)
 */
import { useState, useEffect, useCallback } from "react";
import { apiClient } from "../api/client";

export interface Case {
  id: string;
  title: string;
  description: string;
  status: "open" | "in_progress" | "on_hold" | "resolved" | "closed" | "reopened";
  severity: "critical" | "high" | "medium" | "low" | "info";
  priority: "P1" | "P2" | "P3" | "P4" | "P5";
  owner?: string;
  incidentId: string;
  alerts: string[];
  assets: string[];
  users: string[];
  iocs: string[];
  mitre: string[];
  riskScore: number;
  createdAt: string;
  updatedAt: string;
  closedAt?: string;
  tags: string[];
}

export function useCases(limit: number = 10) {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCases = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<Case[]>(
        `/cases?limit=${limit}&sort=updatedAt&order=desc`
      );
      if (response.success && response.data) {
        setCases(response.data);
      } else {
        setError(response.error?.message || "Failed to fetch cases");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch cases");
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  return { cases, loading, error, refetch: fetchCases };
}
