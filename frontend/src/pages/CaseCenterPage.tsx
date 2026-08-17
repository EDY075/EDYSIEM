import { useCallback, useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";
import { colors, radii, spacing, typography } from "../design-system/tokens";
import { Button } from "../design-system";
import { SeverityBadge, StatusBadge } from "../design-system/components/badges";
import { EmptyState, LoadingSkeleton } from "../design-system/components/feedback";
import { useCases } from "../hooks";
import type { Case } from "../hooks/useCases";
import { apiClient } from "../api/client";
import { useToast } from "../state/toast";
import type { SeverityColor } from "../design-system/tokens/colors";
import { useNavigate, useSearchParams } from "react-router-dom";

interface CaseInvestigation {
  related_alerts: { alert_id: string; title: string; severity: string; risk_score: number }[];
  iocs: string[];
  assets: string[];
  users: string[];
  mitre: string[];
  timeline: { action: string; detail: string; actor: string; created_at: string }[];
  evidence: { kind: string; value: string; label: string; source?: string }[];
}

const UUID4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

const toSeverity = (value: string): SeverityColor => value === "critical" ? "critical" : value === "high" ? "high" : value === "medium" ? "medium" : value === "low" ? "low" : "info";
const statusTone = (value: string) => value === "closed" || value === "resolved" ? "online" as const : value === "on_hold" ? "degraded" as const : "neutral" as const;
const formatDate = (value: string) => value ? new Date(value).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "—";

function shieldEvidenceContext(details: CaseInvestigation | null) {
  const sourceEvidence = details?.evidence.find((item) => item.source === "edy-shield" && item.kind === "json");
  if (!sourceEvidence || sourceEvidence.value.length > 250_000) return { asset: "", filePath: "" };
  try {
    const payload = JSON.parse(sourceEvidence.value) as Record<string, unknown>;
    const asset = payload.asset && typeof payload.asset === "object" ? payload.asset as Record<string, unknown> : {};
    const evidence = payload.evidence && typeof payload.evidence === "object" ? payload.evidence as Record<string, unknown> : {};
    return {
      asset: typeof asset.hostname === "string" ? asset.hostname.slice(0, 255) : "",
      filePath: typeof evidence.file_path === "string" ? evidence.file_path.slice(0, 4096) : "",
    };
  } catch {
    return { asset: "", filePath: "" };
  }
}

export function CaseCenterPage() {
  const { toast } = useToast();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const requestedCaseId = searchParams.get("case") || "";
  const { cases, loading, error, refetch } = useCases(100, requestedCaseId);
  const [selected, setSelected] = useState<Case | null>(null);
  const [details, setDetails] = useState<CaseInvestigation | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [comment, setComment] = useState("");
  const [evidence, setEvidence] = useState("");
  const [owner, setOwner] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!cases.length) return;
    if (requestedCaseId) {
      const requested = cases.find((item) => item.id === requestedCaseId);
      setSelected(requested ?? null);
      return;
    }
    if (!selected) setSelected(cases[0]);
  }, [cases, requestedCaseId, selected]);
  useEffect(() => { setOwner(selected?.owner ?? ""); }, [selected]);
  const loadDetails = useCallback(async (caseId: string) => {
    setDetailsLoading(true);
    setDetailsError("");
    const response = await apiClient.get<CaseInvestigation>(`/soc/cases/${encodeURIComponent(caseId)}/investigate`);
    if (response.success && response.data) setDetails(response.data);
    else setDetailsError("O contexto do caso está temporariamente indisponível. A fila foi preservada; tente novamente antes de decidir.");
    setDetailsLoading(false);
  }, []);
  useEffect(() => {
    if (!selected) return;
    setDetails(null);
    void loadDetails(selected.id);
  }, [loadDetails, selected]);

  const filteredCases = useMemo(() => cases.filter((item) => {
    const matchesQuery = `${item.id} ${item.title} ${item.owner} ${item.priority}`.toLowerCase().includes(query.toLowerCase().trim());
    const matchesStatus = status === "all" || item.status === status;
    return matchesQuery && matchesStatus;
  }), [cases, query, status]);
  const openCount = cases.filter((item) => !["resolved", "closed"].includes(item.status)).length;
  const highPriority = cases.filter((item) => ["critical", "high"].includes(item.severity)).length;
  const linkedShieldEventId = selected?.incidentId?.startsWith("shield-event:")
    ? selected.incidentId.slice("shield-event:".length)
    : "";
  const hasSafeShieldLink = UUID4.test(linkedShieldEventId);
  const shieldContext = shieldEvidenceContext(details);

  const post = async (path: string, params: Record<string, string>) => {
    if (!selected) return;
    setBusy(true);
    const result = await apiClient.post(`${path}?${new URLSearchParams(params).toString()}`);
    if (result.success) { toast("Atualização registrada", "success"); refetch(); await loadDetails(selected.id); }
    else toast(result.error?.message || "Não foi possível concluir a ação", "error");
    setBusy(false);
  };

  return <div style={{ display: "flex", flexDirection: "column", gap: spacing["4"] }}>
    <header style={{ display: "flex", justifyContent: "space-between", alignItems: "end", gap: spacing["4"], flexWrap: "wrap" }}><div><div style={eyebrow}>RESPONSE OPERATIONS</div><h1 style={pageTitle}>Central de cases</h1><p style={pageSubtitle}>Fila, ownership e evidências em uma única superfície operacional.</p></div><Button variant="ghost" onClick={refetch}>Atualizar fila</Button></header>
    {!loading && requestedCaseId && !cases.some((item) => item.id === requestedCaseId) && <div role="alert" className="case-context-warning">O caso solicitado não está nesta fila. Nenhuma seleção foi feita por inferência.</div>}
    <section className="case-summary" style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0,1fr))", gap: spacing["3"] }}>
      <Metric label="Casos na fila" value={cases.length} color={colors.accent} />
      <Metric label="Em tratamento" value={openCount} color={colors.severity.medium} />
      <Metric label="Prioridade alta" value={highPriority} color={colors.severity.critical} />
      <Metric label="Artefatos" value={cases.reduce((total, item) => total + item.evidenceCount + item.attachmentsCount, 0)} color={colors.status.online} />
    </section>
    <div className="cases-workspace" style={{ display: "grid", gridTemplateColumns: "minmax(0, 1.15fr) minmax(390px, .85fr)", overflow: "hidden", border: `1px solid ${colors.border}`, borderRadius: radii.xl, background: colors.surface }}>
      <section style={{ minWidth: 0, borderRight: `1px solid ${colors.border}` }}>
        <div style={{ display: "flex", gap: spacing["2"], padding: spacing["3"], borderBottom: `1px solid ${colors.borderSubtle}` }}><input aria-label="Buscar cases" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar ID, título ou owner…" style={inputStyle} /><select aria-label="Filtrar status dos cases" value={status} onChange={(event) => setStatus(event.target.value)} style={{ ...inputStyle, flex: "0 0 136px" }}><option value="all">Todos</option><option value="open">Abertos</option><option value="in_progress">Em tratamento</option><option value="on_hold">Em espera</option><option value="resolved">Resolvidos</option><option value="closed">Encerrados</option></select></div>
        <div style={{ overflowX: "auto" }}><table style={{ width: "100%", minWidth: 650, borderCollapse: "collapse" }}><thead><tr>{["Case", "Prioridade", "Owner", "Artefatos", "Status"].map((label) => <th key={label} style={{ padding: "11px 14px", borderBottom: `1px solid ${colors.border}`, color: colors.textMuted, fontSize: 10, textAlign: "left", textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: typography.weight.semibold }}>{label}</th>)}</tr></thead><tbody>{loading ? <tr><td colSpan={5} style={{ padding: spacing["4"] }}><LoadingSkeleton rows={5} /></td></tr> : error ? <tr><td colSpan={5}><EmptyState compact title="Fila indisponível" description={error} onRetry={refetch} /></td></tr> : filteredCases.length === 0 ? <tr><td colSpan={5}><EmptyState compact title="Nenhum case encontrado" description="Altere os filtros para revisar a fila." /></td></tr> : filteredCases.map((item) => <tr key={item.id} onClick={() => setSelected(item)} className="case-row" style={{ cursor: "pointer", background: selected?.id === item.id ? "color-mix(in srgb, var(--color-accent) 8%, transparent)" : "transparent", transition: "background 140ms ease" }}><td style={cellStyle}><span style={{ display: "block", color: colors.textMuted, fontFamily: typography.family.mono, fontSize: 10 }}>{item.id}</span><strong style={{ display: "block", marginTop: 4, maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: colors.textPrimary, fontSize: typography.size.sm }}>{item.title}</strong></td><td style={cellStyle}><SeverityBadge severity={toSeverity(item.severity)}>{item.priority}</SeverityBadge></td><td style={cellStyle}><span style={{ color: item.owner ? colors.textSecondary : colors.textMuted, fontSize: typography.size.xs }}>{item.owner || "Não atribuído"}</span></td><td style={cellStyle}><span style={{ color: colors.textSecondary, fontFamily: typography.family.mono, fontSize: typography.size.xs }}>{item.evidenceCount} ev. · {item.attachmentsCount} arq.</span></td><td style={cellStyle}><StatusBadge tone={statusTone(item.status)}>{item.statusLabel}</StatusBadge></td></tr>)}</tbody></table></div>
      </section>
      <section className="case-detail" style={{ minWidth: 0, display: "flex", flexDirection: "column", background: `linear-gradient(180deg, ${colors.surface} 0%, color-mix(in srgb, ${colors.background} 42%, ${colors.surface}) 100%)` }}>
        {!selected ? <EmptyState title="Selecione um case" description="Escolha um item na fila para abrir o contexto operacional." /> : <>
          <header style={{ padding: spacing["4"], borderBottom: `1px solid ${colors.borderSubtle}` }}><div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: spacing["3"] }}><div><span style={{ color: colors.textMuted, fontFamily: typography.family.mono, fontSize: 10 }}>{selected.id}</span><h2 style={{ margin: "5px 0", color: colors.textPrimary, fontSize: typography.size.lg }}>{selected.title}</h2><span style={{ color: colors.textMuted, fontSize: typography.size.xs }}>{selected.statusLabel} · criado {formatDate(selected.createdAt)}</span></div><SeverityBadge severity={toSeverity(selected.severity)}>{selected.severity}</SeverityBadge></div><div className="case-actions" style={{ display: "flex", gap: 8, marginTop: spacing["3"], flexWrap: "wrap" }}>{hasSafeShieldLink && <Button variant="ghost" onClick={() => navigate(`/investigate/shield/${encodeURIComponent(linkedShieldEventId)}`)}>Voltar à investigação</Button>}<Button variant="secondary" disabled={busy} onClick={() => post(`/soc/cases/${encodeURIComponent(selected.id)}/resolve`, { resolution: "incidente confirmado e tratado" })}>Resolver</Button><Button variant="danger" disabled={busy} onClick={() => post(`/soc/cases/${encodeURIComponent(selected.id)}/close`, { resolution: "encerrado pelo SOC" })}>Encerrar</Button></div></header>
          {detailsLoading ? <div style={{ padding: spacing["4"] }}><LoadingSkeleton rows={8} /></div> : detailsError ? <div style={{ padding: spacing["4"] }}><EmptyState title="Contexto indisponível" description={detailsError} onRetry={() => void loadDetails(selected.id)} /></div> : <div style={{ padding: spacing["4"], overflowY: "auto", display: "flex", flexDirection: "column", gap: spacing["4"] }}>
            {hasSafeShieldLink && <section className="case-shield-context" aria-label="Origem EDY Shield"><div><span>ORIGEM EDY SHIELD</span><strong>Evento preservado no caso</strong></div><dl><div><dt>event_id</dt><dd><code>{linkedShieldEventId}</code></dd></div>{shieldContext.asset && <div><dt>Ativo</dt><dd>{shieldContext.asset}</dd></div>}{shieldContext.filePath && <div><dt>Arquivo</dt><dd><code>{shieldContext.filePath}</code></dd></div>}</dl><Button variant="secondary" onClick={() => navigate(`/investigate/shield/${encodeURIComponent(linkedShieldEventId)}`)}>Revisar evento original</Button></section>}
            <section style={detailPanel}><PanelHeader title="Ownership" subtitle="Responsável e prioridade operacional" /><div style={{ display: "flex", gap: 8 }}><input aria-label="Responsável do case" value={owner} onChange={(event) => setOwner(event.target.value)} placeholder="analyst@edy" style={inputStyle} /><Button variant="secondary" disabled={busy || !owner.trim()} onClick={() => post(`/soc/cases/${encodeURIComponent(selected.id)}/assign`, { owner: owner.trim() })}>Atribuir</Button></div></section>
            <section style={detailPanel}><PanelHeader title="Registrar atividade" subtitle="Comentários e evidências entram na timeline do case" /><div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 8, marginBottom: 8 }}><input aria-label="Comentário do case" value={comment} onChange={(event) => setComment(event.target.value)} placeholder="Adicionar comentário operacional…" style={inputStyle} /><Button variant="primary" disabled={busy || !comment.trim()} onClick={() => { post(`/soc/cases/${encodeURIComponent(selected.id)}/comment`, { body: comment.trim() }); setComment(""); }}>Comentar</Button></div><div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 8 }}><input aria-label="Evidência do case" value={evidence} onChange={(event) => setEvidence(event.target.value)} placeholder="IOC, IP ou artefato…" style={inputStyle} /><Button variant="secondary" disabled={busy || !evidence.trim()} onClick={() => { post(`/soc/cases/${encodeURIComponent(selected.id)}/evidence`, { kind: "ioc", value: evidence.trim() }); setEvidence(""); }}>Anexar</Button></div></section>
            <div className="case-context-grid" style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(180px,.7fr)", gap: spacing["3"] }}><section style={detailPanel}><PanelHeader title="Timeline" subtitle={`${details?.timeline.length ?? 0} eventos registrados`} />{details?.timeline?.length ? <div>{details.timeline.map((item, index) => <div key={`${item.created_at}-${index}`} style={{ display: "grid", gridTemplateColumns: "70px 1fr", gap: 8, padding: "8px 0", borderBottom: index < details.timeline.length - 1 ? `1px solid ${colors.borderSubtle}` : "none" }}><span style={{ color: colors.textMuted, fontFamily: typography.family.mono, fontSize: 10 }}>{formatDate(item.created_at)}</span><span><strong style={{ display: "block", color: colors.textPrimary, fontSize: typography.size.xs }}>{item.action}</strong><span style={{ display: "block", marginTop: 2, color: colors.textSecondary, fontSize: typography.size.xs }}>{item.detail || item.actor}</span></span></div>)}</div> : <EmptyState compact title="Sem atividade" description="Comentários e ações aparecerão aqui." />}</section><section style={detailPanel}><PanelHeader title="Artefatos" subtitle={`${details?.evidence.length ?? 0} evidências`} />{details?.evidence?.length ? details.evidence.map((item, index) => <div key={`${item.label}-${index}`} className="case-evidence-item"><span>{item.source === "edy-shield" ? "EDY Shield" : item.kind}</span><strong>{item.label || "Evidência sem rótulo"}</strong>{item.kind === "json" ? <details><summary>Revisar payload validado</summary><pre>{item.value}</pre></details> : <code>{item.value}</code>}</div>) : <span style={{ color: colors.textMuted, fontSize: typography.size.xs }}>Nenhuma evidência.</span>}</section></div>
          </div>}
        </>}
      </section>
    </div>
    <style>{`.case-row:hover { background: color-mix(in srgb, var(--color-accent) 5%, transparent) !important; }.case-context-warning{padding:10px 12px;border:1px solid color-mix(in srgb,var(--severity-medium) 36%,var(--color-border));border-radius:7px;background:color-mix(in srgb,var(--severity-medium) 7%,var(--color-surface));color:var(--color-text-secondary);font-size:12px}.case-shield-context{display:grid;grid-template-columns:minmax(150px,.55fr) minmax(0,1fr) auto;align-items:center;gap:14px;padding:13px;border:1px solid color-mix(in srgb,var(--color-accent) 32%,var(--color-border));border-radius:8px;background:color-mix(in srgb,var(--color-accent) 6%,var(--color-surface))}.case-shield-context>div>span{display:block;color:var(--color-accent);font-size:9px;font-weight:700;letter-spacing:.1em}.case-shield-context>div>strong{display:block;margin-top:4px;color:var(--color-text-primary);font-size:12px}.case-shield-context dl{min-width:0;margin:0}.case-shield-context dl>div{display:grid;grid-template-columns:65px minmax(0,1fr);gap:8px;padding:3px 0}.case-shield-context dt{color:var(--color-text-muted);font-size:10px}.case-shield-context dd{min-width:0;margin:0;color:var(--color-text-secondary);font-size:10px;overflow-wrap:anywhere}.case-shield-context code{font-size:9px}.case-evidence-item{margin-bottom:10px;padding:9px;border:1px solid var(--color-border-subtle);border-radius:7px;background:var(--color-surface-alt)}.case-evidence-item>span{display:block;color:var(--color-accent);font-size:9px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}.case-evidence-item>strong{display:block;margin-top:4px;color:var(--color-text-primary);font-size:11px;overflow-wrap:anywhere}.case-evidence-item summary{margin-top:7px;color:var(--color-text-secondary);font-size:10px;cursor:pointer}.case-evidence-item pre,.case-evidence-item code{display:block;max-height:220px;margin:8px 0 0;padding:8px;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;border-radius:5px;background:var(--color-background);color:var(--color-text-secondary);font-size:9px}@media (max-width: 1120px) { .cases-workspace { grid-template-columns:1fr !important; } .cases-workspace > section:first-child { border-right:0 !important; border-bottom:1px solid var(--color-border) !important; } } @media (max-width: 980px) { .case-shield-context { grid-template-columns:1fr !important; align-items:start; } .case-shield-context > button { justify-self:start; } } @media (max-width: 680px) { .case-summary { grid-template-columns:repeat(2,minmax(0,1fr)) !important; } .case-context-grid { grid-template-columns:1fr !important; } .case-actions > button { flex:1; } }`}</style>
  </div>;
}

function Metric({ label, value, color }: { label: string; value: number; color: string }) { return <div style={{ padding: spacing["3"], border: `1px solid ${colors.border}`, borderRadius: radii.lg, background: `linear-gradient(145deg, color-mix(in srgb, ${color} 8%, ${colors.surface}) 0%, ${colors.surface} 70%)`, borderTop: `2px solid ${color}` }}><strong style={{ color: colors.textPrimary, fontFamily: typography.family.mono, fontSize: typography.size.xl }}>{value}</strong><span style={{ display: "block", marginTop: 4, color: colors.textMuted, fontSize: typography.size.xs }}>{label}</span></div>; }
function PanelHeader({ title, subtitle }: { title: string; subtitle: string }) { return <header style={{ marginBottom: spacing["3"] }}><strong style={{ display: "block", color: colors.textPrimary, fontSize: typography.size.sm }}>{title}</strong><span style={{ display: "block", marginTop: 2, color: colors.textMuted, fontSize: typography.size.xs }}>{subtitle}</span></header>; }
const eyebrow: CSSProperties = { color: colors.accentHover, fontSize: 10, fontWeight: typography.weight.semibold, letterSpacing: "0.12em" };
const pageTitle: CSSProperties = { margin: "6px 0 3px", color: colors.textPrimary, fontSize: typography.size["2xl"], letterSpacing: "-0.035em" };
const pageSubtitle: CSSProperties = { margin: 0, color: colors.textMuted, fontSize: typography.size.sm };
const inputStyle: CSSProperties = { flex: 1, minWidth: 0, padding: "9px 10px", border: `1px solid ${colors.border}`, borderRadius: radii.md, outline: "none", background: colors.background, color: colors.textPrimary, fontFamily: typography.family.ui, fontSize: typography.size.xs };
const cellStyle: CSSProperties = { padding: "12px 14px", borderBottom: `1px solid ${colors.borderSubtle}`, verticalAlign: "middle" };
const detailPanel: CSSProperties = { padding: spacing["3"], border: `1px solid ${colors.border}`, borderRadius: radii.lg, background: colors.surface };
