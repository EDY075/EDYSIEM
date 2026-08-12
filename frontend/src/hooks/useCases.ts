/**
 * Hook: useCases — cases reais do backend (Sprint 2.16)
 * Consome GET /api/v1/soc/cases. Sem fallback mock.
 */
import { useState, useEffect, useCallback } from "react";
import { apiClient } from "../api/client";
import type { SlaSnapshotDto } from "./useShieldEvents";

export interface Case {
  id: string;
  title: string;
  status: string;
  statusLabel: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  priority: string;
  owner?: string;
  incidentId?: string;
  commentsCount: number;
  evidenceCount: number;
  tasksCount: number;
  attachmentsCount: number;
  resolution?: string | null;
  createdAt: string;
  closedAt?: string | null;
  sla?: SlaSnapshotDto;
}

interface SocCaseDto {
  case_id: string;
  title: string;
  status: string;
  status_label: string;
  severity: string;
  priority: string;
  owner: string | null;
  incident_id: string | null;
  comments_count: number;
  evidence_count: number;
  tasks_count: number;
  attachments_count: number;
  resolution: string | null;
  created_at: string;
  closed_at: string | null;
  sla?: SlaSnapshotDto;
}

function toCase(c: SocCaseDto): Case {
  return {
    id: c.case_id,
    title: c.title,
    status: c.status,
    statusLabel: c.status_label || c.status,
    severity: c.severity as Case["severity"],
    priority: c.priority,
    owner: c.owner || "",
    incidentId: c.incident_id || "",
    commentsCount: c.comments_count,
    evidenceCount: c.evidence_count,
    tasksCount: c.tasks_count,
    attachmentsCount: c.attachments_count,
    resolution: c.resolution,
    createdAt: c.created_at,
    closedAt: c.closed_at,
    sla: c.sla,
  };
}

const UUID4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

export function useCases(limit: number = 50, requestedCaseId: string = "") {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCases = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<{ total: number; items: unknown[] }>(
        `/soc/cases?limit=${limit}`
      );
      if (response.success && response.data) {
        const items = (response.data.items || []).map((i) => toCase(i as SocCaseDto));
        if (requestedCaseId && UUID4.test(requestedCaseId) && !items.some((item) => item.id === requestedCaseId)) {
          const exact = await apiClient.get<SocCaseDto>(
            `/soc/cases/${encodeURIComponent(requestedCaseId)}`,
          );
          if (exact.success && exact.data) items.unshift(toCase(exact.data));
        }
        setCases(items);
      } else {
        setError(response.error?.message || "Falha ao carregar cases");
        setCases([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar cases");
      setCases([]);
    } finally {
      setLoading(false);
    }
  }, [limit, requestedCaseId]);

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  return { cases, loading, error, refetch: fetchCases };
}
