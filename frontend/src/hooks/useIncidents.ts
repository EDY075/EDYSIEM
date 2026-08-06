/**
 * Hook: useIncidents — incidentes reais do backend (Sprint 2.16)
 * Consome GET /api/v1/soc/incidents. Sem fallback mock.
 */
import { useState, useEffect, useCallback } from "react";
import { apiClient } from "../api/client";

export interface Incident {
  id: string;
  incidentId: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  status: string;
  owner?: string;
  alertsCount: number;
  assets: string[];
  users: string[];
  iocs: string[];
  mitre: string[];
  riskScore: number;
  created_at: string;
  closed_at?: string | null;
  sla?: { state: string };
}

interface SocIncidentDto {
  incident_id: string;
  title: string;
  severity: string;
  status: string;
  risk_score: number;
  owner: string | null;
  alerts_count: number;
  assets: string[];
  users: string[];
  iocs: string[];
  mitre: string[];
  created_at: string;
  closed_at: string | null;
  sla?: { state: string };
}

function toIncident(i: SocIncidentDto): Incident {
  return {
    id: i.incident_id,
    incidentId: i.incident_id,
    title: i.title,
    severity: i.severity as Incident["severity"],
    status: i.status,
    owner: i.owner || "",
    alertsCount: i.alerts_count,
    assets: i.assets,
    users: i.users,
    iocs: i.iocs,
    mitre: i.mitre,
    riskScore: i.risk_score,
    created_at: i.created_at,
    sla: i.sla,
  };
}

export function useIncidents(limit: number = 50) {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIncidents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<{ total: number; items: unknown[] }>(
        `/soc/incidents?limit=${limit}`
      );
      if (response.success && response.data) {
        const items = (response.data.items || []).map((i) => toIncident(i as SocIncidentDto));
        setIncidents(items);
      } else {
        setError(response.error?.message || "Falha ao carregar incidentes");
        setIncidents([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar incidentes");
      setIncidents([]);
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  return { incidents, loading, error, refetch: fetchIncidents };
}