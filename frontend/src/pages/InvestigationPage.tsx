/**
 * Investigation Workspace (Sprint 2.16 WP4) — dados reais.
 * Cadeia navegável: Eventos → Alertas → Incidente → Caso → MITRE → IOC →
 * Assets → Usuários → Timeline (via /soc/cases/{id}/investigate).
 */
import { useState } from "react";
import { colors, radii, spacing, typography } from "../design-system/tokens";
import { Button } from "../design-system";
import { StatusBadge } from "../design-system/components/badges";
import { EmptyState, LoadingSkeleton } from "../design-system/components/feedback";
import { Breadcrumb } from "../shell/Breadcrumb";
import { apiClient } from "../api/client";

interface InvData {
  case_id: string;
  related_alerts: { alert_id: string; title: string; rule_id: string; severity: string; risk_score: number }[];
  iocs: string[];
  assets: string[];
  users: string[];
  mitre: string[];
  timeline: { action: string; detail: string; created_at: string }[];
}

const fmt = (iso: string) => (iso ? new Date(iso).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : "—");

export function InvestigationPage() {
  const [data, setData] = useState<InvData | null>(null);
  const [dataLoading, setDataLoading] = useState(false);
  const [caseIdInput, setCaseIdInput] = useState("");

  async function open(caseId: string) {
    setDataLoading(true);
    const r = await apiClient.get<InvData>(`/soc/cases/${caseId}/investigate`);
    setData(r.success && r.data ? r.data : null);
    setDataLoading(false);
  }

  return (
    <div style={{ display: "flex", height: "100vh", background: colors.background }}>
      <div style={{ width: 380, borderRight: `1px solid ${colors.border}`, minWidth: 300, background: colors.surface }}>
        <div style={{ padding: spacing["4"], borderBottom: `1px solid ${colors.border}` }}>
          <Breadcrumb items={[{ label: "Operação", to: "/" }, { label: "Investigar", to: "/investigate" }]} />
          <h1 style={{ margin: "6px 0 0", fontSize: typography.size["2xl"], color: colors.textPrimary }}>Investigation</h1>
          <div style={{ fontSize: typography.size.xs, color: colors.textMuted }}>Insira o ID de um caso (coluna case_id) para abrir a investigação</div>
        </div>
        <div style={{ display: "flex", gap: 8, padding: spacing["3"] }}>
          <input value={caseIdInput} onChange={(e) => setCaseIdInput(e.target.value)} placeholder="case_id" style={{ flex: 1, padding: "8px 10px", border: `1px solid ${colors.border}`, borderRadius: radii.md, background: colors.background, color: colors.textPrimary }} />
          <Button variant="primary" onClick={() => caseIdInput && open(caseIdInput)}>Investigar</Button>
        </div>
      </div>

      <div style={{ flex: 1, overflow: "auto", padding: spacing["4"] }}>
        {dataLoading ? <LoadingSkeleton rows={8} variant="card" /> : !data ? (
          <EmptyState title="Aguardando caso" description="A investigação mostra a cadeia completa: eventos, alertas, incidente, caso, MITRE, IOC, assets, usuários e timeline." icon="◉" />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: spacing["4"] }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <div style={{ fontSize: typography.size.xs, color: colors.textMuted, letterSpacing: "0.05em", textTransform: "uppercase" }}>Cadeia de investigação</div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
                {["Eventos", "Alerta", "Incidente", "Caso", "MITRE", "IOC", "Asset", "Usuário", "Timeline"].map((s, i) => (
                  <span key={s} style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 11, color: colors.textSecondary, padding: "3px 8px", background: colors.surfaceAlt, border: `1px solid ${colors.border}`, borderRadius: 9999 }}>
                    {i > 0 && <span style={{ color: colors.textMuted }}>→</span>} {s}
                  </span>
                ))}
              </div>
              <div style={{ fontFamily: typography.family.mono, fontSize: 12, color: colors.textMuted }}>caso {data.case_id}</div>
            </div>

            <Section title={`Alertas relacionados (${data.related_alerts.length})`}>
              {data.related_alerts.length === 0 ? <Empty /> : data.related_alerts.map((a) => (
                <div key={a.alert_id} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: `1px solid ${colors.borderSubtle}`, fontSize: typography.size.sm }}>
                  <div>
                    <span style={{ color: colors.textPrimary, fontWeight: 600 }}>{a.title}</span>{" "}
                    <span style={{ color: colors.textMuted, fontSize: 11, fontFamily: typography.family.mono }}>{a.rule_id}</span>
                  </div>
                  <StatusBadge tone="neutral">{`${a.severity} · ${a.risk_score}`}</StatusBadge>
                </div>
              ))}
            </Section>

            <Tags title="IOC" items={data.iocs} />
            <Tags title="MITRE" items={data.mitre} />
            <Tags title="Assets" items={data.assets} />
            <Tags title="Usuários" items={data.users} />

            <Section title={`Timeline (${data.timeline.length})`}>
              {data.timeline.length === 0 && <Empty />}
              {data.timeline.map((t, i) => (
                <div key={i} style={{ display: "flex", gap: spacing["3"], padding: "4px 0" }}>
                  <span style={{ color: colors.textMuted, fontFamily: typography.family.mono, fontSize: 11 }}>{fmt(t.created_at)}</span>
                  <span style={{ color: colors.accent, fontSize: typography.size.sm }}>[{t.action}]</span>
                  <span style={{ color: colors.textSecondary, fontSize: typography.size.sm }}>{t.detail}</span>
                </div>
              ))}
            </Section>
          </div>
        )}
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: radii.lg, padding: spacing["4"] }}>
      <h3 style={{ margin: "0 0 8px", fontSize: typography.size.lg, color: colors.textPrimary }}>{title}</h3>
      {children}
    </div>
  );
}

function Tags({ title, items }: { title: string; items: string[] }) {
  return (
    <div style={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: radii.lg, padding: spacing["4"] }}>
      <h3 style={{ margin: "0 0 8px", fontSize: typography.size.lg, color: colors.textPrimary }}>{title} ({items.length})</h3>
      {items.length === 0 ? <Empty /> : (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          {items.map((v, i) => (
            <span key={i} style={{ padding: "2px 10px", background: colors.surfaceAlt, border: `1px solid ${colors.border}`, borderRadius: 9999, fontFamily: typography.family.mono, fontSize: 12, color: colors.textSecondary }}>{v}</span>
          ))}
        </div>
      )}
    </div>
  );
}

function Empty() {
  return <div style={{ color: colors.textMuted, fontSize: typography.size.sm }}>Sem dados no período.</div>;
}