/**
 * Incident UI (Sprint 2.16 WP2) — dados reais do backend.
 * Lista incidentes com severidade/status/SLA/owner, assumir, transição e drawer.
 */
import { useState } from "react";
import { colors, spacing, typography } from "../design-system/tokens";
import { Card, Button } from "../design-system";
import { SeverityBadge, StatusBadge } from "../design-system/components/badges";
import { DataTable } from "../design-system/components/DataTable";
import { Toolbar, EmptyState, LoadingSkeleton } from "../design-system/components/feedback";
import { Breadcrumb } from "../shell/Breadcrumb";
import { useIncidents } from "../hooks";
import type { Incident } from "../hooks/useIncidents";
import { apiClient } from "../api/client";
import { useToast } from "../state/toast";

const STATUS_LABELS: Record<string, string> = {
  open: "Aberto", in_progress: "Em Andamento", on_hold: "Em espera",
  triage: "Triagem", investigating: "Investigando", contained: "Contido",
  resolved: "Resolvido", closed: "Fechado", reopened: "Reaberto",
};

const STATUS_FLOW = ["triage", "in_progress", "contained", "resolved", "closed"];

const fmt = (iso: string) => (iso ? new Date(iso).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "—");

type Row = {
  id: string;
  incident_id: string;
  title: string;
  severity: string;
  status: string;
  owner: string;
  slaState: string;
  alerts_count: number;
  created_at: string;
}

export function IncidentCenterPage() {
  const { incidents, loading, error, refetch } = useIncidents(100);
  const [detail, setDetail] = useState<Incident | null>(null);
  const [busy, setBusy] = useState(false);
  const { toast } = useToast();

  const rows: Row[] = incidents.map((r) => ({
    id: r.id,
    incident_id: r.incidentId,
    title: r.title,
    severity: r.severity,
    status: r.status,
    owner: r.owner || "",
    slaState: r.sla?.state || "",
    alerts_count: r.alertsCount,
    created_at: r.created_at,
  }));

  async function act(path: string, params: Record<string, string>, onDone: () => void) {
    setBusy(true);
    const res = await apiClient.post(`${path}?${new URLSearchParams(params).toString()}`);
    if (res.success) toast("Operação realizada", "success");
    else toast("Falha na operação", "error");
    onDone();
    setBusy(false);
  }

  const assume = (i: Incident) =>
    act(`/soc/incidents/${i.incidentId}/assign`, { analyst: "analista.soc" }, refetch);

  const setStatus = (i: Incident, target: string) =>
    act(`/soc/incidents/${i.incidentId}/transition`, { target }, refetch);

  const columns = [
    { key: "incident_id", header: "ID", width: "150px", render: (r: any) => <span style={{ fontFamily: typography.family.mono, fontSize: 12 }}>{r.incident_id}</span> },
    { key: "title", header: "Título", render: (r: any) => <span style={{ fontWeight: 600 }}>{r.title}</span> },
    { key: "severity", header: "Severidade", width: "110px", render: (r: any) => <SeverityBadge severity={r.severity}>{r.severity}</SeverityBadge> },
    { key: "status", header: "Status", width: "140px", render: (r: any) => <StatusBadge tone="neutral">{STATUS_LABELS[r.status] || r.status}</StatusBadge> },
    { key: "owner", header: "Responsável", width: "140px", render: (r: any) => <span style={{ color: r.owner ? colors.textSecondary : colors.textMuted }}>{r.owner || "—"}</span> },
    { key: "slaState", header: "SLA", width: "90px", render: (r: any) => <span style={{ color: r.slaState === "overdue" ? colors.severity.critical : colors.textMuted }}>{r.slaState || "—"}</span> },
    { key: "alerts_count", header: "Alertas", width: "70px", render: (r: any) => r.alerts_count },
    { key: "created_at", header: "Criado", width: "120px", render: (r: any) => fmt(r.created_at) },
    { key: "actions", header: "", width: "150px", render: (r: any) => {
        const inc = detailById(incidents, r.incident_id);
        return (
          <div style={{ display: "flex", gap: 6 }}>
            <Button variant="ghost" onClick={() => setDetail(inc)}>Detalhes</Button>
            <Button variant="secondary" disabled={busy} onClick={() => inc && assume(inc)}>Assumir</Button>
          </div>
        );
      } },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: colors.background }}>
      <div style={{ padding: spacing["4"], borderBottom: `1px solid ${colors.border}`, background: colors.surface }}>
        <Breadcrumb items={[{ label: "Dashboard", to: "/" }, { label: "Incidentes", to: "/incidents" }]} />
        <h1 style={{ margin: "6px 0 0", fontSize: typography.size["2xl"], color: colors.textPrimary }}>Incident Center</h1>
      </div>

      <div style={{ padding: spacing["4"] }}>
        <Toolbar left={<span style={{ fontSize: typography.size.sm, color: colors.textMuted }}>{incidents.length} incidentes</span>} right={<Button variant="ghost" onClick={refetch}>↻ Atualizar</Button>} />
      </div>

      <div style={{ flex: 1, overflow: "auto", padding: `0 ${spacing["4"]} ${spacing["4"]}` }}>
        {loading ? <LoadingSkeleton rows={8} /> : error ? (
          <EmptyState title="Incidentes indisponíveis" description={error} icon="⚠" onRetry={refetch} compact />
        ) : incidents.length === 0 ? (
          <EmptyState title="Sem incidentes" description="Nenhum incidente persistido. Execute o fluxo SOC (GET /soc/pipeline/demo) para gerar dados." icon="◌" />
        ) : (
          <Card><DataTable columns={columns} rows={rows} /></Card>
        )}
      </div>

      {detail && (
        <div style={{ position: "fixed", right: 0, top: 0, bottom: 0, width: 420, background: colors.surface, borderLeft: `1px solid ${colors.border}`, padding: spacing["4"], overflow: "auto", zIndex: 200, boxShadow: "-8px 0 24px rgba(0,0,0,0.35)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: spacing["3"] }}>
            <h2 style={{ margin: 0, fontSize: typography.size.lg, color: colors.textPrimary }}>{detail.title}</h2>
            <button onClick={() => setDetail(null)} style={{ border: "none", background: "transparent", color: colors.textMuted, fontSize: 18, cursor: "pointer" }}>✕</button>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: spacing["2"], marginBottom: spacing["4"] }}>
            <DrawerRow label="ID" value={detail.incidentId} />
            <DrawerRow label="Severidade" value={detail.severity} />
            <DrawerRow label="Status" value={STATUS_LABELS[detail.status] || detail.status} />
            <DrawerRow label="Responsável" value={detail.owner || "—"} />
            <DrawerRow label="Risk" value={String(detail.riskScore)} />
            <DrawerRow label="SLA" value={detail.sla?.state || "—"} />
            <DrawerRow label="Criado" value={fmt(detail.created_at)} />
            <DrawerRow label="Alertas" value={String(detail.alertsCount)} />
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: spacing["2"] }}>
            <Button variant="primary" disabled={busy} onClick={() => assume(detail)}>Assumir incidente</Button>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {STATUS_FLOW.map((s) => (
                <Button key={s} variant="secondary" disabled={busy || s === detail.status} onClick={() => setStatus(detail, s)}>{STATUS_LABELS[s] || s}</Button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function detailById(incidents: Incident[], id: string): Incident | null {
  return incidents.find((i) => i.incidentId === id) || null;
}

function DrawerRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: typography.size.sm }}>
      <span style={{ color: colors.textMuted }}>{label}</span>
      <span style={{ color: colors.textPrimary, fontWeight: 600 }}>{value}</span>
    </div>
  );
}