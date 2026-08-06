import { useMemo, useState } from "react";
import { colors, radii, spacing, typography } from "../design-system/tokens";
import { SeverityBadge } from "../design-system/components/badges";
import { EmptyState, LoadingSkeleton } from "../design-system/components/feedback";
import { useAlerts } from "../hooks";
import type { RecentAlert } from "../hooks/useAlerts";
import type { SeverityColor } from "../design-system/tokens/colors";

const severityColor = (value: string): SeverityColor => value === "critical" ? "critical" : value === "high" ? "high" : value === "medium" ? "medium" : value === "low" ? "low" : "info";
const formatDate = (value: string) => value ? new Date(value).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "—";

function PendingAction({ children, label }: { children: React.ReactNode; label: string }) {
  return <span title="Integração pendente" style={{ display: "inline-flex", cursor: "not-allowed" }}><button type="button" disabled aria-label={label} style={{ padding: "7px 10px", border: `1px solid ${colors.border}`, borderRadius: radii.md, color: colors.textMuted, background: colors.surfaceAlt, fontFamily: typography.family.ui, fontSize: typography.size.xs, cursor: "not-allowed", opacity: .68 }}>{children}</button></span>;
}

export function TriagePage() {
  const { alerts, loading, error, refetch } = useAlerts(100);
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("all");
  const [source, setSource] = useState("all");
  const [rule, setRule] = useState("all");
  const [host, setHost] = useState("all");
  const [period, setPeriod] = useState("all");
  const [selected, setSelected] = useState<RecentAlert | null>(null);

  const origins = useMemo(() => Array.from(new Set(alerts.map((item) => item.source).filter(Boolean))).sort(), [alerts]);
  const rules = useMemo(() => Array.from(new Set(alerts.map((item) => item.rule).filter(Boolean))).sort(), [alerts]);
  const hosts = useMemo(() => Array.from(new Set(alerts.map((item) => item.host).filter(Boolean))).sort(), [alerts]);
  const visible = useMemo(() => alerts.filter((item) => {
    const text = `${item.title} ${item.source} ${item.host} ${item.rule}`.toLocaleLowerCase();
    const timestamp = item.firstSeen ? new Date(item.firstSeen).getTime() : 0;
    const periodMs = period === "24h" ? 86400000 : period === "7d" ? 604800000 : 0;
    return (!query || text.includes(query.toLocaleLowerCase())) && (severity === "all" || item.severity === severity) && (source === "all" || item.source === source) && (rule === "all" || item.rule === rule) && (host === "all" || item.host === host) && (!periodMs || timestamp >= Date.now() - periodMs);
  }), [alerts, query, severity, source, rule, host, period]);
  const awaiting = alerts.filter((item) => ["open", "in_progress"].includes(item.status)).length;
  const critical = alerts.filter((item) => item.severity === "critical").length;

  return <div style={{ display: "flex", flexDirection: "column", gap: spacing["4"] }}>
    <header style={{ display: "flex", alignItems: "end", justifyContent: "space-between", gap: spacing["4"], flexWrap: "wrap" }}><div><div style={eyebrow}>ALERT TRIAGE</div><h1 style={titleStyle}>Fila de triagem</h1><p style={subtitle}>Classificação e encaminhamento de alertas recebidos pelo SOC.</p></div><button type="button" onClick={refetch} style={refreshStyle}>Atualizar</button></header>
    <section className="triage-kpis" style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: spacing["3"] }}>
      <Metric label="Aguardando triagem" value={awaiting} color={colors.accent} context="Alertas abertos e em tratamento" />
      <Metric label="Críticos" value={critical} color={colors.severity.critical} context="Prioridade imediata" />
      <Metric label="SLA próximo" value="—" color={colors.severity.medium} context="Contrato de SLA pendente" />
      <Metric label="Atribuídos" value="—" color={colors.status.online} context="Contrato de atribuição pendente" />
    </section>
    <div className="triage-workspace" style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) 320px", minHeight: 620, overflow: "hidden", border: `1px solid ${colors.border}`, borderRadius: radii.xl, background: colors.surface }}>
      <section style={{ minWidth: 0, borderRight: `1px solid ${colors.border}` }}>
        <div className="triage-filters" style={{ display: "grid", gridTemplateColumns: "minmax(180px, 1.4fr) repeat(5, minmax(105px, .7fr))", gap: 8, padding: spacing["3"], borderBottom: `1px solid ${colors.borderSubtle}` }}>
          <input aria-label="Buscar alertas" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar título, host, regra…" style={fieldStyle} />
          <Filter label="Severidade" value={severity} onChange={setSeverity} options={["all", "critical", "high", "medium", "low", "info"]} />
          <Filter label="Origem" value={source} onChange={setSource} options={["all", ...origins]} />
          <Filter label="Regra" value={rule} onChange={setRule} options={["all", ...rules]} />
          <Filter label="Host" value={host} onChange={setHost} options={["all", ...hosts]} />
          <Filter label="Período" value={period} onChange={setPeriod} options={["all", "24h", "7d"]} labels={{ all: "Período", "24h": "Últimas 24h", "7d": "Últimos 7d" }} />
        </div>
        <div style={{ overflowX: "auto" }}><table style={{ width: "100%", minWidth: 980, borderCollapse: "collapse" }}><thead><tr>{["Severidade", "Título", "Origem", "Host", "Primeira ocorrência", "Score", "SLA", "Responsável"].map((label) => <th key={label} style={thStyle}>{label}</th>)}</tr></thead><tbody>{loading ? <tr><td colSpan={8} style={{ padding: spacing["4"] }}><LoadingSkeleton rows={5} /></td></tr> : error ? <tr><td colSpan={8}><EmptyState title="Fila indisponível" description={error} compact action={<button type="button" onClick={refetch} style={refreshStyle}>Tentar novamente</button>} /></td></tr> : visible.length === 0 ? <tr><td colSpan={8}><EmptyState title="Nenhum alerta na fila" description="A estrutura de triagem continua disponível. Novos alertas aparecerão nesta tabela." compact /></td></tr> : visible.map((item) => <tr key={item.id} onClick={() => setSelected(item)} className="triage-row" style={{ cursor: "pointer", background: selected?.id === item.id ? "color-mix(in srgb, var(--color-accent) 8%, transparent)" : "transparent" }}><td style={tdStyle}><SeverityBadge severity={severityColor(item.severity)}>{item.severity}</SeverityBadge></td><td style={tdStyle}><strong style={{ display: "block", color: colors.textPrimary, fontSize: typography.size.sm }}>{item.title}</strong><span style={{ display: "block", marginTop: 3, color: colors.textMuted, fontFamily: typography.family.mono, fontSize: 10 }}>{item.rule}</span></td><td style={tdStyle}>{item.source}</td><td style={tdStyle}>{item.host}</td><td style={tdStyle}>{formatDate(item.firstSeen)}</td><td style={{ ...tdStyle, fontFamily: typography.family.mono, color: item.riskScore >= 80 ? colors.severity.critical : colors.textSecondary }}>{item.riskScore}</td><td style={{ ...tdStyle, color: colors.textMuted }}>Pendente</td><td style={{ ...tdStyle, color: colors.textMuted }}>Pendente</td></tr>)}</tbody></table></div>
      </section>
      <aside className="triage-detail" style={{ display: "flex", flexDirection: "column", minWidth: 0, background: `linear-gradient(180deg, ${colors.surface} 0%, color-mix(in srgb, ${colors.background} 45%, ${colors.surface}) 100%)` }}>
        <div style={{ padding: spacing["4"], borderBottom: `1px solid ${colors.borderSubtle}` }}><div style={eyebrow}>DETAIL PANEL</div><h2 style={{ margin: "7px 0 0", color: colors.textPrimary, fontSize: typography.size.lg }}>Detalhes do alerta</h2></div>
        {!selected ? <EmptyState title="Nenhum alerta selecionado" description="Selecione uma linha da fila para revisar o contexto e as ações." compact /> : <div style={{ padding: spacing["4"], display: "flex", flexDirection: "column", gap: spacing["4"] }}><div><SeverityBadge severity={severityColor(selected.severity)}>{selected.severity}</SeverityBadge><h3 style={{ margin: "10px 0 5px", color: colors.textPrimary, fontSize: typography.size.base }}>{selected.title}</h3><span style={{ color: colors.textMuted, fontFamily: typography.family.mono, fontSize: 10 }}>{selected.id}</span></div><Detail label="Regra" value={selected.rule} /><Detail label="Origem" value={selected.source} /><Detail label="Host" value={selected.host} /><Detail label="MITRE" value={selected.mitre.length ? selected.mitre.join(", ") : "Não informado"} /><Detail label="Score de risco" value={String(selected.riskScore)} /><div style={{ paddingTop: spacing["3"], borderTop: `1px solid ${colors.borderSubtle}` }}><span style={{ display: "block", marginBottom: 8, color: colors.textMuted, fontSize: 10, letterSpacing: "0.1em" }}>AÇÕES DE TRIAGEM</span><div style={{ display: "flex", flexWrap: "wrap", gap: 7 }}><PendingAction label="Classificar alerta">Classificar</PendingAction><PendingAction label="Atribuir alerta">Atribuir</PendingAction><PendingAction label="Escalar alerta">Escalar</PendingAction><PendingAction label="Fechar alerta">Fechar</PendingAction></div></div></div>}
      </aside>
    </div>
    <style>{`.triage-row:hover { background: color-mix(in srgb, var(--color-accent) 5%, transparent) !important; } @media (max-width: 1120px) { .triage-workspace { grid-template-columns:1fr !important; } .triage-detail { border-top:1px solid var(--color-border); } .triage-filters { grid-template-columns:repeat(3,minmax(0,1fr)) !important; } .triage-filters > input { grid-column:span 3; } } @media (max-width: 640px) { .triage-kpis { grid-template-columns:repeat(2,minmax(0,1fr)) !important; } .triage-filters { grid-template-columns:1fr 1fr !important; } .triage-filters > input { grid-column:span 2; } }`}</style>
  </div>;
}

function Metric({ label, value, color, context }: { label: string; value: number | string; color: string; context: string }) { return <div style={{ padding: spacing["3"], border: `1px solid ${colors.border}`, borderTop: `2px solid ${color}`, borderRadius: radii.lg, background: `linear-gradient(145deg, color-mix(in srgb, ${color} 8%, ${colors.surface}) 0%, ${colors.surface} 72%)` }}><strong style={{ color: colors.textPrimary, fontFamily: typography.family.mono, fontSize: typography.size.xl }}>{value}</strong><span style={{ display: "block", marginTop: 5, color: colors.textSecondary, fontSize: typography.size.xs }}>{label}</span><span style={{ display: "block", marginTop: 3, color: colors.textMuted, fontSize: 10 }}>{context}</span></div>; }
function Filter({ label, value, onChange, options, labels = {} }: { label: string; value: string; onChange: (value: string) => void; options: string[]; labels?: Record<string, string> }) { return <select aria-label={label} value={value} onChange={(event) => onChange(event.target.value)} style={fieldStyle}>{options.map((item) => <option key={item} value={item}>{labels[item] || (item === "all" ? label : item)}</option>)}</select>; }
function Detail({ label, value }: { label: string; value: string }) { return <div><span style={{ display: "block", color: colors.textMuted, fontSize: 10, letterSpacing: "0.08em", textTransform: "uppercase" }}>{label}</span><span style={{ display: "block", marginTop: 4, color: colors.textSecondary, fontSize: typography.size.sm, wordBreak: "break-word" }}>{value}</span></div>; }
const eyebrow = { color: colors.accentHover, fontSize: 10, fontWeight: typography.weight.semibold, letterSpacing: "0.12em" };
const titleStyle = { margin: "6px 0 3px", color: colors.textPrimary, fontSize: typography.size["2xl"], letterSpacing: "-0.035em" };
const subtitle = { margin: 0, color: colors.textMuted, fontSize: typography.size.sm };
const fieldStyle = { minWidth: 0, width: "100%", boxSizing: "border-box" as const, padding: "9px 10px", border: `1px solid ${colors.border}`, borderRadius: radii.md, outline: "none", background: colors.background, color: colors.textPrimary, fontFamily: typography.family.ui, fontSize: typography.size.xs };
const refreshStyle = { padding: "8px 11px", border: `1px solid ${colors.border}`, borderRadius: radii.md, background: colors.surfaceAlt, color: colors.textPrimary, fontFamily: typography.family.ui, fontSize: typography.size.xs, fontWeight: typography.weight.semibold, cursor: "pointer" };
const thStyle = { padding: "11px 13px", borderBottom: `1px solid ${colors.border}`, textAlign: "left" as const, color: colors.textMuted, fontSize: 10, fontWeight: typography.weight.semibold, letterSpacing: "0.1em", textTransform: "uppercase" as const, whiteSpace: "nowrap" as const };
const tdStyle = { padding: "12px 13px", borderBottom: `1px solid ${colors.borderSubtle}`, color: colors.textSecondary, fontSize: typography.size.xs, verticalAlign: "middle" as const };