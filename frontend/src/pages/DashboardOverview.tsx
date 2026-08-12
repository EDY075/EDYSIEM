/** SOC Decision Center — a single, evidence-led queue built only from real APIs. */
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../api/client";
import { SeverityBadge } from "../design-system/components/badges";
import { EmptyState, skeletonCss } from "../design-system/components/feedback";
import { useAlerts, useHealth, useIncidents, useMetrics, useShieldEvents } from "../hooks";
import type { RecentAlert, ShieldDecisionEvent, SlaSnapshotDto } from "../hooks";
import type { Incident } from "../hooks/useIncidents";

type Severity = "critical" | "high" | "medium" | "low" | "info";
type QueueItem = {
  id: string;
  kind: "incident" | "shield" | "alert";
  severity: Severity;
  title: string;
  source: string;
  asset: string;
  evidence: string;
  owner: string;
  sla?: SlaSnapshotDto;
  createdAt: string;
  action: "assume" | "investigate" | "review";
};

const severityOrder: Record<Severity, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
const severityLabel: Record<Severity, string> = { critical: "Crítico", high: "Alto", medium: "Médio", low: "Baixo", info: "Informativo" };
const eventTitles: Record<string, string> = {
  "shield.alert.created": "Alerta de integridade criado",
  "shield.alert.updated": "Alerta de integridade atualizado",
  "shield.fim.file.added": "Arquivo adicionado",
  "shield.fim.file.modified": "Arquivo modificado",
  "shield.fim.file.removed": "Arquivo removido",
  "shield.fim.baseline.created": "Baseline de integridade criada",
  "shield.fim.scan.completed": "Scan de integridade concluído",
  "shield.hash.mismatch": "Hash divergente",
  "shield.hash.verified": "Hash verificado",
};

function formatDate(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Data não informada";
  return parsed.toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function formatDeadline(value?: string) {
  if (!value) return "";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "" : parsed.toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function slaRank(sla?: SlaSnapshotDto) {
  if (sla?.state === "overdue" || sla?.state === "missed") return 0;
  if (sla?.state === "warning") return 1;
  return 2;
}

function slaPresentation(item: QueueItem) {
  if (!item.sla) return { label: item.kind === "shield" ? "SLA inicia no caso" : "SLA não informado", tone: "neutral" };
  const deadline = formatDeadline(item.sla.deadline);
  if (item.sla.state === "overdue" || item.sla.state === "missed") return { label: `SLA vencido${deadline ? ` · ${deadline}` : ""}`, tone: "danger" };
  if (item.sla.state === "warning") return { label: `Próximo do SLA${deadline ? ` · ${deadline}` : ""}`, tone: "warning" };
  if (item.sla.state === "met") return { label: "SLA atendido", tone: "ok" };
  return { label: `Dentro do prazo${deadline ? ` · ${deadline}` : ""}`, tone: "ok" };
}

function incidentEvidence(incident: Incident) {
  const parts = [`${incident.alertsCount} alerta${incident.alertsCount === 1 ? "" : "s"}`];
  if (incident.iocs.length) parts.push(`${incident.iocs.length} IOC${incident.iocs.length === 1 ? "" : "s"}`);
  if (incident.mitre.length) parts.push(`${incident.mitre.length} técnica${incident.mitre.length === 1 ? "" : "s"} MITRE`);
  return parts.join(" · ");
}

function shieldEvidence(event: ShieldDecisionEvent) {
  const parts: string[] = [];
  if (event.evidence.file_path) parts.push(event.evidence.file_path);
  if (event.evidence.previous_hash && event.evidence.current_hash) parts.push("hash anterior × atual");
  else if (event.evidence.current_hash || event.evidence.previous_hash) parts.push("1 hash registrado");
  if (event.evidence.baseline_id) parts.push("baseline vinculada");
  if (event.evidence.scan_id) parts.push("scan vinculado");
  return parts.join(" · ") || "Evento recebido; evidência técnica no detalhe";
}

function alertEvidence(alert: RecentAlert) {
  const parts = [`Regra ${alert.rule}`];
  if (alert.mitre.length) parts.push(`${alert.mitre.length} técnica${alert.mitre.length === 1 ? "" : "s"} MITRE`);
  return parts.join(" · ");
}

export function DashboardOverview() {
  const navigate = useNavigate();
  const { incidents, loading: incidentsLoading, error: incidentsError, refetch: refetchIncidents } = useIncidents(50);
  const { alerts, loading: alertsLoading, error: alertsError, refetch: refetchAlerts } = useAlerts(50);
  const { events: shieldEvents, loading: shieldLoading, error: shieldError, refetch: refetchShield } = useShieldEvents(20);
  const { health, loading: healthLoading, error: healthError, refetch: refetchHealth } = useHealth();
  const { metrics, loading: metricsLoading, error: metricsError, refetch: refetchMetrics } = useMetrics();
  const [assuming, setAssuming] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const fallbackAlerts = incidents.length === 0 && shieldEvents.length === 0;
  const queue = useMemo<QueueItem[]>(() => {
    const items: QueueItem[] = incidents
      .filter((incident) => !["resolved", "closed"].includes(incident.status))
      .map((incident) => ({
        id: incident.id,
        kind: "incident",
        severity: incident.severity,
        title: incident.title,
        source: "Correlação EDY SIEM",
        asset: incident.assets.length ? incident.assets.join(", ") : "Ativo não informado",
        evidence: incidentEvidence(incident),
        owner: incident.owner || "",
        sla: incident.sla,
        createdAt: incident.created_at,
        action: incident.owner ? "investigate" : "assume",
      }));
    shieldEvents.forEach((event) => items.push({
      id: event.event_id,
      kind: "shield",
      severity: event.severity,
      title: eventTitles[event.event_type] || event.event_type,
      source: "EDY Shield",
      asset: event.asset.hostname || event.asset.asset_id || "Ativo não informado",
      evidence: shieldEvidence(event),
      owner: event.case?.owner || "",
      sla: event.case?.sla,
      createdAt: event.timestamp,
      action: "review",
    }));
    if (fallbackAlerts) alerts.filter((alert) => !["resolved", "closed", "false_positive"].includes(alert.status)).forEach((alert) => items.push({
      id: alert.id,
      kind: "alert",
      severity: alert.severity,
      title: alert.title,
      source: "Detecção EDY SIEM",
      asset: alert.host && alert.host !== "detection" ? alert.host : "Ativo não informado",
      evidence: alertEvidence(alert),
      owner: "",
      sla: alert.sla,
      createdAt: alert.firstSeen,
      action: "investigate",
    }));
    return items.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity] || slaRank(a.sla) - slaRank(b.sla) || Number(Boolean(a.owner)) - Number(Boolean(b.owner)) || new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()).slice(0, 10);
  }, [alerts, fallbackAlerts, incidents, shieldEvents]);

  const loading = incidentsLoading || alertsLoading || shieldLoading || healthLoading || metricsLoading;
  const dataError = incidentsError || alertsError || shieldError || healthError || metricsError;
  const criticalCount = queue.filter((item) => item.severity === "critical").length;
  const slaAttention = queue.filter((item) => ["overdue", "missed", "warning"].includes(item.sla?.state ?? "")).length;
  const unassigned = queue.filter((item) => !item.owner).length;
  const onlineComponents = Object.values(health).filter((status) => status === "online").length;
  const lastShieldEvent = shieldEvents[0];

  const retryAll = () => { refetchIncidents(); refetchAlerts(); refetchShield(); refetchHealth(); refetchMetrics(); };
  const openItem = (item: QueueItem) => {
    if (item.kind === "shield") navigate(`/investigate/shield/${encodeURIComponent(item.id)}`);
    else if (item.kind === "incident") navigate(`/incidents?incident=${encodeURIComponent(item.id)}`);
    else navigate("/alerts");
  };
  const assume = async (item: QueueItem) => {
    setAssuming(item.id); setActionError(null);
    const response = await apiClient.post(`/soc/incidents/${encodeURIComponent(item.id)}/assign?analyst=analista.soc`);
    if (response.success) refetchIncidents();
    else setActionError("Não foi possível assumir o incidente. Tente novamente.");
    setAssuming(null);
  };

  return <div className="decision-center" aria-busy={loading}>
    <style>{`${skeletonCss}
      .decision-center{display:flex;flex-direction:column;gap:16px;max-width:1680px;margin:0 auto}
      .decision-header{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;flex-wrap:wrap}
      .decision-eyebrow{color:var(--color-accent-hover);font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase}
      .decision-title{margin:6px 0 4px;color:var(--color-text-primary);font-size:28px;line-height:1.12;letter-spacing:-.04em}
      .decision-subtitle{margin:0;color:var(--color-text-muted);font-size:13px;line-height:1.5}
      .decision-refresh,.decision-action{border:1px solid var(--color-border);border-radius:7px;background:var(--color-surface-alt);color:var(--color-text-primary);font-size:12px;font-weight:600;cursor:pointer;transition:background 140ms ease,border-color 140ms ease,color 140ms ease}
      .decision-refresh{padding:8px 12px}.decision-refresh:hover,.decision-action:hover{border-color:var(--color-accent);color:var(--color-accent-hover)}
      .decision-health{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:18px;align-items:center;padding:13px 16px;border:1px solid var(--color-border);border-left:3px solid var(--status-online);border-radius:9px;background:linear-gradient(90deg,color-mix(in srgb,var(--status-online) 6%,var(--color-surface)) 0%,var(--color-surface) 55%)}
      .decision-health-main{display:flex;align-items:flex-start;gap:10px}.decision-health-dot{width:8px;height:8px;margin-top:5px;border-radius:50%;background:var(--status-online);box-shadow:0 0 0 3px color-mix(in srgb,var(--status-online) 12%,transparent);flex:none}
      .decision-health strong{display:block;color:var(--color-text-primary);font-size:13px}.decision-health p{margin:3px 0 0;color:var(--color-text-muted);font-size:11px;line-height:1.45}
      .decision-health-meta{text-align:right;color:var(--color-text-muted);font:10px 'JetBrains Mono',monospace;line-height:1.6}
      .decision-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid var(--color-border);border-radius:9px;background:var(--color-surface);overflow:hidden}
      .decision-signal{padding:13px 16px;border-right:1px solid var(--color-border-subtle)}.decision-signal:last-child{border-right:0}.decision-signal strong{display:block;color:var(--color-text-primary);font:700 22px 'JetBrains Mono',monospace}.decision-signal span{display:block;margin-top:3px;color:var(--color-text-muted);font-size:11px}
      .decision-queue{overflow:hidden;border:1px solid var(--color-border);border-radius:10px;background:var(--color-surface)}
      .decision-queue-head{display:flex;align-items:flex-end;justify-content:space-between;gap:14px;padding:15px 17px;border-bottom:1px solid var(--color-border)}.decision-queue-head h2{margin:0;color:var(--color-text-primary);font-size:16px}.decision-queue-head p{margin:3px 0 0;color:var(--color-text-muted);font-size:11px}.decision-queue-count{color:var(--color-text-muted);font:10px 'JetBrains Mono',monospace;white-space:nowrap}
      .decision-row{display:grid;grid-template-columns:minmax(250px,1.35fr) minmax(145px,.65fr) minmax(210px,1fr) minmax(135px,.65fr) minmax(150px,.72fr) 150px;gap:14px;align-items:center;min-height:96px;padding:14px 17px;border-bottom:1px solid var(--color-border-subtle);position:relative}.decision-row:last-child{border-bottom:0}.decision-row::before{content:'';position:absolute;left:0;top:14px;bottom:14px;width:2px;background:var(--row-tone)}
      .decision-primary{min-width:0}.decision-primary-top{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.decision-source{display:inline-flex;padding:3px 7px;border:1px solid color-mix(in srgb,var(--color-accent) 32%,var(--color-border));border-radius:999px;background:var(--color-accent-subtle);color:var(--color-accent-hover);font-size:9px;font-weight:700;letter-spacing:.05em;text-transform:uppercase}.decision-primary h3{margin:8px 0 3px;overflow:hidden;text-overflow:ellipsis;color:var(--color-text-primary);font-size:13px;line-height:1.35}.decision-id{display:block;overflow:hidden;text-overflow:ellipsis;color:var(--color-text-muted);font:9px 'JetBrains Mono',monospace;white-space:nowrap}
      .decision-cell{min-width:0}.decision-label{display:block;margin-bottom:5px;color:var(--color-text-subtle);font-size:9px;font-weight:700;letter-spacing:.09em;text-transform:uppercase}.decision-value{display:block;overflow:hidden;text-overflow:ellipsis;color:var(--color-text-secondary);font-size:11px;line-height:1.45}.decision-value.mono{font-family:'JetBrains Mono',monospace;font-size:10px}.decision-evidence{display:-webkit-box;overflow:hidden;-webkit-box-orient:vertical;-webkit-line-clamp:2}.decision-owner.unassigned{color:var(--severity-medium)}
      .decision-sla{display:inline-flex;padding:4px 7px;border:1px solid var(--color-border);border-radius:5px;color:var(--color-text-secondary);font-size:10px;line-height:1.35}.decision-sla[data-tone='danger']{border-color:color-mix(in srgb,var(--severity-critical) 36%,var(--color-border));background:color-mix(in srgb,var(--severity-critical) 9%,transparent);color:var(--severity-critical)}.decision-sla[data-tone='warning']{border-color:color-mix(in srgb,var(--severity-medium) 38%,var(--color-border));background:color-mix(in srgb,var(--severity-medium) 8%,transparent);color:var(--severity-medium)}.decision-sla[data-tone='ok']{color:var(--status-online)}
      .decision-next{text-align:right}.decision-next-label{display:block;margin-bottom:6px;color:var(--color-text-muted);font-size:9px}.decision-action{width:100%;padding:8px 9px;background:transparent}.decision-action.primary{border-color:var(--color-accent);background:var(--color-accent);color:var(--color-text-on-accent)}.decision-action:disabled{cursor:wait;opacity:.55}
      .decision-error{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:10px 13px;border:1px solid color-mix(in srgb,var(--severity-medium) 36%,var(--color-border));border-radius:8px;background:color-mix(in srgb,var(--severity-medium) 8%,transparent);color:var(--color-text-secondary);font-size:12px}
      .decision-context{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;overflow:hidden;border:1px solid var(--color-border);border-radius:9px;background:var(--color-border-subtle)}.decision-context-item{padding:13px 15px;background:var(--color-surface)}.decision-context-item strong{display:block;color:var(--color-text-primary);font-size:12px}.decision-context-item span{display:block;margin-top:4px;color:var(--color-text-muted);font-size:10px;line-height:1.45}
      @media(max-width:1500px){.decision-row{grid-template-columns:minmax(230px,1.2fr) minmax(130px,.7fr) minmax(190px,1fr) minmax(135px,.7fr) 150px}.decision-row>.decision-cell:nth-of-type(4){display:none}}
      @media(max-width:1000px){.decision-row{grid-template-columns:minmax(0,1fr) 150px}.decision-row>.decision-cell:nth-of-type(2),.decision-row>.decision-cell:nth-of-type(4){display:none}.decision-context{grid-template-columns:1fr}.decision-summary{grid-template-columns:repeat(2,minmax(0,1fr))}.decision-signal:nth-child(2){border-right:0}.decision-signal:nth-child(-n+2){border-bottom:1px solid var(--color-border-subtle)}}
      @media(max-width:680px){.decision-center{gap:12px}.decision-title{font-size:23px}.decision-health{grid-template-columns:1fr}.decision-health-meta{text-align:left}.decision-row{grid-template-columns:1fr;gap:10px;padding:14px 15px}.decision-row>.decision-cell{display:block!important}.decision-row>.decision-cell:nth-of-type(4){display:none!important}.decision-next{text-align:left}.decision-action{width:auto}.decision-queue-head{align-items:flex-start}.decision-summary{overflow:visible}.decision-signal{padding:11px 12px}.decision-signal strong{font-size:18px}}
    `}</style>

    <header className="decision-header">
      <div><div className="decision-eyebrow">SOC Decision Center</div><h1 className="decision-title">Decisões que exigem ação</h1><p className="decision-subtitle">Prioridade, prazo, ownership, ativo e evidência em uma única fila operacional.</p></div>
      <button type="button" className="decision-refresh" onClick={retryAll}>Atualizar dados</button>
    </header>

    <section className="decision-health" aria-label="Saúde operacional e ingestão">
      <div className="decision-health-main"><span className="decision-health-dot" /><div><strong>{healthError ? "Saúde operacional indisponível" : "SOC operacional · receptor Shield disponível"}</strong><p>{shieldError ? "Não foi possível consultar a fonte EDY Shield. A fila SOC permanece disponível com os demais dados." : lastShieldEvent ? `Último evento EDY Shield recebido em ${formatDate(lastShieldEvent.received_at)}. A ausência de tráfego novo não interrompe investigação e casos.` : "Nenhum evento EDY Shield recebido. Conecte uma fonte em Configurações quando quiser iniciar a ingestão."}</p></div></div>
      <div className="decision-health-meta"><span>{onlineComponents} componentes reportados online</span><br /><span>{shieldEvents.length} eventos Shield na janela da fila</span></div>
    </section>

    <section className="decision-summary" aria-label="Resumo da fila de decisão">
      <div className="decision-signal"><strong>{queue.length}</strong><span>decisões visíveis</span></div>
      <div className="decision-signal"><strong style={{ color: criticalCount ? "var(--severity-critical)" : undefined }}>{criticalCount}</strong><span>críticas agora</span></div>
      <div className="decision-signal"><strong style={{ color: slaAttention ? "var(--severity-medium)" : undefined }}>{slaAttention}</strong><span>SLA vencido ou próximo</span></div>
      <div className="decision-signal"><strong>{unassigned}</strong><span>sem responsável</span></div>
    </section>

    {(dataError || actionError) && <div className="decision-error" role="alert"><span>{actionError || "Parte dos dados operacionais está indisponível. A fila mostra apenas as fontes carregadas com sucesso."}</span><button type="button" className="decision-refresh" onClick={retryAll}>Tentar novamente</button></div>}

    <section className="decision-queue">
      <header className="decision-queue-head"><div><h2>Decision Queue</h2><p>Crítico → alto → SLA em risco → sem responsável → demais eventos</p></div><span className="decision-queue-count">{queue.length} de {incidents.length + shieldEvents.length + (fallbackAlerts ? alerts.length : 0)} itens</span></header>
      {loading && !queue.length ? <div style={{ padding: 18 }}>{Array.from({ length: 4 }).map((_, index) => <div key={index} className="skeleton-line" style={{ height: 72, marginBottom: 10 }} />)}</div> : !queue.length ? <EmptyState title="Fila de decisão vazia" description="Não há incidentes ativos, eventos Shield ou alertas aguardando decisão." /> : queue.map((item) => {
        const sla = slaPresentation(item);
        const rowTone = item.severity === "critical" ? "var(--severity-critical)" : item.severity === "high" ? "var(--severity-high)" : item.severity === "medium" ? "var(--severity-medium)" : "var(--severity-low)";
        return <article className="decision-row" key={`${item.kind}:${item.id}`} style={{ "--row-tone": rowTone } as React.CSSProperties}>
          <div className="decision-primary"><div className="decision-primary-top"><SeverityBadge severity={item.severity}>{severityLabel[item.severity]}</SeverityBadge><span className="decision-source">{item.source}</span></div><h3 title={item.title}>{item.title}</h3><span className="decision-id">{item.id} · {formatDate(item.createdAt)}</span></div>
          <div className="decision-cell"><span className="decision-label">Ativo afetado</span><span className="decision-value mono" title={item.asset}>{item.asset}</span></div>
          <div className="decision-cell"><span className="decision-label">Evidência</span><span className="decision-value decision-evidence" title={item.evidence}>{item.evidence}</span></div>
          <div className="decision-cell"><span className="decision-label">Responsável</span><span className={`decision-value decision-owner ${item.owner ? "" : "unassigned"}`}>{item.owner || "Sem responsável"}</span></div>
          <div className="decision-cell"><span className="decision-label">SLA</span><span className="decision-sla" data-tone={sla.tone}>{sla.label}</span></div>
          <div className="decision-next"><span className="decision-next-label">Próxima ação</span><button type="button" className={`decision-action ${item.kind === "shield" ? "primary" : ""}`} disabled={assuming === item.id} onClick={() => item.action === "assume" ? assume(item) : openItem(item)}>{assuming === item.id ? "Assumindo…" : item.action === "assume" ? "Assumir" : item.action === "review" ? "Revisar evidência" : "Continuar investigação"}</button></div>
        </article>;
      })}
    </section>

    <section className="decision-context" aria-label="Contexto operacional preservado">
      <div className="decision-context-item"><strong>{metrics.activeAlerts} alertas ativos</strong><span>Detecções permanecem disponíveis na Central de Alertas, sem duplicar o mesmo sinal nesta Home.</span></div>
      <div className="decision-context-item"><strong>{metrics.openCases} casos abertos</strong><span>Ownership, tarefas, evidências e encerramento continuam no sistema de casos existente.</span></div>
      <div className="decision-context-item"><strong>{metrics.eventsLast24h} eventos nas últimas 24h</strong><span>Volume preservado como contexto; a fila acima prioriza decisão em vez de gráficos decorativos.</span></div>
    </section>
  </div>;
}
