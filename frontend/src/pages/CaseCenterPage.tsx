/**
 * Case Management UI (Sprint 2.16 WP3) â€” dados reais.
 * Lista de casos + painel de detalhe (timeline, evidÃªncias, investigaÃ§Ã£o) +
 * aÃ§Ãµes: comentar, anexar evidÃªncia, resolver e encerrar.
 */
import { useState } from "react";
import type { CSSProperties } from "react";
import { colors, radii, spacing, typography } from "../design-system/tokens";
import { Button } from "../design-system";
import { MetricCard } from "../design-system/components/cards";
import { StatusBadge } from "../design-system/components/badges";
import { Toolbar, EmptyState, LoadingSkeleton } from "../design-system/components/feedback";
import { Breadcrumb } from "../shell/Breadcrumb";
import { useCases } from "../hooks";
import type { Case } from "../hooks/useCases";
import { apiClient } from "../api/client";

interface Investigate {
  related_alerts: unknown[];
  iocs: string[];
  assets: string[];
  users: string[];
  mitre: string[];
  timeline: { action: string; detail: string; actor: string; created_at: string }[];
  evidence: { kind: string; value: string; label: string }[];
}

const fmt = (iso: string) => (iso ? new Date(iso).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "â€”");

export function CaseCenterPage() {
  const { cases, loading, error, refetch } = useCases(100);
  const [selected, setSelected] = useState<Case | null>(null);
  const [inv, setInv] = useState<Investigate | null>(null);
  const [invLoading, setInvLoading] = useState(false);
  const [comment, setComment] = useState("");
  const [evidence, setEvidence] = useState("");
  const [busy, setBusy] = useState(false);

  async function loadInvestigation(c: Case) {
    setSelected(c);
    setInvLoading(true);
    setInv(null);
    const r = await apiClient.get<Investigate>(`/soc/cases/${c.id}/investigate`);
    if (r.success && r.data) setInv(r.data);
    setInvLoading(false);
  }

  async function doPost(path: string, params: Record<string, string>) {
    setBusy(true);
    await apiClient.post(`${path}?${new URLSearchParams(params).toString()}`);
    // recarrega detalhe para refletir mudanÃ§as
    const r = await apiClient.get<Investigate>(`/soc/cases/${selected?.id}/investigate`);
    if (r.success && r.data) setInv(r.data);
    refetch();
    setBusy(false);
  }

  const addComment = () => { if (selected && comment) { doPost(`/soc/cases/${selected.id}/comment`, { body: comment, author: "analista.soc" }); setComment(""); } };
  const addEvidence = () => { if (selected && evidence) { doPost(`/soc/cases/${selected.id}/evidence`, { kind: "ioc", value: evidence }); setEvidence(""); } };

  return (
    <div style={{ display: "flex", height: "100vh", background: colors.background }} className="cl-center">
      <div style={{ width: 420, borderRight: `1px solid ${colors.border}`, display: "flex", flexDirection: "column", minWidth: 320 }}>
        <div style={{ padding: spacing["4"], borderBottom: `1px solid ${colors.border}`, background: colors.surface }}>
          <Breadcrumb items={[{ label: "Dashboard", to: "/" }, { label: "Cases", to: "/cases" }]} />
          <h1 style={{ margin: "6px 0 0", fontSize: typography.size["2xl"], color: colors.textPrimary }}>Case Management</h1>
        </div>
        <div style={{ padding: spacing["3"] }}>
          <Toolbar left={<span style={{ fontSize: typography.size.sm, color: colors.textMuted }}>{cases.length} casos</span>} right={<Button variant="ghost" onClick={refetch}>â†»</Button>} />
        </div>
        <div style={{ flex: 1, overflow: "auto", padding: `0 ${spacing["3"]} ${spacing["3"]}`, display: "flex", flexDirection: "column", gap: 8 }}>
          {loading ? <LoadingSkeleton rows={6} /> : error ? (
            <EmptyState title="Casos indisponÃ­veis" description={error} onRetry={refetch} />
          ) : cases.length === 0 ? (
            <EmptyState title="Sem casos" description="Execute o fluxo SOC para gerar casos." />
          ) : cases.map((c) => (
            <button key={c.id} onClick={() => loadInvestigation(c)} style={{ textAlign: "left", padding: spacing["3"], background: selected?.id === c.id ? colors.surfaceAlt : colors.surface, border: `1px solid ${selected?.id === c.id ? colors.accent : colors.border}`, borderRadius: radii.md, cursor: "pointer" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontWeight: 600, color: colors.textPrimary, fontSize: typography.size.sm }}>{c.title}</span>
                <StatusBadge tone="neutral">{c.statusLabel}</StatusBadge>
              </div>
              <div style={{ marginTop: 6, fontSize: typography.size.xs, color: colors.textMuted }}>
                {c.id} â€¢ evid:{c.evidenceCount} Â· com:{c.commentsCount} Â· {c.owner || "sem owner"}
              </div>
            </button>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, overflow: "auto", padding: spacing["4"] }}>
        {!selected ? (
          <EmptyState title="Selecione um caso" description="Escolha um caso Ã  esquerda para visualizar timeline, evidÃªncias, IOCs, MITRE e histÃ³rico." icon="â–¤" />
        ) : invLoading ? (
          <LoadingSkeleton rows={10} variant="card" />
        ) : (
          <>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: spacing["4"] }}>
              <div>
                <h2 style={{ margin: 0, color: colors.textPrimary }}>{selected.title}</h2>
                <div style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
                  {selected.id} Â· {selected.statusLabel} Â· severity {selected.severity} Â· {selected.resolution ? `resoluÃ§Ã£o: ${selected.resolution}` : "sem resoluÃ§Ã£o"}
                </div>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <Button variant="secondary" disabled={busy} onClick={() => selected && doPost(`/soc/cases/${selected.id}/resolve`, { resolution: "incidente confirmado e tratado" })}>Resolver</Button>
                <Button variant="danger" disabled={busy} onClick={() => selected && doPost(`/soc/cases/${selected.id}/close`, { resolution: "encerrado" })}>Encerrar</Button>
              </div>
            </div>

            {/* ComentÃ¡rio + evidÃªncia */}
            <div style={{ display: "flex", gap: 8, marginBottom: spacing["4"] }}>
              <input value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Novo comentÃ¡rio..." style={inputStyle} />
              <Button variant="primary" disabled={busy || !comment} onClick={addComment}>Comentar</Button>
              <input value={evidence} onChange={(e) => setEvidence(e.target.value)} placeholder="EvidÃªncia (IOC/IP)â€¦" style={inputStyle} />
              <Button variant="secondary" disabled={busy || !evidence} onClick={addEvidence}>Anexar evidÃªncia</Button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: spacing["4"] }}>
              <MetricCard title="Timeline">
                {inv?.timeline?.length ? inv.timeline.map((t, i) => (
                  <div key={i} style={{ padding: `6px 0`, borderBottom: `1px solid ${colors.borderSubtle}`, fontSize: typography.size.sm }}>
                    <span style={{ color: colors.textMuted, fontSize: 11, fontFamily: typography.family.mono }}>{fmt(t.created_at)}</span>{" "}
                    <span style={{ color: colors.accent }}>[{t.action}]</span>
                    <div style={{ color: colors.textSecondary }}>{t.detail || t.actor}</div>
                  </div>
                )) : <div style={{ color: colors.textMuted }}>Sem eventos.</div>}
              </MetricCard>
              <div style={{ display: "flex", flexDirection: "column", gap: spacing["4"] }}>
                <MetricCard title={`EvidÃªncias (${inv?.evidence.length || 0})`}>
                  {inv?.evidence.length ? inv.evidence.map((e, i) => (
                    <div key={i} style={{ fontSize: typography.size.sm, padding: `4px 0` }}>
                      <span style={{ color: colors.textMuted }}>{e.kind}: </span>
                      <span style={{ fontFamily: typography.family.mono, color: colors.textPrimary }}>{e.value}</span>
                    </div>
                  )) : <div style={{ color: colors.textMuted }}>Nenhuma evidÃªncia.</div>}
                </MetricCard>
                <MetricCard title="Contexto da investigaÃ§Ã£o">
                  <Detail label="IOC" value={inv?.iocs.length || 0} />
                  <Detail label="MITRE" value={inv?.mitre.length || 0} />
                  <Detail label="Assets" value={inv?.assets.length || 0} />
                  <Detail label="UsuÃ¡rios" value={inv?.users.length || 0} />
                </MetricCard>
              </div>
            </div>
          </>
        )}
      </div>

      <style>{`.cl-center { }
@media (max-width: 1100px) { .cl-center { flex-direction: column; } .cl-center>div:first-child { width: 100% !important; } }`}</style>
    </div>
  );
}

const inputStyle: CSSProperties = {
  flex: 1, minWidth: 120, padding: "8px 10px", border: `1px solid ${colors.border}`, borderRadius: radii.md,
  background: colors.surface, color: colors.textPrimary, fontFamily: typography.family.ui, fontSize: typography.size.sm,
};

function Detail({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: typography.size.sm, padding: "4px 0" }}>
      <span style={{ color: colors.textMuted }}>{label}</span>
      <span style={{ color: colors.textPrimary, fontWeight: 600 }}>{value}</span>
    </div>
  );
}