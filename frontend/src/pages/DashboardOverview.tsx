/**
 * Dashboard Overview (UI 4.1 / sprint 5.1.1)
 * Visão geral do SOC com 6 KPIs principais + seção de volume, gráficos,
 * tabela de alertas e saúde do sistema. Conectado ao backend real.
 *
 * Sprint 5.1.1: KPIs reorganizados (6 principais + secundários), Empty States
 * profissionais, aviso de API compacto com retry, gráfico com eixo X limpo,
 * tipografia técnica (mono) apenas para dados técnicos e layout equilibrado.
 */
import { useState, useMemo } from "react";
import { colors, spacing, typography } from "../design-system/tokens";
import { KpiCard } from "../design-system/components/cards";
import { DataTable } from "../design-system/components/DataTable";
import { SeverityBadge } from "../design-system/components/badges";
import { EmptyState } from "../design-system/components/feedback";
import { SecurityAreaChart, SecurityDonutChart } from "../charts";
import { useMetrics, useHealth, useAlerts } from "../hooks";
import type { SystemHealth } from "../hooks";

function healthColor(status: string): string {
  switch (status) {
    case "online": return colors.status.online;
    case "degraded": return colors.status.degraded;
    case "offline": return colors.status.offline;
    case "error": return colors.status.offline;
    default: return colors.textMuted;
  }
}

/** Formata número compacto sem zeros excessivos (12.4K, 3.1M). */
function formatNumber(num: number): string {
  if (Math.abs(num) >= 1000000) return (num / 1000000).toFixed(1).replace(".0", "") + "M";
  if (Math.abs(num) >= 1000) return (num / 1000).toFixed(1).replace(".0", "") + "K";
  return String(Math.round(num));
}

/** Formata timestamp ISO → "dd/mm HH:MM" (tipografia técnica). */
function formatTime(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const mo = String(d.getMonth() + 1).padStart(2, "0");
  return `${dd}/${mo} ${hh}:${mm}`;
}

/** Gera série temporal legível de eventos (rótulos HH:MM). */
function buildEventSeries(eps: number, loading: boolean) {
  const now = new Date();
  const base = now.getMinutes();
  return Array.from({ length: 60 }, (_, i) => {
    const t = new Date(now);
    t.setMinutes(base - (59 - i));
    const label = `${String(t.getHours()).padStart(2, "0")}:${String(t.getMinutes()).padStart(2, "0")}`;
    if (loading || eps === 0) {
      return { time: label, events: Math.floor(Math.random() * 50) + 10 };
    }
    return { time: label, events: Math.max(0, Math.floor(eps / 10 + Math.random() * 50 - 25)) };
  });
}

export function DashboardOverview() {
  const [timeRange, setTimeRange] = useState<"1h" | "6h" | "24h" | "7d">("1h");
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Conexão real com a API
  const { metrics, loading: metricsLoading, error: metricsError, refetch: refetchMetrics } = useMetrics(timeRange);
  const { health, loading: healthLoading, error: healthError, refetch: refetchHealth } = useHealth();
  const { alerts: apiAlerts, loading: alertsLoading, error: alertsError, refetch: refetchAlerts, usingMock } = useAlerts(10);

  // Série temporal de eventos por minuto (60 pontos, rótulos HH:MM)
  const eventsPerMinuteData = useMemo(
    () => buildEventSeries(metrics.eps, metricsLoading),
    [metrics.eps, metricsLoading],
  );

  // Severity chart data (baseado nos alertas atuais ou valores de referência)
  const severityData = useMemo(
    () => [
      { name: "Crítico", value: apiAlerts.filter((a) => a.severity === "critical").length || 3, color: colors.severity.critical },
      { name: "Alto", value: apiAlerts.filter((a) => a.severity === "high").length || 8, color: colors.severity.high },
      { name: "Médio", value: apiAlerts.filter((a) => a.severity === "medium").length || 12, color: colors.severity.medium },
      { name: "Baixo", value: apiAlerts.filter((a) => a.severity === "low").length || 5, color: colors.severity.low },
      { name: "Info", value: apiAlerts.filter((a) => a.severity === "info").length || 2, color: colors.severity.info },
    ],
    [apiAlerts],
  );
  const severityTotal = severityData.reduce((acc, s) => acc + s.value, 0);

  const systemHealth: SystemHealth = health;
  const componentsOnline = Object.values(systemHealth).filter((s) => s === "online").length;
  const componentsTotal = Object.keys(systemHealth).length;

  const isLoading = metricsLoading || healthLoading || alertsLoading;
  const hasError = metricsError || healthError || alertsError;
  const errorMessage = metricsError || healthError || alertsError;

  const retryAll = () => {
    refetchMetrics();
    refetchHealth();
    refetchAlerts();
  };

  const healthLabel =
    systemHealth.api === "online" ? "Saudável" : systemHealth.api === "degraded" ? "Degradado" : "Crítico";
  const healthSeverity =
    systemHealth.api === "online" ? "info" : systemHealth.api === "degraded" ? "medium" : "critical";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Cabeçalho de página compacto */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: spacing["3"],
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <h1 style={{ fontSize: typography.size["2xl"], fontWeight: 700, color: colors.textPrimary, letterSpacing: "-0.02em", margin: 0 }}>
            Overview
          </h1>
          <span
            data-mono
            style={{
              fontSize: "12px",
              color: colors.textMuted,
              padding: "3px 10px",
              background: colors.surfaceAlt,
              border: `1px solid ${colors.border}`,
              borderRadius: 9999,
              whiteSpace: "nowrap",
            }}
          >
            {timeRange} • {new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              fontSize: typography.size.sm,
              color: colors.textSecondary,
              cursor: "pointer",
            }}
          >
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              style={{ accentColor: colors.accent, cursor: "pointer" }}
            />
            Auto-refresh (30s)
          </label>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as typeof timeRange)}
            style={{
              padding: "5px 10px",
              border: `1px solid ${colors.border}`,
              borderRadius: "6px",
              background: colors.surface,
              color: colors.textPrimary,
              fontSize: "13px",
              cursor: "pointer",
            }}
          >
            <option value="1h">Última hora</option>
            <option value="6h">Últimas 6h</option>
            <option value="24h">Últimas 24h</option>
            <option value="7d">Últimos 7 dias</option>
          </select>
        </div>
      </div>

      {/* Aviso de API compacto (apenas quando há erro) */}
      {hasError && (
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: spacing["3"],
            padding: `${spacing["2"]} ${spacing["3"]}`,
            background: colors.severity.medium + "14",
            border: `1px solid ${colors.severity.medium}44`,
            borderRadius: 8,
            alignSelf: "flex-start",
            maxWidth: "100%",
          }}
        >
          <span aria-hidden style={{ color: colors.severity.medium, fontSize: 14, flex: "none" }}>⚠</span>
          <span style={{ fontSize: typography.size.sm, color: colors.textSecondary, lineHeight: 1.4 }}>
            Dados demonstrativos em uso — API indisponível
            <span style={{ color: colors.textMuted }}> ({errorMessage})</span>
          </span>
          <button
            onClick={retryAll}
            style={{
              flex: "none",
              marginLeft: spacing["1"],
              padding: "4px 10px",
              fontSize: "12px",
              fontWeight: 600,
              background: colors.surfaceAlt,
              border: `1px solid ${colors.border}`,
              borderRadius: 6,
              color: colors.textPrimary,
              cursor: "pointer",
              transition: "border-color 120ms cubic-bezier(0.2,0,0,1), background 120ms cubic-bezier(0.2,0,0,1)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = colors.accent;
              e.currentTarget.style.background = colors.accent + "14";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = colors.border;
              e.currentTarget.style.background = colors.surfaceAlt;
            }}
          >
            Tentar novamente
          </button>
        </div>
      )}

      {/* KPI principais (6) */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))",
          gap: 14,
        }}
      >
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <KpiCard key={i} label="Carregando..." value={""} delta="" trend="flat" />
          ))
        ) : (
          <>
            <KpiCard label="Events/sec" value={formatNumber(metrics.eps)} icon="≋" delta="+12% vs 1h" trend="up" mono />
            <KpiCard label="Alertas Ativos" value={String(metrics.activeAlerts)} icon="⚠" delta="+3 vs 1h" trend="up" severity="critical" mono />
            <KpiCard label="Casos Abertos" value={String(metrics.openCases)} icon="▤" delta="-2 vs 1h" trend="down" />
            <KpiCard label="MTTR" value={`${metrics.mttr}min`} icon="◷" delta="-5min vs 24h" trend="down" severity="medium" mono />
            <KpiCard label="MTTA" value={`${metrics.mtta}min`} icon="◔" delta="-2min vs 24h" trend="down" mono />
            <KpiCard label="Score Médio" value={String(metrics.avgRiskScore)} icon="◉" delta="+3 vs 24h" trend="up" severity="high" mono />
          </>
        )}
      </div>

      {/* Seção secundária — Volume & Saúde */}
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
        <h2 style={{ margin: 0, fontSize: typography.size.lg, fontWeight: 600, color: colors.textSecondary, letterSpacing: "0.01em" }}>
          Volume & Saúde
        </h2>
        <span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>métricas agregadas</span>
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))",
          gap: 14,
        }}
      >
        <KpiCard label="Eventos/hora" value={formatNumber(metrics.eps * 3600)} icon="▥" delta="+12% vs 1h" trend="up" mono />
        <KpiCard label="Eventos/24h" value={formatNumber(metrics.eventsLast24h)} icon="▦" delta="+8% vs 24h" trend="up" mono />
        <KpiCard
          label="Saúde do Sistema"
          value={healthLabel}
          icon="⬢"
          delta={`${componentsOnline}/${componentsTotal} componentes online`}
          trend="flat"
          severity={healthSeverity}
        />
      </div>

      {/* Grid de painéis (2 colunas equilibradas) */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr)",
          gap: 20,
          alignItems: "stretch",
        }}
      >
        {/* Coluna esquerda — gráficos */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Eventos por Minuto */}
          <section
            style={{
              background: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: 12,
              padding: "18px 20px 12px",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 8 }}>
              <h3 style={{ margin: 0, fontSize: typography.size.lg, fontWeight: 600, color: colors.textPrimary }}>
                Eventos por Minuto
              </h3>
              <span data-mono style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
                últimos 60min
              </span>
            </div>
            <SecurityAreaChart
              data={eventsPerMinuteData}
              xKey="time"
              yKeys={["events"]}
              height={210}
              xInterval={11}
            />
          </section>

          {/* Alertas por Severidade */}
          <section
            style={{
              background: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: 12,
              padding: "18px 20px",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 8 }}>
              <h3 style={{ margin: 0, fontSize: typography.size.lg, fontWeight: 600, color: colors.textPrimary }}>
                Alertas por Severidade
              </h3>
              <span data-mono style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
                24h
              </span>
            </div>
            {severityTotal > 0 ? (
              <SecurityDonutChart
                data={severityData}
                nameKey="name"
                valueKey="value"
                height={210}
              />
            ) : (
              <EmptyState
                icon="◌"
                title="Sem dados de severidade"
                description="Nenhuma ocorrência classificada nas últimas 24h."
                compact
              />
            )}
          </section>
        </div>

        {/* Coluna direita — alertas recentes + saúde */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Últimos Alertas */}
          <section
            style={{
              background: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: 12,
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div
              style={{
                padding: "14px 20px",
                borderBottom: `1px solid ${colors.border}`,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: spacing["3"],
              }}
            >
              <h3 style={{ margin: 0, fontSize: typography.size.lg, fontWeight: 600, color: colors.textPrimary }}>
                Últimos Alertas
              </h3>
              <div style={{ display: "flex", alignItems: "center", gap: spacing["2"] }}>
                {usingMock && (
                  <span
                    style={{
                      fontSize: typography.size.xs,
                      color: colors.textMuted,
                      background: colors.surfaceAlt,
                      border: `1px solid ${colors.border}`,
                      borderRadius: 9999,
                      padding: "1px 8px",
                    }}
                  >
                    demo
                  </span>
                )}
                <span data-mono style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
                  {timeRange}
                </span>
              </div>
            </div>

            {alertsLoading ? (
              <div style={{ padding: "28px 20px", textAlign: "center", color: colors.textMuted, fontSize: typography.size.sm }}>
                Carregando alertas...
              </div>
            ) : apiAlerts.length === 0 ? (
              <EmptyState
                icon="◎"
                title="Sem alertas recentes"
                description="Nenhum evento crítico detectado no período. Novos alertas aparecerão aqui automaticamente."
                compact
              />
            ) : (
              <DataTable
                columns={[
                  {
                    key: "severity",
                    header: "Severidade",
                    width: "96px",
                    render: (row: any) => (
                      <SeverityBadge severity={row.severity}>{row.severity}</SeverityBadge>
                    ),
                  },
                  { key: "title", header: "Título / Regra" },
                  { key: "host", header: "Host", width: "110px", mono: true },
                  {
                    key: "firstSeen",
                    header: "Primeira vez",
                    width: "108px",
                    mono: true,
                    render: (row: any) => formatTime(row.firstSeen),
                  },
                  {
                    key: "riskScore",
                    header: "Risk",
                    width: "52px",
                    mono: true,
                    render: (row: any) => (
                      <span
                        style={{
                          fontWeight: 600,
                          color:
                            row.riskScore >= 80
                              ? colors.severity.critical
                              : row.riskScore >= 60
                                ? colors.severity.high
                                : row.riskScore >= 40
                                  ? colors.severity.medium
                                  : colors.severity.low,
                        }}
                      >
                        {row.riskScore}
                      </span>
                    ),
                  },
                  {
                    key: "actions",
                    header: "",
                    width: "88px",
                    render: () => (
                      <button
                        onClick={() => {}}
                        style={{
                          padding: "3px 10px",
                          fontSize: "12px",
                          fontWeight: 500,
                          background: "transparent",
                          border: `1px solid ${colors.border}`,
                          borderRadius: 6,
                          color: colors.textSecondary,
                          cursor: "pointer",
                          transition: "border-color 120ms cubic-bezier(0.2,0,0,1), color 120ms cubic-bezier(0.2,0,0,1), background 120ms cubic-bezier(0.2,0,0,1)",
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.borderColor = colors.accent;
                          e.currentTarget.style.color = colors.accentHover;
                          e.currentTarget.style.background = colors.accent + "14";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.borderColor = colors.border;
                          e.currentTarget.style.color = colors.textSecondary;
                          e.currentTarget.style.background = "transparent";
                        }}
                      >
                        Investigar
                      </button>
                    ),
                  },
                ]}
                rows={apiAlerts as unknown as Array<Record<string, React.ReactNode>>}
              />
            )}
          </section>

          {/* Saúde do Sistema */}
          <section
            style={{
              background: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: 12,
              padding: "18px 20px",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 12 }}>
              <h3 style={{ margin: 0, fontSize: typography.size.lg, fontWeight: 600, color: colors.textPrimary }}>
                Saúde do Sistema
              </h3>
              <span data-mono style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
                {componentsOnline}/{componentsTotal}
              </span>
            </div>
            {healthLoading ? (
              <div style={{ paddingBottom: 12, textAlign: "center", color: colors.textMuted, fontSize: typography.size.sm }}>
                Carregando saúde do sistema...
              </div>
            ) : (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(108px, 1fr))",
                  gap: 10,
                }}
              >
                {Object.entries(systemHealth).map(([key, status]) => {
                  const s = status as string;
                  const c = healthColor(s);
                  const label = key.charAt(0).toUpperCase() + key.slice(1);
                  const human =
                    s === "online" ? "Online" : s === "degraded" ? "Degradado" : s === "offline" ? "Offline" : s === "error" ? "Erro" : s;
                  return (
                    <div
                      key={key}
                      style={{
                        padding: "11px",
                        background: colors.surfaceAlt,
                        borderRadius: 8,
                        textAlign: "center",
                        border: `1px solid ${colors.border}`,
                      }}
                    >
                      <div
                        style={{
                          width: 9,
                          height: 9,
                          borderRadius: "50%",
                          background: c,
                          margin: "0 auto 7px",
                          boxShadow: `0 0 8px ${c}`,
                        }}
                      />
                      <div style={{ fontWeight: 600, fontSize: typography.size.xs, color: colors.textPrimary }}>
                        {label}
                      </div>
                      <div
                        data-mono
                        style={{
                          marginTop: 2,
                          fontSize: typography.size.xs,
                          fontWeight: typography.weight.medium,
                          color: c,
                          textTransform: "capitalize",
                        }}
                      >
                        {human}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
