/**
 * Hook: useAlerts — fetch recent alerts (UI 4.0)
 * Backend não expõe GET /alerts (apenas POST). Mantém fallback mock
 * para desenvolvimento offline. Conectado ao endpoint real quando disponível.
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

const MOCK_ALERTS: RecentAlert[] = [
  { id: "ALT-001", title: "Brute Force SSH", severity: "critical", status: "open", source: "web-01", host: "web-01", user: "root", rule: "brute-force-ssh", firstSeen: "2026-08-04T10:15:00", riskScore: 95 },
  { id: "ALT-002", title: "Malware Execution - PowerShell", severity: "critical", status: "open", source: "wks-042", host: "wks-042", user: "john.doe", rule: "malware-exec", firstSeen: "2026-08-04T14:22:00", riskScore: 95 },
  { id: "ALT-003", title: "Impossible Travel - geo impossível", severity: "high", status: "in_progress", source: "vpn-gateway", host: "vpn-gw", user: "jane.smith", rule: "impossible-travel", firstSeen: "2026-08-04T09:15:00", riskScore: 78 },
  { id: "ALT-004", title: "Data Exfiltration - Cloud Storage", severity: "critical", status: "in_progress", source: "proxy-01", host: "proxy-01", user: "jane.doe", rule: "data-exfiltration", firstSeen: "2026-08-04T08:30:00", riskScore: 92 },
  { id: "ALT-005", title: "Crypto Miner - XMRig", severity: "high", status: "open", source: "wks-033", host: "wks-033", user: "svc-backup", rule: "crypto-miner", firstSeen: "2026-08-04T06:00:00", riskScore: 88 },
];

export function useAlerts(limit: number = 10) {
  const [alerts, setAlerts] = useState<RecentAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<RecentAlert[]>(
        `/alerts?limit=${limit}&sort=lastSeen&order=desc`
      );
      if (response.success && response.data) {
        setAlerts(response.data);
      } else if (response.error?.status === 404 || response.error?.status === 405) {
        // Backend ainda não expõe GET /alerts (404) ou retorna Method Not Allowed (405) — usar mock
        setAlerts(MOCK_ALERTS.slice(0, limit));
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

  return { alerts, loading, error, refetch: fetchAlerts, usingMock: !error && alerts.length > 0 };
}