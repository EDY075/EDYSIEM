/**
 * Hook: useCases — fetch recent cases (UI 4.0)
 * Backend não expõe GET /cases (apenas POST). Mantém fallback mock
 * para desenvolvimento offline. Conectado ao endpoint real quando disponível.
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

const MOCK_CASES: Case[] = [
  {
    id: "CASE-001",
    title: "Investigação: Campanha SSH + PowerShell",
    description: "Análise de ataques coordenados",
    status: "in_progress",
    severity: "critical",
    priority: "P1",
    owner: "analyst@soc",
    incidentId: "INC-001",
    alerts: ["ALT-001", "ALT-002"],
    assets: ["wks-042", "web-01"],
    users: ["john.doe", "root"],
    iocs: ["18.220.1.2"],
    mitre: ["T1110.001", "T1059.001"],
    riskScore: 95,
    createdAt: "2026-08-04T14:30:00",
    updatedAt: "2026-08-04T15:00:00",
    tags: ["authentication", "malware", "lateral-movement"],
  },
  {
    id: "CASE-002",
    title: "Investigação: Exfiltração de Dados via Nuvem",
    description: "Análise de transferência não autorizada",
    status: "open",
    severity: "high",
    priority: "P2",
    owner: undefined,
    incidentId: "INC-002",
    alerts: ["ALT-004"],
    assets: ["proxy-01"],
    users: ["jane.doe"],
    iocs: [],
    mitre: ["T1567.001"],
    riskScore: 92,
    createdAt: "2026-08-04T08:30:00",
    updatedAt: "2026-08-04T08:35:00",
    tags: ["data-loss"],
  },
];

export function useCases(limit: number = 10) {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCases = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<Case[]>(
        `/cases?limit=${limit}&sort=updatedAt&order=desc`
      );
      if (response.success && response.data) {
        setCases(response.data);
      } else if (response.error?.status === 404) {
        // Backend não implementou GET /cases — usar mock
        setCases(MOCK_CASES.slice(0, limit));
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

  return { cases, loading, error, refetch: fetchCases, usingMock: !error && cases.length > 0 };
}