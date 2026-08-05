/**
 * Hook: useIncidents — fetch recent incidents (UI 4.0)
 * Backend não expõe GET /incidents (apenas POST). Mantém fallback mock
 * para desenvolvimento offline. Conectado ao endpoint real quando disponível.
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

const MOCK_INCIDENTS: Incident[] = [
  {
    id: "INC-001",
    title: "Campanha de Ataque Contínuo - SSH + PowerShell",
    severity: "critical",
    status: "in_progress",
    source: "correlation-engine",
    host: "wks-042",
    user: "john.doe",
    rule: "multi-stage-attack",
    firstSeen: "2026-08-04T14:22:00",
    riskScore: 95,
    alerts: ["ALT-001", "ALT-002"],
    assetId: "wks-042",
  },
  {
    id: "INC-002",
    title: "Data Exfiltration via Cloud Storage",
    severity: "critical",
    status: "open",
    source: "data-loss-prevention",
    host: "proxy-01",
    user: "jane.doe",
    rule: "data-exfiltration",
    firstSeen: "2026-08-04T08:30:00",
    riskScore: 92,
    alerts: ["ALT-004"],
    assetId: "proxy-01",
  },
];

export function useIncidents(limit: number = 10) {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIncidents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<Incident[]>(
        `/incidents?limit=${limit}&sort=lastSeen&order=desc`
      );
      if (response.success && response.data) {
        setIncidents(response.data);
      } else if (response.error?.status === 404) {
        // Backend não implementou GET /incidents — usar mock
        setIncidents(MOCK_INCIDENTS.slice(0, limit));
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

  return { incidents, loading, error, refetch: fetchIncidents, usingMock: !error && incidents.length > 0 };
}