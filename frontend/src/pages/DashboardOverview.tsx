/**
 * Dashboard Overview (UI 4.1)
 * Visão geral do SOC com KPIs, gráficos, tabela de alertas e saúde do sistema.
 */
import { useState } from "react";
import { colors, spacing } from "../design-system/tokens";
import { KpiCard } from "../design-system/components/cards";
import { DataTable } from "../design-system/components/DataTable";
import { SeverityBadge } from "../design-system/components/badges";
import { SecurityAreaChart, SecurityDonutChart } from "../charts";
import { Breadcrumb } from "../shell/Breadcrumb";

interface DashboardMetrics {
  eps: number;
  activeAlerts: number;
  openCases: number;
  eventsLast24h: number;
  avgRiskScore: number;
  mttr: number;
  mtta: number;
}

interface RecentAlert {
  id: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  status: "open" | "in_progress" | "resolved" | "closed" | "false_positive";
  source: string;
  host: string;
  user?: string;
  rule: string;
  firstSeen: string;
  riskScore: number;
}

interface SystemHealth {
  ingestion: "healthy" | "degraded" | "critical";
  correlation: "healthy" | "degraded" | "critical";
  enrichment: "healthy" | "degraded" | "critical";
  detection: "healthy" | "degraded" | "critical";
  alerts: "healthy" | "degraded" | "critical";
  cases: "healthy" | "degraded" | "critical";
  storage: "healthy" | "degraded" | "critical";
  api: "healthy" | "degraded" | "critical";
}

const MOCK_ALERTS: RecentAlert[] = [
  { id: "ALT-001", title: "Brute Force SSH", severity: "critical", status: "open", source: "web-01", host: "web-01", user: "root", rule: "brute-force-ssh", firstSeen: "2026-08-04T10:15:00", riskScore: 95 },
  { id: "ALT-002", title: "Malware Execution - PowerShell", severity: "critical", status: "open", source: "wks-042", host: "wks-042", user: "john.doe", rule: "malware-exec", firstSeen: "2026-08-04T14:22:00", riskScore: 95 },
  { id: "ALT-003", title: "Impossible Travel - geo impossível", severity: "high", status: "in_progress", source: "vpn-gateway", host: "vpn-gw", user: "jane.smith", rule: "impossible-travel", firstSeen: "2026-08-04T09:15:00", riskScore: 78 },
  { id: "ALT-004", title: "Data Exfiltration - Cloud Storage", severity: "critical", status: "in_progress", source: "proxy-01", host: "proxy-01", user: "jane.doe", rule: "data-exfiltration", firstSeen: "2026-08-04T08:30:00", riskScore: 92 },
  { id: "ALT-005", title: "Crypto Miner - XMRig", severity: "high", status: "open", source: "wks-033", host: "wks-033", user: "svc-backup", rule: "crypto-miner", firstSeen: "2026-08-04T06:00:00", riskScore: 88 },
];

const eventsPerMinuteData = Array.from({ length: 60 }, (_, i) => ({
  time: `${i}:${String(Math.floor(Math.random() * 60)).padStart(2, "0")}`,
  events: Math.floor(Math.random() * 50) + 10,
}));

const MOCK_HEALTH: SystemHealth = {
  ingestion: "healthy",
  correlation: "healthy",
  enrichment: "healthy",
  detection: "healthy",
  alerts: "healthy",
  cases: "healthy",
  storage: "healthy",
  api: "healthy",
};

function healthColor(status: string): string {
  switch (status) {
    case "healthy": return colors.status.online;
    case "degraded": return colors.status.degraded;
    case "critical": return colors.status.offline;
    default: return colors.textMuted;
  }
}

function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return String(num);
}

export function DashboardOverview() {
  const [metrics] = useState<DashboardMetrics>({
    eps: 1247,
    activeAlerts: 23,
    openCases: 5,
    eventsLast24h: 298740,
    avgRiskScore: 68,
    mttr: 47,
    mtta: 12,
  });
  const [recentAlerts] = useState<RecentAlert[]>(MOCK_ALERTS);
  const [systemHealth] = useState<SystemHealth>(MOCK_HEALTH);
  const [timeRange, setTimeRange] = useState<"1h" | "6h" | "24h" | "7d">("1h");
  const [autoRefresh, setAutoRefresh] = useState(true);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        background: colors.background,
      }}
    >
      {/* Topbar */}
      <div
        style={{
          padding: `${spacing["3"]} ${spacing["4"]}`,
          borderBottom: `1px solid ${colors.border}`,
          background: colors.surface,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: spacing["3"],
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <Breadcrumb
            items={[{ label: "Dashboard", to: "/" }]}
          />
          <h1 style={{ fontSize: "24px", fontWeight: 600, color: colors.textPrimary, margin: 0 }}>
            Dashboard Overview
          </h1>
          <span
            style={{
              fontSize: "12px",
              color: colors.textMuted,
              padding: "4px 12px",
              background: colors.surfaceAlt,
              borderRadius: 9999,
            }}
          >
            {timeRange} • Última atualização: {new Date().toLocaleTimeString()}
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              fontSize: "14px",
              color: colors.textSecondary,
            }}
          >
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh (30s)
          </label>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as typeof timeRange)}
            style={{
              padding: "6px 12px",
              border: `1px solid ${colors.border}`,
              borderRadius: "6px",
              background: colors.surface,
              color: colors.textPrimary,
              fontSize: "13px",
            }}
          >
            <option value="1h">Última hora</option>
            <option value="6h">Últimas 6h</option>
            <option value="24h">Últimas 24h</option>
            <option value="7d">Últimos 7 dias</option>
          </select>
        </div>
      </div>

      {/* KPI Row */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "16px",
          padding: "24px 24px 0",
        }}
      >
        <KpiCard label="Events/sec" value={formatNumber(metrics.eps)} delta="+12% vs 1h ago" trend="up" />
        <KpiCard label="Alertas Ativos" value={String(metrics.activeAlerts)} delta="+3 vs 1h ago" trend="up" severity="critical" />
        <KpiCard label="Casos Abertos" value={String(metrics.openCases)} delta="-2 vs 1h ago" trend="down" />
        <KpiCard label="Eventos/hora" value={formatNumber(metrics.eps * 3600)} delta="+12% vs 1h ago" trend="up" />
        <KpiCard label="Eventos/24h" value={formatNumber(metrics.eventsLast24h)} delta="+8% vs 24h ago" trend="up" />
        <KpiCard label="MTTR" value={`${metrics.mttr}min`} delta="-5min vs 24h ago" trend="down" severity="medium" />
        <KpiCard label="MTTA" value={`${metrics.mtta}min`} delta="-2min vs 24h ago" trend="down" />
        <KpiCard label="Score Médio" value={String(metrics.avgRiskScore)} delta="+3 vs 24h ago" trend="up" severity="high" />
        <KpiCard
          label="Saúde Sistema"
          value={
            systemHealth.api === "healthy" ? "Saudável" :
            systemHealth.api === "degraded" ? "Degradado" : "Crítico"
          }
          severity={
            systemHealth.api === "healthy" ? "info" :
            systemHealth.api === "degraded" ? "medium" : "critical"
          }
        />
      </div>

      {/* Charts + Tables Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 24,
          padding: "0 24px 24px",
          minHeight: "calc(100vh - 320px)",
        }}
      >
        {/* Coluna esquerda - Gráficos */}
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {/* Eventos por Minuto */}
          <div
            style={{
              background: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: "12px",
              padding: "20px",
              minHeight: 300,
            }}
          >
            <h3 style={{ margin: "0 0 16px", fontSize: "16px", fontWeight: 600, color: colors.textPrimary }}>
              Eventos por Minuto (últimos 60min)
            </h3>
            <SecurityAreaChart
              data={eventsPerMinuteData}
              xKey="time"
              yKeys={["events"]}
              height={240}
            />
          </div>

          {/* Severidade */}
          <div
            style={{
              background: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: "12px",
              padding: "20px",
              minHeight: 300,
            }}
          >
            <h3 style={{ margin: "0 0 16px", fontSize: "16px", fontWeight: 600, color: colors.textPrimary }}>
              Alertas por Severidade (24h)
            </h3>
            <SecurityDonutChart
              data={[
                { name: "Crítico", value: 3, color: colors.severity.critical },
                { name: "Alto", value: 8, color: colors.severity.high },
                { name: "Médio", value: 12, color: colors.severity.medium },
                { name: "Baixo", value: 5, color: colors.severity.low },
                { name: "Info", value: 2, color: colors.severity.info },
              ]}
              nameKey="name"
              valueKey="value"
              height={240}
            />
          </div>
        </div>

        {/* Coluna direita - Alertas recentes + Saúde */}
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {/* Últimos Alertas */}
          <div
            style={{
              background: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: "12px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                padding: "16px 20px",
                borderBottom: `1px solid ${colors.border}`,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 600, color: colors.textPrimary }}>
                Últimos Alertas
              </h3>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value as typeof timeRange)}
                style={{
                  padding: "6px 12px",
                  borderRadius: "6px",
                  border: `1px solid ${colors.border}`,
                  background: colors.surface,
                  color: colors.textPrimary,
                  fontSize: "13px",
                }}
              >
                <option value="1h">Última hora</option>
                <option value="6h">Últimas 6h</option>
                <option value="24h">Últimas 24h</option>
                <option value="7d">Últimos 7 dias</option>
              </select>
            </div>

            <DataTable
              columns={[
                {
                  key: "severity",
                  header: "Severidade",
                  width: "100px",
                  render: (row: any) => (
                    <SeverityBadge severity={row.severity}>{row.severity}</SeverityBadge>
                  ),
                },
                { key: "title", header: "Título / Regra" },
                { key: "source", header: "Origem", width: "140px" },
                { key: "host", header: "Host", width: "120px" },
                { key: "firstSeen", header: "Primeira vez", width: "140px" },
                {
                  key: "riskScore",
                  header: "Risk",
                  width: "70px",
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
                  key: "status",
                  header: "Status",
                  width: "120px",
                  render: (row: any) => (
                    <span
                      style={{
                        fontSize: "12px",
                        color: row.status === "open" ? colors.severity.critical : colors.textSecondary,
                        textTransform: "capitalize",
                      }}
                    >
                      {row.status.replace("_", " ")}
                    </span>
                  ),
                },
                {
                  key: "actions",
                  header: "",
                  width: "100px",
                  render: () => (
                    <button
                      onClick={() => {}}
                      style={{
                        padding: "4px 8px",
                        fontSize: "12px",
                        background: "transparent",
                        border: `1px solid ${colors.border}`,
                        borderRadius: "4px",
                        color: colors.textSecondary,
                        cursor: "pointer",
                      }}
                    >
                      Investigar
                    </button>
                  ),
                },
              ]}
              rows={recentAlerts as unknown as Array<Record<string, React.ReactNode>>}
            />
          </div>

          {/* Saúde do Sistema */}
          <div
            style={{
              background: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: "12px",
              padding: "20px",
            }}
          >
            <h3
              style={{
                margin: "0 0 16px",
                fontSize: "16px",
                fontWeight: 600,
                color: colors.textPrimary,
              }}
            >
              Saúde do Sistema
            </h3>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                gap: "16px",
              }}
            >
              {Object.entries(systemHealth).map(([key, status]) => (
                <div
                  key={key}
                  style={{
                    padding: "16px",
                    background: colors.surfaceAlt,
                    borderRadius: "8px",
                    textAlign: "center",
                    border: `1px solid ${colors.border}`,
                  }}
                >
                  <div
                    style={{
                      width: 12,
                      height: 12,
                      borderRadius: "50%",
                      background: healthColor(status),
                      margin: "0 auto 8px",
                      boxShadow: `0 0 8px ${healthColor(status)}`,
                    }}
                  />
                  <div style={{ fontWeight: 600, fontSize: "14px", marginTop: 8, color: colors.textPrimary }}>
                    {key.charAt(0).toUpperCase() + key.slice(1)}
                  </div>
                  <div
                    style={{
                      marginTop: 4,
                      fontSize: "12px",
                      color: colors.textSecondary,
                      textTransform: "capitalize",
                    }}
                  >
                    {status === "healthy" ? "Saudável" : status === "degraded" ? "Degradado" : "Crítico"}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
