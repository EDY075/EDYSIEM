/** SOC Decision Center — a single, evidence-led queue built only from real APIs. */
import { useMemo, useRef, useState } from "react";
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
  status: string;
  sla?: SlaSnapshotDto;
  createdAt: string;
  action: "assume" | "investigate" | "review";
};

type QueueFilters = {
  severity: "all" | Severity;
  source: "all" | QueueItem["kind"];
  sla: "all" | "overdue" | "warning" | "ok" | "none";
  ownership: "all" | "assigned" | "unassigned";
  status: string;
};

const defaultFilters: QueueFilters = {
  severity: "all",
  source: "all",
  sla: "all",
  ownership: "all",
  status: "all",
};
const CURRENT_ANALYST = "analista.soc";

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

function priorityBand(item: QueueItem) {
  if (item.severity === "critical") return 0;
  if (item.severity === "high") return 1;
  if (item.sla?.state === "overdue" || item.sla?.state === "missed") return 2;
  if (item.sla?.state === "warning") return 3;
  if (!item.owner) return 4;
  return 5;
}

function deadlineTime(sla?: SlaSnapshotDto) {
  if (!sla?.deadline) return Number.POSITIVE_INFINITY;
  const value = new Date(sla.deadline).getTime();
  return Number.isNaN(value) ? Number.POSITIVE_INFINITY : value;
}

function compareQueueItems(a: QueueItem, b: QueueItem) {
  return priorityBand(a) - priorityBand(b)
    || slaRank(a.sla) - slaRank(b.sla)
    || deadlineTime(a.sla) - deadlineTime(b.sla)
    || severityOrder[a.severity] - severityOrder[b.severity]
    || Number(Boolean(a.owner)) - Number(Boolean(b.owner))
    || new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    || a.id.localeCompare(b.id);
}

function durationLabel(milliseconds: number) {
  const totalMinutes = Math.max(0, Math.floor(Math.abs(milliseconds) / 60000));
  if (totalMinutes < 1) return "menos de 1 min";
  const days = Math.floor(totalMinutes / 1440);
  const hours = Math.floor((totalMinutes % 1440) / 60);
  const minutes = totalMinutes % 60;
  if (days) return `${days}d ${hours}h`;
  if (hours) return `${hours}h ${minutes}min`;
  return `${minutes}min`;
}

function slaPresentation(item: QueueItem) {
  if (!item.sla) return {
    label: item.kind === "shield" && !item.owner ? "Sem SLA · caso não aberto" : "Sem SLA informado",
    detail: "",
    tone: "neutral",
  };
  const deadline = deadlineTime(item.sla);
  const relative = Number.isFinite(deadline) ? durationLabel(deadline - Date.now()) : "";
  if (item.sla.state === "overdue" || item.sla.state === "missed") return {
    label: relative ? `Vencido há ${relative}` : "SLA vencido",
    detail: formatDeadline(item.sla.deadline),
    tone: "danger",
  };
  if (item.sla.state === "warning") return {
    label: relative ? `Vence em ${relative}` : "Próximo do SLA",
    detail: formatDeadline(item.sla.deadline),
    tone: "warning",
  };
  if (item.sla.state === "met") return { label: "SLA atendido", detail: "", tone: "ok" };
  return {
    label: relative ? `${relative} restantes` : "Dentro do prazo",
    detail: formatDeadline(item.sla.deadline),
    tone: "ok",
  };
}

function statusLabel(value: string) {
  return ({
    open: "Aberto",
    in_progress: "Em investigação",
    acknowledged: "Reconhecido",
    pending: "Pendente",
    processed: "Processado",
    delivered: "Entregue",
    resolved: "Resolvido",
    closed: "Encerrado",
    reopened: "Reaberto",
  } as Record<string, string>)[value] || value.replace(/_/g, " ");
}

function slaFilterState(item: QueueItem): QueueFilters["sla"] {
  if (!item.sla) return "none";
  if (item.sla.state === "overdue" || item.sla.state === "missed") return "overdue";
  if (item.sla.state === "warning") return "warning";
  return "ok";
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
  const { incidents, loading: incidentsLoading, error: incidentsError, refetch: refetchIncidents } = useIncidents(100);
  const { alerts, loading: alertsLoading, error: alertsError, refetch: refetchAlerts } = useAlerts(100);
  const { events: shieldEvents, loading: shieldLoading, error: shieldError, refetch: refetchShield } = useShieldEvents(100);
  const { health, loading: healthLoading, error: healthError, lastUpdated: healthUpdatedAt, refetch: refetchHealth } = useHealth();
  const { metrics, loading: metricsLoading, error: metricsError, refetch: refetchMetrics } = useMetrics();
  const [assuming, setAssuming] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [ownerOverrides, setOwnerOverrides] = useState<Record<string, string>>({});
  const [filters, setFilters] = useState<QueueFilters>(defaultFilters);
  const assignmentsInFlight = useRef(new Set<string>());

  const fallbackAlerts = !incidentsError && !shieldError && incidents.length === 0 && shieldEvents.length === 0;
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
        owner: ownerOverrides[incident.id] || incident.owner || "",
        status: incident.status,
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
      status: event.case?.status || event.processing_status,
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
      status: alert.status,
      sla: alert.sla,
      createdAt: alert.firstSeen,
      action: "investigate",
    }));
    return items.sort(compareQueueItems);
  }, [alerts, fallbackAlerts, incidents, ownerOverrides, shieldEvents]);

  const statusOptions = useMemo(
    () => [...new Set(queue.map((item) => item.status))].sort((a, b) => statusLabel(a).localeCompare(statusLabel(b), "pt-BR")),
    [queue],
  );
  const visibleQueue = useMemo(() => queue.filter((item) => {
    if (filters.severity !== "all" && item.severity !== filters.severity) return false;
    if (filters.source !== "all" && item.kind !== filters.source) return false;
    if (filters.sla !== "all" && slaFilterState(item) !== filters.sla) return false;
    if (filters.ownership === "assigned" && !item.owner) return false;
    if (filters.ownership === "unassigned" && item.owner) return false;
    if (filters.status !== "all" && item.status !== filters.status) return false;
    return true;
  }), [filters, queue]);
  const activeFilterCount = Object.entries(filters).filter(([, value]) => value !== "all").length;

  const loading = incidentsLoading || alertsLoading || shieldLoading || healthLoading || metricsLoading;
  const dataError = incidentsError || alertsError || shieldError || healthError || metricsError;
  const criticalCount = queue.filter((item) => item.severity === "critical").length;
  const slaAttention = queue.filter((item) => ["overdue", "missed", "warning"].includes(item.sla?.state ?? "")).length;
  const unassigned = queue.filter((item) => !item.owner).length;
  const ingestion = health.ingestionDetails;
  const acceptedEvents = ingestion.acceptedEvents;
  const pendingEvents = ingestion.pendingEvents;
  const healthIsStale = !!healthError && healthUpdatedAt !== null;
  const ingestionUnavailable = health.ingestion !== "online";
  const healthTone = healthError || ingestionUnavailable || health.overall !== "healthy" ? "degraded" : "online";
  const healthTitle = healthError
    ? healthIsStale ? "Dados de ingestão podem estar desatualizados" : "Saúde de ingestão indisponível"
    : ingestionUnavailable ? "Receptor EDY Shield indisponível"
    : health.overall !== "healthy" ? "Ingestão disponível · operação degradada"
    : acceptedEvents === 0 ? "Receptor pronto · aguardando primeira fonte"
    : "Recepção saudável · EDY Shield integrado";
  const healthDescription = healthError
    ? healthIsStale
      ? "Mantendo o último estado confirmado. A fila preservada pode estar desatualizada até a API responder."
      : "A API de saúde não respondeu. Investigação e casos já carregados não foram descartados."
    : ingestionUnavailable
      ? "A indisponibilidade do receptor não torna investigação, casos ou outras fontes automaticamente offline."
      : health.overall !== "healthy"
        ? "O receptor Shield está pronto, mas outro componente reportou degradação. Revise o estado global antes de agir."
      : acceptedEvents === 0
        ? "Nenhum evento foi recebido ainda; receptor pronto não significa que uma fonte esteja conectada."
        : "Eventos foram recebidos com sucesso. O receptor não confirma sozinho se o agente permanece online agora.";

  const retryAll = () => { refetchIncidents(); refetchAlerts(); refetchShield(); refetchHealth(); refetchMetrics(); };
  const reviewShieldEvents = () => setFilters({ ...defaultFilters, source: "shield" });
  const openItem = (item: QueueItem) => {
    if (item.kind === "shield") navigate(`/investigate/shield/${encodeURIComponent(item.id)}`);
    else if (item.kind === "incident") navigate(`/incidents?incident=${encodeURIComponent(item.id)}`);
    else navigate("/alerts");
  };
  const assume = async (item: QueueItem) => {
    if (item.kind !== "incident" || assignmentsInFlight.current.has(item.id)) return;
    assignmentsInFlight.current.add(item.id);
    setAssuming(item.id);
    setActionError(null);
    setActionNotice(null);
    try {
      const response = await apiClient.post(`/soc/incidents/${encodeURIComponent(item.id)}/assign?analyst=${encodeURIComponent(CURRENT_ANALYST)}`);
      if (response.success) {
        setOwnerOverrides((current) => ({ ...current, [item.id]: CURRENT_ANALYST }));
        setActionNotice(`Incidente atribuído a ${CURRENT_ANALYST}.`);
        await refetchIncidents();
      } else {
        setActionError("Não foi possível assumir o incidente. A atribuição não foi alterada.");
      }
    } catch {
      setActionError("Não foi possível assumir o incidente. A atribuição não foi alterada.");
    } finally {
      assignmentsInFlight.current.delete(item.id);
      setAssuming(null);
    }
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
      .decision-health{display:grid;grid-template-columns:minmax(330px,1.35fr) minmax(430px,1fr) auto;gap:16px;align-items:center;padding:13px 15px;border:1px solid var(--color-border);border-left:3px solid var(--status-online);border-radius:9px;background:linear-gradient(90deg,color-mix(in srgb,var(--status-online) 6%,var(--color-surface)) 0%,var(--color-surface) 55%)}
      .decision-health-main{display:flex;align-items:flex-start;gap:10px}.decision-health-dot{width:8px;height:8px;margin-top:5px;border-radius:50%;background:var(--status-online);box-shadow:0 0 0 3px color-mix(in srgb,var(--status-online) 12%,transparent);flex:none}
      .decision-health[data-state='degraded']{border-left-color:var(--severity-medium);background:linear-gradient(90deg,color-mix(in srgb,var(--severity-medium) 6%,var(--color-surface)) 0%,var(--color-surface) 55%)}.decision-health[data-state='degraded'] .decision-health-dot{background:var(--severity-medium);box-shadow:0 0 0 3px color-mix(in srgb,var(--severity-medium) 12%,transparent)}
      .decision-health strong{display:block;color:var(--color-text-primary);font-size:13px}.decision-health p{margin:3px 0 0;color:var(--color-text-muted);font-size:11px;line-height:1.45}
      .decision-health-env{display:inline-flex;margin-left:7px;padding:2px 6px;border:1px solid var(--color-border);border-radius:999px;color:var(--color-text-muted);font:8px 'JetBrains Mono',monospace;letter-spacing:.05em;vertical-align:1px}.decision-health-facts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));min-width:0}.decision-health-fact{min-width:0;padding:2px 12px;border-left:1px solid var(--color-border-subtle)}.decision-health-fact span{display:block;color:var(--color-text-subtle);font-size:8px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}.decision-health-fact strong{margin-top:4px;overflow:hidden;text-overflow:ellipsis;font:600 10px 'JetBrains Mono',monospace;white-space:nowrap}.decision-health-action{white-space:nowrap}
      .decision-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid var(--color-border);border-radius:9px;background:var(--color-surface);overflow:hidden}
      .decision-signal{padding:13px 16px;border-right:1px solid var(--color-border-subtle)}.decision-signal:last-child{border-right:0}.decision-signal strong{display:block;color:var(--color-text-primary);font:700 22px 'JetBrains Mono',monospace}.decision-signal span{display:block;margin-top:3px;color:var(--color-text-muted);font-size:11px}
      .decision-queue{overflow:hidden;border:1px solid var(--color-border);border-radius:10px;background:var(--color-surface)}
      .decision-queue-head{display:flex;align-items:flex-end;justify-content:space-between;gap:14px;padding:14px 17px 11px}.decision-queue-head h2{margin:0;color:var(--color-text-primary);font-size:16px}.decision-queue-head p{margin:3px 0 0;color:var(--color-text-muted);font-size:11px}.decision-queue-count{color:var(--color-text-muted);font:10px 'JetBrains Mono',monospace;white-space:nowrap}
      .decision-filters{display:grid;grid-template-columns:repeat(5,minmax(120px,1fr)) auto;gap:8px;padding:0 17px 13px;border-bottom:1px solid var(--color-border);align-items:end}.decision-filter{display:flex;flex-direction:column;gap:4px;min-width:0}.decision-filter span{color:var(--color-text-subtle);font-size:9px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}.decision-filter select{width:100%;min-width:0;padding:7px 28px 7px 9px;border:1px solid var(--color-border);border-radius:6px;background:var(--color-surface-alt);color:var(--color-text-secondary);font-size:11px}.decision-filter select:focus-visible,.decision-action:focus-visible,.decision-refresh:focus-visible{outline:2px solid var(--color-accent);outline-offset:2px}.decision-clear{align-self:end;min-height:31px;padding:6px 9px;border:0;background:transparent;color:var(--color-accent-hover);font-size:11px;font-weight:600;cursor:pointer}.decision-clear:disabled{color:var(--color-text-subtle);cursor:default}
      .decision-columns,.decision-row{display:grid;grid-template-columns:minmax(230px,1.35fr) minmax(120px,.62fr) minmax(170px,.95fr) minmax(112px,.62fr) minmax(132px,.72fr) minmax(92px,.5fr) 150px;gap:12px;align-items:center;padding-left:17px;padding-right:17px}.decision-columns{min-height:30px;border-bottom:1px solid var(--color-border-subtle);background:var(--color-surface-alt);color:var(--color-text-subtle);font-size:9px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}.decision-columns span:last-child{text-align:right}
      .decision-row{min-height:76px;padding-top:10px;padding-bottom:10px;border-bottom:1px solid var(--color-border-subtle);position:relative}.decision-row:last-child{border-bottom:0}.decision-row::before{content:'';position:absolute;left:0;top:10px;bottom:10px;width:2px;background:var(--row-tone)}
      .decision-primary{min-width:0}.decision-primary-top{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.decision-source{display:inline-flex;padding:3px 7px;border:1px solid color-mix(in srgb,var(--color-accent) 32%,var(--color-border));border-radius:999px;background:var(--color-accent-subtle);color:var(--color-accent-hover);font-size:9px;font-weight:700;letter-spacing:.05em;text-transform:uppercase}.decision-primary h3{margin:8px 0 3px;overflow:hidden;text-overflow:ellipsis;color:var(--color-text-primary);font-size:13px;line-height:1.35}.decision-id{display:block;overflow:hidden;text-overflow:ellipsis;color:var(--color-text-muted);font:9px 'JetBrains Mono',monospace;white-space:nowrap}
      .decision-cell{min-width:0}.decision-label{display:none;margin-bottom:5px;color:var(--color-text-subtle);font-size:9px;font-weight:700;letter-spacing:.09em;text-transform:uppercase}.decision-value{display:block;overflow:hidden;text-overflow:ellipsis;color:var(--color-text-secondary);font-size:11px;line-height:1.4}.decision-value.mono{font-family:'JetBrains Mono',monospace;font-size:10px}.decision-evidence{display:-webkit-box;overflow:hidden;-webkit-box-orient:vertical;-webkit-line-clamp:2}.decision-owner.unassigned{color:var(--severity-medium);font-weight:600}.decision-state{display:inline-flex;max-width:100%;padding:3px 6px;border:1px solid var(--color-border-subtle);border-radius:4px;background:var(--color-surface-alt);font-size:10px;text-transform:capitalize}.decision-compact-meta{display:none;margin-top:5px;color:var(--color-text-muted);font-size:10px}
      .decision-sla{display:inline-flex;max-width:100%;padding:4px 7px;border:1px solid var(--color-border);border-radius:5px;color:var(--color-text-secondary);font-size:10px;font-weight:600;line-height:1.3}.decision-sla-detail{display:block;margin-top:3px;color:var(--color-text-subtle);font:8px 'JetBrains Mono',monospace}.decision-sla[data-tone='danger']{border-color:color-mix(in srgb,var(--severity-critical) 36%,var(--color-border));background:color-mix(in srgb,var(--severity-critical) 9%,transparent);color:var(--severity-critical)}.decision-sla[data-tone='warning']{border-color:color-mix(in srgb,var(--severity-medium) 38%,var(--color-border));background:color-mix(in srgb,var(--severity-medium) 8%,transparent);color:var(--severity-medium)}.decision-sla[data-tone='ok']{color:var(--status-online)}
      .decision-next{display:flex;justify-content:flex-end;gap:5px;flex-wrap:wrap;text-align:right}.decision-action{width:auto;min-width:0;padding:7px 9px;background:transparent;white-space:nowrap}.decision-action.primary{border-color:var(--color-accent);background:var(--color-accent);color:var(--color-text-on-accent)}.decision-action:disabled{cursor:wait;opacity:.55}
      .decision-error{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:10px 13px;border:1px solid color-mix(in srgb,var(--severity-medium) 36%,var(--color-border));border-radius:8px;background:color-mix(in srgb,var(--severity-medium) 8%,transparent);color:var(--color-text-secondary);font-size:12px}
      .decision-context{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;overflow:hidden;border:1px solid var(--color-border);border-radius:9px;background:var(--color-border-subtle)}.decision-context-item{padding:13px 15px;background:var(--color-surface)}.decision-context-item strong{display:block;color:var(--color-text-primary);font-size:12px}.decision-context-item span{display:block;margin-top:4px;color:var(--color-text-muted);font-size:10px;line-height:1.45}
      @media(max-width:1500px){.decision-health{grid-template-columns:minmax(400px,1fr) 420px auto}.decision-columns,.decision-row{grid-template-columns:minmax(230px,1.25fr) minmax(105px,.58fr) minmax(170px,.95fr) minmax(130px,.68fr) 145px;gap:10px}.decision-column-owner,.decision-cell-owner,.decision-column-status,.decision-cell-status{display:none}.decision-compact-meta{display:block}}
      @media(max-width:1050px){.decision-health{grid-template-columns:1fr auto}.decision-health-facts{grid-column:1/-1;grid-row:2}.decision-health-fact:first-child{border-left:0;padding-left:18px}.decision-filters{grid-template-columns:repeat(3,minmax(120px,1fr))}.decision-columns{display:none}.decision-row{grid-template-columns:minmax(0,1fr) 145px;align-items:start}.decision-primary{grid-column:1}.decision-next{grid-column:2;grid-row:1}.decision-cell-asset{grid-column:1;grid-row:2}.decision-cell-sla{grid-column:2;grid-row:2}.decision-cell-evidence{grid-column:1/-1;grid-row:3}.decision-label{display:block}.decision-context{grid-template-columns:1fr}.decision-summary{grid-template-columns:repeat(2,minmax(0,1fr))}.decision-signal:nth-child(2){border-right:0}.decision-signal:nth-child(-n+2){border-bottom:1px solid var(--color-border-subtle)}}
      @media(max-width:760px){.decision-center{gap:12px}.decision-title{font-size:23px}.decision-health{grid-template-columns:1fr}.decision-health-facts{grid-column:auto;grid-row:auto;grid-template-columns:1fr}.decision-health-fact,.decision-health-fact:first-child{padding:8px 0;border-left:0;border-top:1px solid var(--color-border-subtle)}.decision-health-action{justify-self:start}.decision-filters{grid-template-columns:repeat(2,minmax(0,1fr));padding-left:13px;padding-right:13px}.decision-columns{display:none}.decision-row{grid-template-columns:1fr;gap:9px;padding:13px 15px}.decision-primary,.decision-next,.decision-cell-asset,.decision-cell-evidence,.decision-cell-sla{grid-column:auto;grid-row:auto}.decision-row .decision-cell{display:block}.decision-label{display:block}.decision-compact-meta{display:none}.decision-next{justify-content:flex-start;text-align:left}.decision-action{width:auto}.decision-queue-head{align-items:flex-start;padding-left:13px;padding-right:13px}.decision-summary{overflow:visible}.decision-signal{padding:11px 12px}.decision-signal strong{font-size:18px}}
    `}</style>

    <header className="decision-header">
      <div><div className="decision-eyebrow">SOC Decision Center</div><h1 className="decision-title">Decisões que exigem ação</h1><p className="decision-subtitle">Prioridade, prazo, ownership, ativo e evidência em uma única fila operacional.</p></div>
      <button type="button" className="decision-refresh" onClick={retryAll}>Atualizar dados</button>
    </header>

    <section className="decision-health" data-state={healthTone} aria-label="Saúde operacional e ingestão" role="status" aria-live="polite" aria-atomic="true">
      <div className="decision-health-main"><span className="decision-health-dot" aria-hidden="true" /><div><strong>{healthTitle}{health.environment === "development" && <span className="decision-health-env">LAB LOCAL</span>}</strong><p>{healthDescription}</p></div></div>
      <div className="decision-health-facts">
        <div className="decision-health-fact"><span>EDY Shield</span><strong>{ingestionUnavailable ? "Fonte indisponível" : acceptedEvents === 0 ? "Nenhum evento" : `${acceptedEvents ?? "—"} evento${acceptedEvents === 1 ? " recebido" : "s recebidos"}`}</strong></div>
        <div className="decision-health-fact"><span>Última ingestão</span><strong>{ingestion.lastReceivedAt ? formatDate(ingestion.lastReceivedAt) : "Nenhum evento"}</strong></div>
        <div className="decision-health-fact"><span>Aguardando processamento</span><strong>{pendingEvents === null ? "Não disponível" : `${pendingEvents} evento${pendingEvents === 1 ? "" : "s"}`}</strong></div>
      </div>
      {healthError
        ? <button type="button" className="decision-refresh decision-health-action" onClick={retryAll}>Atualizar estado</button>
        : ingestionUnavailable || acceptedEvents === 0
          ? <button type="button" className="decision-refresh decision-health-action" onClick={() => navigate("/settings")}>{ingestionUnavailable ? "Revisar configuração" : "Conectar fonte"}</button>
          : <button type="button" className="decision-refresh decision-health-action" aria-controls="decision-queue" onClick={reviewShieldEvents}>Revisar eventos Shield</button>}
    </section>

    <section className="decision-summary" aria-label="Resumo da fila de decisão">
      <div className="decision-signal"><strong>{queue.length}</strong><span>decisões visíveis</span></div>
      <div className="decision-signal"><strong style={{ color: criticalCount ? "var(--severity-critical)" : undefined }}>{criticalCount}</strong><span>críticas agora</span></div>
      <div className="decision-signal"><strong style={{ color: slaAttention ? "var(--severity-medium)" : undefined }}>{slaAttention}</strong><span>SLA vencido ou próximo</span></div>
      <div className="decision-signal"><strong>{unassigned}</strong><span>sem responsável</span></div>
    </section>

    {(dataError || actionError) && <div className="decision-error" role="alert"><span>{actionError || (queue.length ? "Parte dos dados operacionais está indisponível. Dados carregados anteriormente foram preservados e podem estar desatualizados." : "Não foi possível carregar a fila operacional. O estado vazio não foi assumido como ausência real de trabalho.")}</span><button type="button" className="decision-refresh" onClick={retryAll}>Tentar novamente</button></div>}
    {actionNotice && !actionError && <div className="decision-error" role="status" style={{ borderColor: "color-mix(in srgb,var(--status-online) 35%,var(--color-border))", background: "color-mix(in srgb,var(--status-online) 7%,transparent)" }}><span>{actionNotice}</span></div>}

    <section id="decision-queue" className="decision-queue" aria-label="Decision Queue operacional">
      <header className="decision-queue-head"><div><h2>Decision Queue</h2><p>Crítico → alto → SLA vencido → SLA próximo → sem responsável → demais itens</p></div><span className="decision-queue-count">{visibleQueue.length} de {queue.length} itens · até 100 por fonte</span></header>
      <div className="decision-filters" aria-label="Filtros da Decision Queue">
        <label className="decision-filter"><span>Severidade</span><select value={filters.severity} onChange={(event) => setFilters((current) => ({ ...current, severity: event.target.value as QueueFilters["severity"] }))}><option value="all">Todas</option>{Object.entries(severityLabel).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        <label className="decision-filter"><span>Source</span><select value={filters.source} onChange={(event) => setFilters((current) => ({ ...current, source: event.target.value as QueueFilters["source"] }))}><option value="all">Todas as fontes</option><option value="incident">Correlação SIEM</option><option value="shield">EDY Shield</option><option value="alert">Detecção SIEM</option></select></label>
        <label className="decision-filter"><span>SLA</span><select value={filters.sla} onChange={(event) => setFilters((current) => ({ ...current, sla: event.target.value as QueueFilters["sla"] }))}><option value="all">Todos</option><option value="overdue">Vencido</option><option value="warning">Próximo</option><option value="ok">Dentro do prazo</option><option value="none">Sem SLA</option></select></label>
        <label className="decision-filter"><span>Responsável</span><select value={filters.ownership} onChange={(event) => setFilters((current) => ({ ...current, ownership: event.target.value as QueueFilters["ownership"] }))}><option value="all">Todos</option><option value="unassigned">Sem responsável</option><option value="assigned">Com responsável</option></select></label>
        <label className="decision-filter"><span>Estado</span><select value={filters.status} onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}><option value="all">Todos</option>{statusOptions.map((status) => <option key={status} value={status}>{statusLabel(status)}</option>)}</select></label>
        <button type="button" className="decision-clear" disabled={!activeFilterCount} onClick={() => setFilters(defaultFilters)}>Limpar {activeFilterCount ? `(${activeFilterCount})` : ""}</button>
      </div>
      {!!queue.length && <div className="decision-columns" aria-hidden="true"><span>Prioridade / evento</span><span>Ativo</span><span>Evidência</span><span className="decision-column-owner">Responsável</span><span>SLA</span><span className="decision-column-status">Estado</span><span>Ação</span></div>}
      {loading && !queue.length ? <div style={{ padding: 18 }}>{Array.from({ length: 4 }).map((_, index) => <div key={index} className="skeleton-line" style={{ height: 62, marginBottom: 8 }} />)}</div> : !queue.length ? dataError ? <EmptyState title="Fila temporariamente indisponível" description="Tente novamente quando a API local estiver acessível. Nenhum item foi classificado como resolvido ou inexistente." action={<button type="button" className="decision-refresh" onClick={retryAll}>Tentar novamente</button>} /> : <EmptyState title="Fila de decisão vazia" description="Não há incidentes ativos, eventos Shield ou alertas aguardando decisão." /> : !visibleQueue.length ? <EmptyState title="Nenhum item corresponde aos filtros" description="Ajuste ou limpe os filtros para voltar à fila operacional completa." action={<button type="button" className="decision-refresh" onClick={() => setFilters(defaultFilters)}>Limpar filtros</button>} /> : visibleQueue.map((item) => {
        const sla = slaPresentation(item);
        const rowTone = item.severity === "critical" ? "var(--severity-critical)" : item.severity === "high" ? "var(--severity-high)" : item.severity === "medium" ? "var(--severity-medium)" : "var(--severity-low)";
        return <article className="decision-row" key={`${item.kind}:${item.id}`} style={{ "--row-tone": rowTone } as React.CSSProperties}>
          <div className="decision-primary"><div className="decision-primary-top"><SeverityBadge severity={item.severity}>{severityLabel[item.severity]}</SeverityBadge><span className="decision-source">{item.source}</span></div><h3 title={item.title}>{item.title}</h3><span className="decision-id">{item.id} · {formatDate(item.createdAt)}</span><span className="decision-compact-meta">{statusLabel(item.status)} · {item.owner || "Sem responsável"}</span></div>
          <div className="decision-cell decision-cell-asset"><span className="decision-label">Ativo afetado</span><span className="decision-value mono" title={item.asset}>{item.asset}</span></div>
          <div className="decision-cell decision-cell-evidence"><span className="decision-label">Evidência</span><span className="decision-value decision-evidence" title={item.evidence}>{item.evidence}</span></div>
          <div className="decision-cell decision-cell-owner"><span className="decision-label">Responsável</span><span className={`decision-value decision-owner ${item.owner ? "" : "unassigned"}`}>{item.owner || "Sem responsável"}</span></div>
          <div className="decision-cell decision-cell-sla"><span className="decision-label">SLA</span><span className="decision-sla" data-tone={sla.tone}>{sla.label}</span>{sla.detail && <span className="decision-sla-detail">até {sla.detail}</span>}</div>
          <div className="decision-cell decision-cell-status"><span className="decision-label">Estado</span><span className="decision-value decision-state">{statusLabel(item.status)}</span></div>
          <div className="decision-next"><span className="decision-label">Próxima ação</span>{item.action === "assume" ? <><button type="button" className="decision-action primary" disabled={assuming === item.id} aria-busy={assuming === item.id} onClick={() => void assume(item)}>{assuming === item.id ? "Assumindo…" : "Assumir"}</button><button type="button" className="decision-action" onClick={() => openItem(item)}>Investigar</button></> : <button type="button" className={`decision-action ${item.kind === "shield" ? "primary" : ""}`} onClick={() => openItem(item)}>{item.kind === "shield" ? "Investigar" : item.action === "review" ? "Revisar evidência" : "Continuar investigação"}</button>}</div>
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
