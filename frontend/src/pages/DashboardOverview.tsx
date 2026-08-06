/**
 * EDY SIEM Overview — Echelon operational console.
 * UI composition only: every panel is derived from the existing metrics, alerts and health hooks.
 */
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { colors, radii, spacing, typography } from "../design-system/tokens";
import { KpiCard } from "../design-system/components/cards";
import { DataTable } from "../design-system/components/DataTable";
import { SeverityBadge } from "../design-system/components/badges";
import { EmptyState, skeletonCss } from "../design-system/components/feedback";
import { Timeline } from "../design-system/components/Timeline";
import { SecurityAreaChart, SecurityHeatmap } from "../charts";
import { useAlerts, useHealth, useMetrics } from "../hooks";
import type { SystemHealth } from "../hooks";

type KpiGlyphKind = "telemetry" | "alert" | "case" | "response" | "risk" | "health";

function KpiGlyph({ kind }: { kind: KpiGlyphKind }) {
  const stroke = { fill: "none", stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  const shapes: Record<KpiGlyphKind, JSX.Element> = {
    telemetry: <path d="M3 15h3l2-7 4 11 3-7h6" />,
    alert: <><path d="M18 9a6 6 0 0 0-12 0c0 7-3 8-3 8h18s-3-1-3-8" /><path d="M10 21h4" /></>,
    case: <><rect x="3" y="5" width="18" height="15" rx="2" /><path d="M8 5V3h8v2M8 11h8M8 15h5" /></>,
    response: <><circle cx="12" cy="12" r="8" /><path d="M12 8v4l3 2" /></>,
    risk: <><path d="M12 3 4 7v5c0 5 3.4 7.7 8 9 4.6-1.3 8-4 8-9V7l-8-4Z" /><path d="M12 8v5" /><circle cx="12" cy="16" r=".7" fill="currentColor" /></>,
    health: <><path d="M3 12h4l2-5 4 10 2-5h4" /><circle cx="12" cy="12" r="9" /></>,
  };
  return <svg width="15" height="15" viewBox="0 0 24 24" aria-hidden="true" {...stroke}>{shapes[kind]}</svg>;
}

function formatNumber(value: number) {
  if (Math.abs(value) >= 1000000) return `${(value / 1000000).toFixed(1).replace(".0", "")}M`;
  if (Math.abs(value) >= 1000) return `${(value / 1000).toFixed(1).replace(".0", "")}K`;
  return String(Math.round(value));
}

function formatTime(iso: string) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return `${String(date.getDate()).padStart(2, "0")}/${String(date.getMonth() + 1).padStart(2, "0")} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function healthColor(status: string) {
  if (status === "online") return colors.status.online;
  if (status === "degraded") return colors.status.degraded;
  if (status === "offline" || status === "error") return colors.status.offline;
  return colors.textMuted;
}

function healthCopy(status: string) {
  if (status === "online") return "Online";
  if (status === "degraded") return "Degradado";
  if (status === "offline") return "Offline";
  if (status === "error") return "Erro";
  return status;
}

function riskTone(score: number) {
  if (score >= 80) return colors.severity.critical;
  if (score >= 60) return colors.severity.high;
  if (score >= 40) return colors.severity.medium;
  return colors.severity.low;
}

function OpsPanel({ title, meta, children, footer }: { title: string; meta?: string; children: React.ReactNode; footer?: React.ReactNode }) {
  return (
    <section className="overview-panel">
      <header className="overview-panel-head">
        <h2>{title}</h2>
        {meta && <span data-mono>{meta}</span>}
      </header>
      <div className="overview-panel-body">{children}</div>
      {footer && <footer className="overview-panel-footer">{footer}</footer>}
    </section>
  );
}

export function DashboardOverview() {
  const navigate = useNavigate();
  const [timeRange, setTimeRange] = useState<"1h" | "6h" | "24h" | "7d">("1h");
  const [autoRefresh, setAutoRefresh] = useState(true);
  const { metrics, loading: metricsLoading, error: metricsError, refetch: refetchMetrics } = useMetrics(timeRange);
  const { health, loading: healthLoading, error: healthError, refetch: refetchHealth } = useHealth();
  const { alerts, loading: alertsLoading, error: alertsError, refetch: refetchAlerts } = useAlerts(10);

  const isLoading = metricsLoading || healthLoading || alertsLoading;
  const hasError = metricsError || healthError || alertsError;
  const systemHealth: SystemHealth = health;
  const componentsOnline = Object.values(systemHealth).filter((status) => status === "online").length;
  const componentsTotal = Object.keys(systemHealth).length;
  const healthLabel = systemHealth.api === "online" ? "Saudável" : systemHealth.api === "degraded" ? "Degradado" : "Crítico";

  const criticalAlerts = useMemo(() => [...alerts].filter((alert) => alert.severity === "critical" || alert.severity === "high").sort((a, b) => b.riskScore - a.riskScore).slice(0, 5), [alerts]);
  const feedAlerts = useMemo(() => alerts.slice(0, 5), [alerts]);
  const timelineItems = useMemo(() => alerts.slice(0, 5).map((alert) => ({ id: alert.id, title: alert.title, detail: `${alert.host} · ${alert.rule}`, time: formatTime(alert.firstSeen), tone: alert.severity })), [alerts]);
  const topHosts = useMemo(() => {
    const hosts = new Map<string, { risk: number; count: number }>();
    alerts.forEach((alert) => {
      const existing = hosts.get(alert.host) ?? { risk: 0, count: 0 };
      hosts.set(alert.host, { risk: Math.max(existing.risk, alert.riskScore), count: existing.count + 1 });
    });
    return [...hosts.entries()].map(([host, detail]) => ({ host, ...detail })).sort((a, b) => b.risk - a.risk || b.count - a.count).slice(0, 5);
  }, [alerts]);
  const heatmap = useMemo(() => {
    const rows = ["Crítico", "Alto", "Médio", "Baixo"];
    const cols = ["00h", "04h", "08h", "12h", "16h", "20h"];
    const rowFor: Record<string, string> = { critical: "Crítico", high: "Alto", medium: "Médio", low: "Baixo", info: "Baixo" };
    const values = new Map<string, number>();
    alerts.forEach((alert) => {
      const time = new Date(alert.firstSeen);
      if (Number.isNaN(time.getTime())) return;
      const col = cols[Math.floor(time.getHours() / 4)] ?? cols[0];
      const row = rowFor[alert.severity] ?? "Baixo";
      const key = `${row}::${col}`;
      values.set(key, (values.get(key) ?? 0) + 1);
    });
    return { rows, cols, cells: [...values.entries()].map(([key, value]) => { const [row, col] = key.split("::"); return { row, col, value }; }) };
  }, [alerts]);

  const retryAll = () => { refetchMetrics(); refetchHealth(); refetchAlerts(); };

  return (
    <div className="overview-console" aria-busy={isLoading}>
      <style>{`${skeletonCss}
        .overview-console { display:flex; flex-direction:column; gap:18px; }
        .overview-intro { display:flex; justify-content:space-between; align-items:end; gap:16px; flex-wrap:wrap; padding: 2px 0; }
        .overview-eyebrow { color:var(--color-accent); font-size:10px; font-weight:600; letter-spacing:.12em; margin-bottom:5px; }
        .overview-title { margin:0; color:var(--color-text-primary); font-size:26px; line-height:1.15; letter-spacing:-.03em; }
        .overview-subtitle { margin:6px 0 0; color:var(--color-text-muted); font-size:13px; }
        .overview-controls { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
        .overview-select { padding:7px 10px; border:1px solid var(--color-border); border-radius:6px; background:var(--color-surface); color:var(--color-text-primary); font-size:13px; cursor:pointer; }
        .overview-auto { display:inline-flex; align-items:center; gap:7px; color:var(--color-text-secondary); font-size:12px; cursor:pointer; padding:7px 9px; border:1px solid var(--color-border-subtle); border-radius:6px; background:color-mix(in srgb, var(--color-surface-alt) 44%, transparent); }
        .overview-status { display:flex; align-items:center; gap:10px; padding:10px 12px; border:1px solid var(--color-border); border-radius:8px; background:linear-gradient(90deg, color-mix(in srgb, var(--status-online) 7%, var(--color-surface)) 0%, var(--color-surface) 58%); }
        .overview-status-copy { display:flex; flex-direction:column; gap:1px; }
        .overview-status-copy strong { font-size:13px; color:var(--color-text-primary); }
        .overview-status-copy span { font-size:11px; color:var(--color-text-muted); }
        .overview-kpis { display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:12px; }
        .overview-kpis button { min-width:0 !important; }
        .overview-grid-primary, .overview-grid-secondary { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; align-items:start; }
        .overview-panel { min-width:0; overflow:hidden; border:1px solid var(--color-border); border-radius:10px; background:linear-gradient(180deg, var(--color-surface) 0%, color-mix(in srgb, var(--color-surface-alt) 34%, var(--color-surface)) 100%); box-shadow:var(--elevation-floating); }
        .overview-panel-head { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:14px 16px; border-bottom:1px solid var(--color-border-subtle); }
        .overview-panel-head h2 { margin:0; color:var(--color-text-primary); font-size:14px; font-weight:600; letter-spacing:-.01em; }
        .overview-panel-head span { color:var(--color-text-muted); font-size:11px; white-space:nowrap; }
        .overview-panel-body { padding:14px 16px; }
        .overview-panel-footer { padding:9px 16px; border-top:1px solid var(--color-border-subtle); background:color-mix(in srgb, var(--color-surface-alt) 56%, transparent); color:var(--color-text-muted); font-size:11px; }
        .overview-feed { display:flex; flex-direction:column; }
        .overview-feed-row { display:grid; grid-template-columns:7px minmax(0,1fr) auto; align-items:center; gap:9px; min-height:38px; border-bottom:1px solid var(--color-border-subtle); }
        .overview-feed-row:last-child { border-bottom:0; }
        .overview-feed-title { min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:var(--color-text-primary); font-size:12px; font-weight:500; }
        .overview-feed-meta { color:var(--color-text-muted); font-family:'JetBrains Mono', monospace; font-size:10px; white-space:nowrap; }
        .overview-hosts { display:flex; flex-direction:column; gap:11px; }
        .overview-host-row { display:grid; grid-template-columns:minmax(0,1fr) 48px; gap:10px; align-items:center; }
        .overview-host-name { color:var(--color-text-primary); font:600 11px 'JetBrains Mono', monospace; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
        .overview-host-rail { height:4px; overflow:hidden; border-radius:999px; background:var(--color-border-subtle); margin-top:6px; }
        .overview-host-fill { height:100%; border-radius:inherit; }
        .overview-host-risk { color:var(--color-text-muted); font:11px 'JetBrains Mono', monospace; text-align:right; }
        .overview-health { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; }
        .overview-health-item { min-width:0; padding:9px 8px; border:1px solid var(--color-border); border-radius:6px; background:color-mix(in srgb, var(--color-surface-alt) 54%, transparent); }
        .overview-health-name { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:var(--color-text-secondary); font-size:10px; text-transform:capitalize; }
        .overview-health-state { display:flex; align-items:center; gap:5px; margin-top:5px; font:10px 'JetBrains Mono', monospace; }
        .overview-critical-action { border:1px solid var(--color-border); border-radius:5px; background:transparent; color:var(--color-text-secondary); cursor:pointer; font-size:11px; padding:4px 7px; transition:background 120ms cubic-bezier(.2,0,0,1), border-color 120ms cubic-bezier(.2,0,0,1), color 120ms cubic-bezier(.2,0,0,1); }
        .overview-critical-action:hover { background:var(--color-accent-subtle); border-color:var(--color-accent); color:var(--color-accent-hover); }
        @media (max-width:1500px) { .overview-kpis { grid-template-columns:repeat(3,minmax(0,1fr)); } }
        @media (max-width:1120px) { .overview-grid-primary, .overview-grid-secondary { grid-template-columns:repeat(2,minmax(0,1fr)); } .overview-grid-secondary > :last-child { grid-column:span 2; } }
        @media (max-width:760px) { .overview-console { gap:14px; } .overview-kpis, .overview-grid-primary, .overview-grid-secondary { grid-template-columns:1fr; } .overview-grid-secondary > :last-child { grid-column:auto; } .overview-health { grid-template-columns:repeat(2,minmax(0,1fr)); } .overview-panel-body { padding:12px; } .overview-panel-head { padding:12px; } .overview-intro { align-items:start; } }
      `}</style>

      <div className="overview-intro">
        <div>
          <div className="overview-eyebrow">SOC OVERVIEW</div>
          <h1 className="overview-title">Visão operacional</h1>
          <p className="overview-subtitle">Telemetria, risco e resposta no período selecionado.</p>
        </div>
        <div className="overview-controls">
          <div className="overview-status">
            <span style={{ width: 7, height: 7, borderRadius: "50%", background: healthColor(systemHealth.api), boxShadow: `0 0 0 3px color-mix(in srgb, ${healthColor(systemHealth.api)} 12%, transparent)` }} />
            <div className="overview-status-copy"><strong>{healthLabel}</strong><span>{componentsOnline}/{componentsTotal} serviços online</span></div>
          </div>
          <label className="overview-auto"><input type="checkbox" checked={autoRefresh} onChange={(event) => setAutoRefresh(event.target.checked)} style={{ accentColor: colors.accent }} />Auto-refresh</label>
          <select className="overview-select" value={timeRange} onChange={(event) => setTimeRange(event.target.value as typeof timeRange)} aria-label="Período da Overview"><option value="1h">Última hora</option><option value="6h">Últimas 6h</option><option value="24h">Últimas 24h</option><option value="7d">Últimos 7 dias</option></select>
        </div>
      </div>

      {hasError && <div style={{ alignSelf: "flex-start", display: "flex", alignItems: "center", gap: spacing["2"], padding: `${spacing["2"]} ${spacing["3"]}`, border: "1px solid color-mix(in srgb, var(--severity-medium) 30%, transparent)", borderRadius: radii.md, background: "color-mix(in srgb, var(--severity-medium) 10%, transparent)", color: colors.textSecondary, fontSize: typography.size.sm }}><span style={{ color: colors.severity.medium }}>!</span>Dados operacionais indisponíveis <button type="button" onClick={retryAll} className="overview-critical-action">Tentar novamente</button></div>}

      <div className="overview-kpis" aria-busy={isLoading}>
        {isLoading ? Array.from({ length: 6 }).map((_, index) => <div key={index} style={{ minHeight: 126, padding: spacing["4"], border: `1px solid ${colors.border}`, borderRadius: radii.lg, background: colors.surface }}><div className="skeleton-line" style={{ height: 11, width: "54%" }} /><div className="skeleton-line" style={{ height: 28, width: "44%", marginTop: 18 }} /><div className="skeleton-line" style={{ height: 10, width: "62%", marginTop: 18 }} /></div>) : <>
          <KpiCard label="Events/sec" value={formatNumber(metrics.eps)} icon={<KpiGlyph kind="telemetry" />} delta={`${formatNumber(metrics.eventsLastHour)} na janela`} trend="up" mono />
          <KpiCard label="Alertas ativos" value={String(metrics.activeAlerts)} icon={<KpiGlyph kind="alert" />} delta={`${criticalAlerts.length} prioritários`} trend={criticalAlerts.length ? "up" : "flat"} severity="critical" mono />
          <KpiCard label="Casos abertos" value={String(metrics.openCases)} icon={<KpiGlyph kind="case" />} delta="em acompanhamento" trend="flat" />
          <KpiCard label="MTTR" value={`${metrics.mttr}min`} icon={<KpiGlyph kind="response" />} delta="tempo de resposta" trend="down" severity="medium" mono />
          <KpiCard label="Score médio" value={String(metrics.avgRiskScore)} icon={<KpiGlyph kind="risk" />} delta="risco consolidado" trend="flat" severity="high" mono />
          <KpiCard label="Saúde da pipeline" value={healthLabel} icon={<KpiGlyph kind="health" />} delta={`${componentsOnline}/${componentsTotal} componentes`} trend="flat" />
        </>}
      </div>

      <div className="overview-grid-primary">
        <OpsPanel title="Eventos por minuto" meta="últimos 60 min" footer={<span>Ingestão processada no período selecionado</span>}><SecurityAreaChart data={metrics.eventsSeries} xKey="time" yKeys={["events"]} height={210} xInterval={11} /></OpsPanel>
        <OpsPanel title="Matriz de atividade" meta="severidade × horário" footer={<span>Distribuição baseada no horário dos alertas recebidos</span>}>{alerts.length ? <SecurityHeatmap rows={heatmap.rows} cols={heatmap.cols} cells={heatmap.cells} /> : <EmptyState title="Sem atividade classificada" description="A matriz será preenchida à medida que alertas forem recebidos." compact />}</OpsPanel>
        <OpsPanel title="Live feed" meta={`${feedAlerts.length} eventos`} footer={<span>Alertas mais recentes recebidos pelo SOC</span>}>{feedAlerts.length ? <div className="overview-feed">{feedAlerts.map((alert) => <div className="overview-feed-row" key={alert.id}><span style={{ width: 7, height: 7, borderRadius: "50%", background: riskTone(alert.riskScore) }} /><span className="overview-feed-title" title={alert.title}>{alert.title}</span><span className="overview-feed-meta">{formatTime(alert.firstSeen)}</span></div>)}</div> : <EmptyState title="Feed aguardando eventos" description="Novos alertas aparecerão aqui automaticamente." compact />}</OpsPanel>
      </div>

      <div className="overview-grid-secondary">
        <OpsPanel title="Alertas prioritários" meta={`${criticalAlerts.length} itens`} footer={<span>Ordenados pelo maior score de risco</span>}>{criticalAlerts.length ? <DataTable columns={[{ key: "severity", header: "Sev.", width: "76px", render: (row: any) => <SeverityBadge severity={row.severity}>{row.severity}</SeverityBadge> }, { key: "title", header: "Alerta / Regra" }, { key: "host", header: "Host", width: "84px", mono: true }, { key: "riskScore", header: "Risco", width: "48px", mono: true, render: (row: any) => <span style={{ color: riskTone(row.riskScore), fontWeight: 700 }}>{row.riskScore}</span> }, { key: "action", header: "", width: "50px", render: () => <button className="overview-critical-action" onClick={() => navigate("/investigate")}>Abrir</button> }]} rows={criticalAlerts as unknown as Array<Record<string, React.ReactNode>>} compact /> : <EmptyState title="Sem alertas prioritários" description="Alertas de alta criticidade aparecerão aqui." compact />}</OpsPanel>
        <OpsPanel title="Linha do tempo" meta="alertas recentes" footer={<span>Sequência cronológica de evidências registradas</span>}>{timelineItems.length ? <Timeline items={timelineItems} /> : <EmptyState title="Sem eventos na linha do tempo" compact />}</OpsPanel>
        <OpsPanel title="Hosts por risco" meta={`${topHosts.length} ativos`} footer={<span>Maior score por host observado no período</span>}>{topHosts.length ? <div className="overview-hosts">{topHosts.map((host) => { const color = riskTone(host.risk); return <div className="overview-host-row" key={host.host}><div><div className="overview-host-name">{host.host}</div><div className="overview-host-rail"><div className="overview-host-fill" style={{ width: `${Math.max(4, host.risk)}%`, background: color }} /></div></div><div className="overview-host-risk">{host.risk}</div></div>; })}</div> : <EmptyState title="Sem hosts em risco" compact />}</OpsPanel>
      </div>

      <OpsPanel title="Saúde da pipeline" meta={`${componentsOnline}/${componentsTotal} online`} footer={<span>Estado atual dos serviços de coleta, correlação e resposta</span>}><div className="overview-health">{Object.entries(systemHealth).map(([name, status]) => { const color = healthColor(status); return <div className="overview-health-item" key={name}><div className="overview-health-name">{name}</div><div className="overview-health-state" style={{ color }}><span style={{ width: 5, height: 5, borderRadius: "50%", background: color }} />{healthCopy(status)}</div></div>; })}</div></OpsPanel>
    </div>
  );
}
