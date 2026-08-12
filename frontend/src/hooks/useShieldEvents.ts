import { useCallback, useEffect, useState } from "react";
import { apiClient } from "../api/client";

export interface SlaSnapshotDto {
  state: "ok" | "warning" | "overdue" | "met" | "missed";
  deadline: string;
  remaining_seconds?: number;
  remaining?: string;
}

export interface ShieldDecisionEvent {
  event_id: string;
  timestamp: string;
  received_at: string;
  processing_status: string;
  event_type: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  source: { product: string; component?: string };
  asset: { hostname?: string; asset_id?: string };
  evidence: {
    file_path?: string;
    previous_hash?: string;
    current_hash?: string;
    baseline_id?: string;
    scan_id?: string;
    details?: Record<string, unknown>;
  };
  case: {
    case_id: string;
    status: string;
    owner?: string | null;
    evidence_count: number;
    sla?: SlaSnapshotDto;
  } | null;
}

export function useShieldEvents(limit = 20) {
  const [events, setEvents] = useState<ShieldDecisionEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<{ total: number; items: ShieldDecisionEvent[] }>(
        `/investigation/sources/edy-shield/events?limit=${limit}`,
      );
      if (response.success && response.data) {
        setEvents(response.data.items ?? []);
      } else {
        setEvents([]);
        setError(response.error?.message || "Falha ao carregar eventos do EDY Shield");
      }
    } catch (err) {
      setEvents([]);
      setError(err instanceof Error ? err.message : "Falha ao carregar eventos do EDY Shield");
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => { refetch(); }, [refetch]);

  return { events, loading, error, refetch };
}
