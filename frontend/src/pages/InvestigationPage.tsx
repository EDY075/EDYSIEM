import { useEffect, useMemo, useState } from "react";
import { colors, radii, spacing, typography } from "../design-system/tokens";
import { EmptyState, LoadingSkeleton } from "../design-system/components/feedback";
import { SeverityBadge } from "../design-system/components/badges";
import type { SeverityColor } from "../design-system/tokens/colors";
import { useCases } from "../hooks";
import type { Case } from "../hooks/useCases";
import { apiClient } from "../api/client";

interface InvestigationData {
  case_id: string;
  related_alerts: { alert_id: string; title: string; rule_id: string; severity: string; risk_score: number }[];
  iocs: string[];
  assets: string[];
  users: string[];
  mitre: string[];
  timeline: { action: string; detail: string; created_at: string }[];
}

const formatTime = (value: string) => value ? new Date(value).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "Sem horário";
const severityTone = (value: string): SeverityColor => value === "critical" ? "critical" : value === "high" ? "high" : value === "medium" ? "medium" : value === "low" ? "low" : "info";

function InvestigationGlyph({ type }: { type: "trace" | "evidence" | "link" | "mitre" }) {
  const common = { fill: "none", stroke: "currentColor", strokeWidth: 1.75, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  const path = type === "trace" ? <><circle cx="12" cy="12" r="8" /><path d="M12 7v5l3.5 2" /></> : type === "evidence" ? <><path d="M6 3h9l3 3v15H6V3Z" /><path d="M9 11h6M9 15h5" /></> : type === "link" ? <><path d="M10 13a5 5 0 0 0 7.1.1l2-2a5 5 0 0 0-7.1-7.1l-1.2 1.2" /><path d="M14 11a5 5 0 0 0-7.1-.1l-2 2A5 5 0 0 0 12 20l1.2-1.2" /></> : <><circle cx="12" cy="12" r="8" /><path d="m12 4 2.4 5.1L20 10l-4 3.8.9 5.4-4.9-2.7-4.9 2.7.9-5.4L4 10l5.6-.9L12 4Z" /></>;
  return <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true" {...common}>{path}</svg>;
}

export function InvestigationPage() {
  const { cases, loading: casesLoading, error: casesError } = useCases(60);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [investigation, setInvestigation] = useState<InvestigationData | null>(null);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("");

  useEffect(() => { if (!selectedCase && cases[0]) setSelectedCase(cases[0]); }, [cases, selectedCase]);
  useEffect(() => {
    if (!selectedCase) return;
    let active = true;
    setLoading(true);
    setInvestigation(null);
    apiClient.get<InvestigationData>(`/soc/cases/${selectedCase.id}/investigate`).then((response) => {
      if (active && response.success && response.data) setInvestigation(response.data);
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [selectedCase]);

  const visibleCases = useMemo(() => {
    const normalized = filter.trim().toLowerCase();
    if (!normalized) return cases;
    return cases.filter((item) => `${item.id} ${item.title} ${item.owner} ${item.statusLabel}`.toLowerCase().includes(normalized));
  }, [cases, filter]);

  const relationshipCount = (investigation?.related_alerts.length ?? 0) + (investigation?.iocs.length ?? 0) + (investigation?.assets.length ?? 0) + (investigation?.users.length ?? 0) + (investigation?.mitre.length ?? 0);

  return <div className="investigation-workspace" style={{ display: "grid", gridTemplateColumns: "300px minmax(0, 1fr) 300px", minHeight: 650, overflow: "hidden", border: `1px solid ${colors.border}`, borderRadius: radii.xl, background: colors.surface, boxShadow: "0 16px 38px color-mix(in srgb, var(--color-text-primary) 7%, transparent)" }}>
    <aside className="investigation-queue" style={{ display: "flex", flexDirection: "column", minWidth: 0, borderRight: `1px solid ${colors.border}` }}>
      <div style={{ padding: spacing["4"], borderBottom: `1px solid ${colors.borderSubtle}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, color: colors.accentHover, fontSize: 10, fontWeight: typography.weight.semibold, letterSpacing: "0.12em" }}><InvestigationGlyph type="trace" /> INVESTIGATION QUEUE</div>
        <h1 style={{ margin: "8px 0 4px", color: colors.textPrimary, fontSize: typography.size.xl, letterSpacing: "-0.025em" }}>Investigações</h1>
        <p style={{ margin: 0, color: colors.textMuted, fontSize: typography.size.xs, lineHeight: 1.45 }}>Selecione um caso para abrir a cadeia de evidências.</p>
      </div>
      <div style={{ padding: spacing["3"], borderBottom: `1px solid ${colors.borderSubtle}` }}><input aria-label="Filtrar casos" value={filter} onChange={(event) => setFilter(event.target.value)} placeholder="Filtrar por caso, owner…" style={{ width: "100%", boxSizing: "border-box", padding: "9px 10px", border: `1px solid ${colors.border}`, borderRadius: radii.md, background: colors.background, color: colors.textPrimary, outline: "none", fontSize: typography.size.xs }} /></div>
      <div style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: spacing["2"] }}>
        {casesLoading ? <LoadingSkeleton rows={5} /> : casesError ? <EmptyState compact title="Fila indisponível" description={casesError} /> : visibleCases.length === 0 ? <EmptyState compact title="Nenhum caso encontrado" description="Ajuste o filtro para ver a fila." /> : visibleCases.map((item) => {
          const active = selectedCase?.id === item.id;
          return <button key={item.id} type="button" onClick={() => setSelectedCase(item)} className="investigation-case" style={{ width: "100%", display: "block", marginBottom: 6, padding: spacing["3"], border: `1px solid ${active ? colors.accent : colors.borderSubtle}`, borderLeft: `3px solid ${active ? colors.accent : "transparent"}`, borderRadius: radii.md, background: active ? "color-mix(in srgb, var(--color-accent) 9%, var(--color-surface-alt))" : "transparent", color: colors.textPrimary, textAlign: "left", cursor: "pointer", transition: "background 140ms ease, border-color 140ms ease, transform 140ms ease" }}>
            <span style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}><span style={{ color: colors.textMuted, fontFamily: typography.family.mono, fontSize: 10 }}>{item.id}</span><SeverityBadge severity={severityTone(item.severity)}>{item.priority}</SeverityBadge></span>
            <span style={{ display: "block", marginTop: 6, color: colors.textPrimary, fontSize: typography.size.sm, fontWeight: typography.weight.semibold, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.title}</span>
            <span style={{ display: "block", marginTop: 5, color: colors.textMuted, fontSize: typography.size.xs }}>{item.owner || "Sem owner"} · {item.statusLabel}</span>
          </button>;
        })}
      </div>
    </aside>

    <section className="investigation-main" style={{ minWidth: 0, display: "flex", flexDirection: "column", background: `linear-gradient(180deg, ${colors.surface} 0%, color-mix(in srgb, ${colors.background} 48%, ${colors.surface}) 100%)` }}>
      {!selectedCase ? <EmptyState title="Selecione uma investigação" description="A fila à esquerda contém os casos disponíveis para análise." /> : <>
        <header style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: spacing["3"], padding: `${spacing["4"]} ${spacing["5"]}`, borderBottom: `1px solid ${colors.borderSubtle}` }}>
          <div><div style={{ color: colors.textMuted, fontFamily: typography.family.mono, fontSize: 10 }}>{selectedCase.id} · {selectedCase.statusLabel}</div><h2 style={{ margin: "6px 0 4px", color: colors.textPrimary, fontSize: typography.size.xl, letterSpacing: "-0.025em" }}>{selectedCase.title}</h2><span style={{ color: colors.textMuted, fontSize: typography.size.xs }}>Owner: {selectedCase.owner || "não atribuído"} · Prioridade {selectedCase.priority}</span></div>
          <SeverityBadge severity={severityTone(selectedCase.severity)}>{selectedCase.severity}</SeverityBadge>
        </header>
        {loading ? <div style={{ padding: spacing["5"] }}><LoadingSkeleton rows={10} variant="card" /></div> : !investigation ? <EmptyState title="Dados de investigação indisponíveis" description="Não foi possível carregar a correlação deste caso." /> : <div style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: spacing["5"] }}>
          <div className="investigation-summary" style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: spacing["3"], marginBottom: spacing["5"] }}>
            {[{ label: "Evidências", value: investigation.timeline.length, type: "evidence" as const, color: colors.accent }, { label: "Alertas", value: investigation.related_alerts.length, type: "trace" as const, color: colors.severity.critical }, { label: "IOCs", value: investigation.iocs.length, type: "link" as const, color: colors.severity.medium }, { label: "MITRE", value: investigation.mitre.length, type: "mitre" as const, color: colors.status.online }].map((metric) => <div key={metric.label} style={{ padding: spacing["3"], border: `1px solid ${colors.border}`, borderRadius: radii.lg, background: colors.surface }}><span style={{ display: "inline-flex", color: metric.color }}><InvestigationGlyph type={metric.type} /></span><strong style={{ display: "block", marginTop: 8, color: colors.textPrimary, fontFamily: typography.family.mono, fontSize: typography.size.xl }}>{metric.value}</strong><span style={{ display: "block", marginTop: 2, color: colors.textMuted, fontSize: typography.size.xs }}>{metric.label}</span></div>)}
          </div>
          <div className="investigation-detail-grid" style={{ display: "grid", gridTemplateColumns: "minmax(0, 1.2fr) minmax(260px, .8fr)", gap: spacing["4"] }}>
            <Panel title="Timeline de evidências" subtitle="Sequência registrada na cadeia do caso" icon="trace"><div>{investigation.timeline.length === 0 ? <EmptyState compact title="Sem eventos registrados" description="A timeline será preenchida pela operação do caso." /> : investigation.timeline.map((event, index) => <div key={`${event.created_at}-${index}`} style={{ display: "grid", gridTemplateColumns: "72px 18px minmax(0, 1fr)", gap: spacing["2"], minHeight: 66 }}><span style={{ paddingTop: 2, color: colors.textMuted, fontFamily: typography.family.mono, fontSize: 10 }}>{formatTime(event.created_at)}</span><span style={{ position: "relative", display: "flex", justifyContent: "center" }}><span style={{ position: "relative", zIndex: 1, width: 8, height: 8, marginTop: 4, borderRadius: "50%", background: colors.accent, boxShadow: `0 0 0 3px color-mix(in srgb, ${colors.accent} 15%, transparent)` }} />{index < investigation.timeline.length - 1 && <span style={{ position: "absolute", top: 15, bottom: -4, width: 1, background: colors.border }} />}</span><span style={{ paddingBottom: spacing["3"], borderBottom: index < investigation.timeline.length - 1 ? `1px solid ${colors.borderSubtle}` : "none" }}><strong style={{ display: "block", color: colors.textPrimary, fontSize: typography.size.sm }}>{event.action}</strong><span style={{ display: "block", marginTop: 3, color: colors.textSecondary, fontSize: typography.size.xs, lineHeight: 1.45 }}>{event.detail}</span></span></div>)}</div></Panel>
            <Panel title="Alertas correlacionados" subtitle="Detecções que sustentam esta análise" icon="evidence"><div style={{ display: "flex", flexDirection: "column", gap: 8 }}>{investigation.related_alerts.length === 0 ? <EmptyState compact title="Sem alertas associados" description="Não há alertas correlacionados a este caso." /> : investigation.related_alerts.map((alert) => <div key={alert.alert_id} style={{ padding: spacing["3"], border: `1px solid ${colors.borderSubtle}`, borderRadius: radii.md, background: colors.surfaceAlt }}><div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}><strong style={{ color: colors.textPrimary, fontSize: typography.size.sm }}>{alert.title}</strong><SeverityBadge severity={severityTone(alert.severity)}>{alert.severity}</SeverityBadge></div><div style={{ marginTop: 7, color: colors.textMuted, fontFamily: typography.family.mono, fontSize: 10 }}>{alert.rule_id} · risco {alert.risk_score}</div></div>)}</div></Panel>
          </div>
        </div>}
      </>}
    </section>

    <aside className="investigation-correlation" style={{ minWidth: 0, borderLeft: `1px solid ${colors.border}`, background: colors.surface }}>
      <div style={{ padding: spacing["4"], borderBottom: `1px solid ${colors.borderSubtle}` }}><div style={{ display: "flex", alignItems: "center", gap: 8, color: colors.accentHover, fontSize: 10, fontWeight: typography.weight.semibold, letterSpacing: "0.12em" }}><InvestigationGlyph type="link" /> CORRELATION</div><strong style={{ display: "block", marginTop: 8, color: colors.textPrimary, fontFamily: typography.family.mono, fontSize: typography.size.xl }}>{relationshipCount}</strong><span style={{ color: colors.textMuted, fontSize: typography.size.xs }}>Relacionamentos observados</span></div>
      <div style={{ padding: spacing["3"], display: "flex", flexDirection: "column", gap: spacing["4"], overflowY: "auto" }}>
        <CorrelationGroup title="IOCs" items={investigation?.iocs ?? []} color={colors.severity.medium} />
        <CorrelationGroup title="MITRE ATT&CK" items={investigation?.mitre ?? []} color={colors.accent} />
        <CorrelationGroup title="Ativos" items={investigation?.assets ?? []} color={colors.status.online} />
        <CorrelationGroup title="Usuários" items={investigation?.users ?? []} color={colors.textSecondary} />
      </div>
    </aside>
    <style>{`.investigation-case:hover { transform: translateX(1px); background: color-mix(in srgb, var(--color-accent) 6%, var(--color-surface-alt)) !important; } @media (max-width: 1180px) { .investigation-workspace { grid-template-columns: 270px minmax(0,1fr) !important; } .investigation-correlation { display:none; } } @media (max-width: 820px) { .investigation-workspace { grid-template-columns: 1fr !important; overflow: visible !important; } .investigation-queue { max-height: 300px; border-right:0 !important; border-bottom:1px solid var(--color-border) !important; } .investigation-summary { grid-template-columns: repeat(2,minmax(0,1fr)) !important; } .investigation-detail-grid { grid-template-columns:1fr !important; } }`}</style>
  </div>;
}

function Panel({ title, subtitle, icon, children }: { title: string; subtitle: string; icon: "trace" | "evidence"; children: React.ReactNode }) {
  return <section style={{ border: `1px solid ${colors.border}`, borderRadius: radii.lg, overflow: "hidden", background: colors.surface }}><header style={{ display: "flex", alignItems: "flex-start", gap: spacing["2"], padding: spacing["3"], borderBottom: `1px solid ${colors.borderSubtle}` }}><span style={{ color: colors.accent, display: "inline-flex", marginTop: 1 }}><InvestigationGlyph type={icon} /></span><span><strong style={{ display: "block", color: colors.textPrimary, fontSize: typography.size.sm }}>{title}</strong><span style={{ display: "block", marginTop: 2, color: colors.textMuted, fontSize: typography.size.xs }}>{subtitle}</span></span></header><div style={{ padding: spacing["3"] }}>{children}</div></section>;
}

function CorrelationGroup({ title, items, color }: { title: string; items: string[]; color: string }) {
  return <section><div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}><span style={{ color: colors.textSecondary, fontSize: typography.size.xs, fontWeight: typography.weight.semibold }}>{title}</span><span style={{ color, fontFamily: typography.family.mono, fontSize: 10 }}>{items.length}</span></div>{items.length === 0 ? <span style={{ color: colors.textMuted, fontSize: typography.size.xs }}>Nenhum vínculo.</span> : <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>{items.map((item) => <span key={item} style={{ maxWidth: "100%", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", padding: "5px 7px", color, background: `color-mix(in srgb, ${color} 9%, transparent)`, border: `1px solid color-mix(in srgb, ${color} 22%, transparent)`, borderRadius: 5, fontFamily: typography.family.mono, fontSize: 10 }}>{item}</span>)}</div>}</section>;
}