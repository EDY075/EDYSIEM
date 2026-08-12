/**
 * War Room (UI 4.2 / Sprint 2.16) — dados reais, sem mocks.
 * Tela única de comando operacional: KPIs, feed ao vivo, MITRE, severidade,
 * assets e saúde da pipeline — tudo consumido da API /soc/*.
 */
import { useEffect, useMemo, useState } from "react";
import { colors, radii, spacing, typography } from "../design-system/tokens";
import { KpiCard, MetricCard } from "../design-system/components/cards";
import { StatusBadge } from "../design-system/components/badges";
import { ActivityFeed, ActivityItem } from "../design-system/components/Timeline";
import { SecurityDonutChart } from "../charts";
import { Breadcrumb } from "../shell/Breadcrumb";
import { useMetrics, useHealth, useAlerts } from "../hooks";
import type { ComponentStatus } from "../api/client";
import type { SystemHealth } from "../hooks/useHealth";

type PipelineHealthKey = keyof Pick<
  SystemHealth,
  "ingestion" | "correlation" | "enrichment" | "detection" | "alerts" | "cases" | "storage" | "api"
>;

const PIPELINE_COMPONENTS = [
  { key: "ingestion", label: "Ingestão" },
  { key: "correlation", label: "Correlação" },
  { key: "enrichment", label: "Enriquecimento" },
  { key: "detection", label: "Detecção" },
  { key: "alerts", label: "Alertas" },
  { key: "cases", label: "Casos" },
  { key: "storage", label: "Storage" },
  { key: "api", label: "API" },
] as const satisfies ReadonlyArray<{ key: PipelineHealthKey; label: string }>;

function healthTone(status: ComponentStatus): "online" | "degraded" | "offline" | "neutral" {
  if (status === "online") return "online";
  if (status === "degraded") return "degraded";
  if (status === "offline" || status === "error") return "offline";
  return "neutral";
}

function healthLabel(status: ComponentStatus): string {
  switch (status) {
    case "online": return "Online";
    case "degraded": return "Degradado";
    case "offline": return "Offline";
    case "error": return "Erro";
    default: return "—";
  }
}

export function WarRoomPage() {
  const { metrics, loading: metricsLoading } = useMetrics("1h");
  const { health, loading: healthLoading } = useHealth();
  const { alerts, loading: alertsLoading, error: alertsError } = useAlerts(50);

  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 3000);
    return () => clearInterval(timer);
  }, []);

  const loading = metricsLoading || healthLoading || alertsLoading;

  // Feed ao vivo — alertas reais dos últ.phist15 (só dados da API)
  const liveItems: ActivityItem[] = useMemo(() => {
    return alerts.slice(0, 6).map((a, i) => ({
      id: a.id,
      actor: a.rule,
      action: "disparou alerta em",
      target: a.host,
      time: `${i}s`,
      tone: a.severity === "critical" ? "critical" : a.severity === "high" ? "high" : a.severity === "medium" ? "medium" : undefined,
    }));
  }, [alerts]);

  // MITRE — agregado dos alertas reais
  const mitre = useMemo(() => {
    const map = new Map<string, number>();
    alerts.forEach((a) => (a.mitre || []).forEach((m) => map.set(m, (map.get(m) || 0) + 1)));
    return [...map.entries()].map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count).slice(0, 5);
  }, [alerts]);

  // Assets comprometidos — hosts dos alertas críticos
  const assets = useMemo(() => {
    const map = new Map<string, number>();
    alerts.forEach((a) => map.set(a.host, (map.get(a.host) || 0) + 1));
    return [...map.entries()].map(([id, count]) => ({ id, count })).sort((a, b) => b.count - a.count).slice(0, 5);
  }, [alerts]);

  const criticals = alerts.filter((a) => a.severity === "critical");

  const statusData = useMemo(
    () => [
      { name: "Crítico", value: alerts.filter((a) => a.severity === "critical").length, color: colors.severity.critical },
      { name: "Alto", value: alerts.filter((a) => a.severity === "high").length, color: colors.severity.high },
      { name: "Médio", value: alerts.filter((a) => a.severity === "medium").length, color: colors.severity.medium },
      { name: "Baixo", value: alerts.filter((a) => a.severity === "low").length, color: colors.severity.low },
    ],
    [alerts],
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh", background: colors.background }} aria-busy={loading}>
      {/* Cabeçalho */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: spacing["3"], padding: `${spacing["3"]} ${spacing["4"]}`, borderBottom: `1px solid ${colors.border}`, background: `linear-gradient(100deg, color-mix(in srgb, ${colors.surfaceAlt} 54%, ${colors.surface}) 0%, ${colors.surface} 68%)`, position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <Breadcrumb items={[{ label: "Operação", to: "/war-room" }, { label: "War Room", to: "/war-room" }]} />
          <div><div style={{ color: colors.severity.high, fontSize: "10px", fontWeight: typography.weight.semibold, letterSpacing: "0.11em", marginBottom: 3 }}>INCIDENT COMMAND</div><h1 style={{ fontSize: 20, fontWeight: 700, letterSpacing: "-0.02em", margin: 0, color: colors.textPrimary }}>War Room</h1></div>
          <span style={{ display: "flex", alignItems: "center", gap: 6, fontSize: typography.size.xs, color: colors.status.online, padding: "3px 10px", background: "color-mix(in srgb, var(--status-online) 12%, transparent)", borderRadius: 9999 }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: colors.status.online, boxShadow: "0 0 0 3px color-mix(in srgb, var(--status-online) 12%, transparent)" }} />
            LIVE
          </span>
        </div>
        <span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
          Atualizado às {now.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
        </span>
      </div>

      <div style={{ padding: spacing["4"], display: "flex", flexDirection: "column", gap: spacing["4"] }}>
        {alertsError && (
          <div style={{ padding: `${spacing["2"]} ${spacing["3"]}`, background: "color-mix(in srgb, var(--severity-medium) 12%, transparent)", border: "1px solid color-mix(in srgb, var(--severity-medium) 30%, transparent)", borderRadius: 8, fontSize: typography.size.sm, color: colors.textSecondary }}>
            ⚠ {alertsError}
          </div>
        )}

        {/* KPIs operacionais — dados reais */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: spacing["3"] }}>
          <KpiCard label="Events/sec" value={String(metrics.eps)} delta="real" trend="flat" mono />
          <KpiCard label="Alertas críticos" value={String(criticals.length)} delta="ativos" trend="up" severity={criticals.length ? "critical" : undefined} />
          <KpiCard label="Casos abertos" value={String(metrics.openCases)} delta="reais" trend="flat" severity="high" />
          <KpiCard label="MTTR" value={`${metrics.mttr}min`} delta="real" trend="flat" mono />
          <KpiCard label="Risk médio" value={String(metrics.avgRiskScore)} delta="real" trend="flat" mono />
        </div>

        <div className="wr-grid-main">
          {/* Coluna esquerda */}
          <div style={{ display: "flex", flexDirection: "column", gap: spacing["4"] }}>
            <MetricCard title="Live Event Feed" footer={<span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>{alerts.length} eventos na janela</span>}>
              <ActivityFeed items={liveItems.length ? liveItems : [{ id: "empty", actor: "—", action: "nenhum evento ainda", time: "", tone: "low" }]} />
            </MetricCard>

            <MetricCard title="MITRE ATT&CK — Técnicas detectadas" footer={<span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>{mitre.reduce((s, m) => s + m.count, 0)} ocorrências</span>}>
              {mitre.length === 0 ? (
                <div style={{ color: colors.textMuted, fontSize: typography.size.sm, padding: spacing["3"] }}>Sem detecções no período.</div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: spacing["3"] }}>
                  {mitre.map((m) => (
                    <div key={m.name} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: typography.size.sm }}>
                        <span style={{ fontFamily: typography.family.mono, color: colors.severity.high }}>{m.name}</span>
                        <span style={{ color: colors.textMuted, fontFamily: typography.family.mono }}>{m.count}</span>
                      </div>
                      <div style={{ height: 8, background: colors.surfaceAlt, borderRadius: 9999, overflow: "hidden" }}>
                        <div style={{ height: "100%", width: `${Math.min(100, (m.count / (mitre[0]?.count || 1)) * 100)}%`, background: colors.severity.high, borderRadius: 9999 }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </MetricCard>

            <MetricCard title="Saúde da Pipeline" footer={<span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>health do container</span>}>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px,1fr))", gap: spacing["3"] }}>
                {PIPELINE_COMPONENTS.map((component) => {
                  const status = health[component.key];
                  return <div key={component.key} style={{ padding: spacing["3"], background: colors.surfaceAlt, borderRadius: radii.md, border: `1px solid ${colors.border}` }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>{component.label}</span>
                      <StatusBadge tone={healthTone(status)}>{healthLabel(status)}</StatusBadge>
                    </div>
                  </div>;
                })}
              </div>
            </MetricCard>
          </div>

          {/* Coluna direita */}
          <div style={{ display: "flex", flexDirection: "column", gap: spacing["4"] }}>
            <MetricCard title={`Alertas críticos (${criticals.length})`}>
              {criticals.length === 0 ? (
                <div style={{ color: colors.textMuted, fontSize: typography.size.sm, textAlign: "center", padding: spacing["3"] }}>Nenhum alerta crítico no momento.</div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: spacing["2"] }}>
                  {criticals.slice(0, 5).map((a) => (
                    <div key={a.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: `${spacing["2"]} ${spacing["3"]}`, background: colors.surfaceAlt, border: "1px solid color-mix(in srgb, var(--severity-critical) 25%, transparent)", borderLeft: `3px solid ${colors.severity.critical}`, borderRadius: radii.md }}>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: typography.size.sm, fontWeight: typography.weight.semibold, color: colors.textPrimary, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{a.title}</div>
                        <div style={{ fontSize: typography.size.xs, color: colors.textMuted }}>{a.host} • regra: {a.rule}</div>
                      </div>
                      <span style={{ fontFamily: typography.family.mono, fontSize: typography.size.sm, color: colors.severity.critical, fontWeight: 700, marginLeft: 8 }}>{a.riskScore}</span>
                    </div>
                  ))}
                </div>
              )}
            </MetricCard>

            <MetricCard title="Top assets acionados" footer={<span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>hosts com mais alertas</span>}>
              {assets.length === 0 ? (
                <div style={{ color: colors.textMuted, fontSize: typography.size.sm, textAlign: "center", padding: spacing["3"] }}>Sem assets no período.</div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: spacing["2"] }}>
                  {assets.map((a) => (
                    <div key={a.id} style={{ display: "flex", alignItems: "center", gap: spacing["3"] }}>
                      <span style={{ flex: 1, fontFamily: typography.family.mono, fontSize: typography.size.sm, color: colors.textPrimary }}>{a.id}</span>
                      <span style={{ fontFamily: typography.family.mono, fontSize: typography.size.xs, color: colors.textMuted }}>{a.count}</span>
                    </div>
                  ))}
                </div>
              )}
            </MetricCard>

            <MetricCard title="Alertas por severidade" footer={<span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>{alerts.length} alertas no período</span>}>
              <SecurityDonutChart data={statusData} nameKey="name" valueKey="value" height={220} />
            </MetricCard>
          </div>
        </div>
      </div>

      <style>{`.wr-grid-main { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start; }
@media (max-width: 1024px) { .wr-grid-main { grid-template-columns: 1fr !important; } }`}</style>
    </div>
  );
}
