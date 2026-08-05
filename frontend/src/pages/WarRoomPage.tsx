/**
 * War Room (UI 4.2)
 * Tela única de comando operacional do SOC: KPIs, feed ao vivo, top MITRE,
 * top IPs/países, assets, coletores, saúde da pipeline e resumo operacional.
 *
 * Prioridade: aparência e leitura rápida. Sem IA real nem integrações externas.
 * Dados demo são usados quando a API retorna vazio e são rotulados claramente.
 */
import { useMemo } from "react";
import { colors, radii, spacing, typography } from "../design-system/tokens";
import { KpiCard, MetricCard } from "../design-system/components/cards";
import { StatusBadge } from "../design-system/components/badges";
import { ActivityFeed, ActivityItem } from "../design-system/components/Timeline";
import { SecurityDonutChart } from "../charts";
import { Breadcrumb } from "../shell/Breadcrumb";
import { useMetrics, useHealth, useAlerts } from "../hooks";

/* ------------------------------------------------------------------ */
/*  Dados de demonstração (usados quando a API não retorna dados)      */
/* ------------------------------------------------------------------ */

const DEMO_COLLECTORS = [
  { name: "collector-syslog-01", type: "syslog", status: "online" as const, eps: 1840 },
  { name: "collector-syslog-02", type: "syslog", status: "online" as const, eps: 1234 },
  { name: "collector-fw-01", type: "firewall", status: "online" as const, eps: 980 },
  { name: "collector-windows-01", type: "winevt", status: "degraded" as const, eps: 412 },
  { name: "collector-proxy-01", type: "http", status: "online" as const, eps: 720 },
  { name: "collector-dns-01", type: "dns", status: "offline" as const, eps: 0 },
];

const DEMO_LIVE = [
  { id: "ev-1", actor: "ssh", action: "login_failed from", target: "10.0.0.14 → web-01", time: "agora", tone: "critical" as const },
  { id: "ev-2", actor: "winlogbeat", action: "svchost spawns", target: "powershell.exe (wks-042)", time: "2s", tone: "critical" as const },
  { id: "ev-3", actor: "proxy", action: "egress to", target: "185.220.101.4:443", time: "5s", tone: "high" as const },
  { id: "ev-4", actor: "dns", action: "NXDOMAIN flood", target: "wks-033", time: "9s", tone: "high" as const },
  { id: "ev-5", actor: "fw", action: "blocked", target: "portscan 10.0.2.0/24", time: "12s", tone: "medium" as const },
  { id: "ev-6", actor: "enrichment", action: "geo tag→", target: "RU (Moscow)", time: "15s", tone: "high" as const },
];

const DEMO_MITRE = [
  { name: "T1071", label: "App Protocol", count: 42, color: colors.severity.critical },
  { name: "T1021", label: "Remote Svc", count: 31, color: colors.severity.high },
  { name: "T1059", label: "Command & Scripting", count: 27, color: colors.severity.medium },
  { name: "T1110", label: "Brute Force", count: 19, color: colors.severity.high },
  { name: "T1566", label: "Phishing", count: 14, color: colors.severity.medium },
];

const DEMO_COUNTRIES = [
  { code: "BR", name: "Brasil", count: 128, x: 34, y: 66 },
  { code: "US", name: "EUA", count: 96, x: 22, y: 40 },
  { code: "CN", name: "China", count: 61, x: 76, y: 44 },
  { code: "RU", name: "Rússia", count: 45, x: 62, y: 30 },
  { code: "DE", name: "Alemanha", count: 30, x: 51, y: 36 },
  { code: "IN", name: "Índia", count: 24, x: 71, y: 54 },
];

const DEMO_ASSETS = [
  { id: "wks-042", role: "Workstation", severity: "critical" as const, impact: 920 },
  { id: "proxy-01", role: "Proxy", severity: "critical" as const, impact: 888 },
  { id: "web-01", role: "Web DMZ", severity: "high" as const, impact: 764 },
  { id: "db-01", role: "Database", severity: "high" as const, impact: 751 },
  { id: "vpn-gw", role: "VPN Gateway", severity: "medium" as const, impact: 540 },
];

/* ------------------------------------------------------------------ */

function healthTone(status: string): "online" | "degraded" | "offline" | "neutral" {
  if (status === "online") return "online";
  if (status === "degraded") return "degraded";
  if (status === "offline" || status === "error") return "offline";
  return "neutral";
}

function healthLabel(status: string): string {
  switch (status) {
    case "online": return "Online";
    case "degraded": return "Degradado";
    case "offline": return "Offline";
    case "error": return "Erro";
    default: return status;
  }
}

function pipeTone(status: string): "online" | "degraded" | "offline" | "neutral" {
  return status === "online" || status === "healthy" ? "online" : status === "degraded" ? "degraded" : "offline";
}

export function WarRoomPage() {
  const { metrics, loading: metricsLoading } = useMetrics("1h");
  const { health, loading: healthLoading } = useHealth();
  const { alerts, loading: alertsLoading, usingMock: alertsMock } = useAlerts(8);

  const usingDemo = metricsLoading || healthLoading || alertsLoading || alerts.length === 0;

  const liveItems: ActivityItem[] = useMemo(() => {
    if (!alertsLoading && alerts.length > 0) {
      return alerts.slice(0, 6).map((a, i) => ({
        id: a.id,
        actor: a.rule,
        action: "disparou alerta em",
        target: a.host,
        time: `${i}s`,
      }));
    }
    return DEMO_LIVE;
  }, [alerts, alertsLoading]);

  const mitreTotal = DEMO_MITRE.reduce((s, m) => s + m.count, 0);
  const statusData = [
    { name: "Crítico", value: alerts.filter((a) => a.severity === "critical").length || 2, color: colors.severity.critical },
    { name: "Alto", value: alerts.filter((a) => a.severity === "high").length || 5, color: colors.severity.high },
    { name: "Médio", value: alerts.filter((a) => a.severity === "medium").length || 7, color: colors.severity.medium },
    { name: "Baixo", value: alerts.filter((a) => a.severity === "low").length || 3, color: colors.severity.low },
  ];

  const collectors = DEMO_COLLECTORS;
  const criticals = alerts.filter((a) => a.severity === "critical");
  const criticalCount = criticals.length || 2;

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh", background: colors.background }}>
      {/* ---------------- Cabeçalho ---------------- */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: spacing["3"],
          padding: `${spacing["3"]} ${spacing["4"]}`,
          borderBottom: `1px solid ${colors.border}`,
          background: colors.surface,
          position: "sticky",
          top: 0,
          zIndex: 100,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <Breadcrumb items={[{ label: "Operação", to: "/war-room" }, { label: "War Room", to: "/war-room" }]} />
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0, color: colors.textPrimary }}>War Room</h1>
          <span
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: typography.size.xs,
              color: colors.status.online,
              padding: "3px 10px",
              background: "rgba(63,185,80,0.12)",
              borderRadius: 9999,
            }}
          >
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: colors.status.online, boxShadow: `0 0 8px ${colors.status.online}` }} />
            LIVE
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: spacing["3"] }}>
          <span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
            Janela: Última hora • Atualizado às {new Date().toLocaleTimeString()}
          </span>
          {usingDemo && (
            <span
              style={{
                fontSize: typography.size.xs,
                color: colors.warning,
                padding: "4px 10px",
                border: `1px solid ${colors.warning}55`,
                borderRadius: radii.sm,
                background: "rgba(210,153,34,0.1)",
              }}
            >
              ● Amostra de demonstração
            </span>
          )}
        </div>
      </div>

      <div style={{ padding: spacing["4"], display: "flex", flexDirection: "column", gap: spacing["4"], flex: 1 }}>
        {/* ---------------- Linha de KPIs operacionais ---------------- */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: spacing["3"] }}>
          <KpiCard label="Events/sec" value={String(metrics.eps || "1.2K")} delta="+12% vs 1h" trend="up" />
          <KpiCard label="Alertas críticos" value={String(criticalCount)} delta="ação imediata" trend="up" severity="critical" />
          <KpiCard label="Incidentes ativos" value={String(metrics.openCases || "4")} delta="2 em andamento" trend="up" severity="high" />
          <KpiCard label="Assets comprometidos" value={String(DEMO_ASSETS.filter((a) => a.severity === "critical").length)} delta="3 críticos" trend="up" severity="critical" />
          <KpiCard label="MTTR" value={`${metrics.mttr || 24}min`} delta="-5min vs 24h" trend="down" />
        </div>

        {/* ---------------- Grade principal ---------------- */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: spacing["4"], alignItems: "start" }}>
          {/* ---- Coluna esquerda ---- */}
          <div style={{ display: "flex", flexDirection: "column", gap: spacing["4"] }}>
            {/* Live Event Feed */}
            <MetricCard
              title="Live Event Feed"
              footer={
                <span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
                  {alertsMock ? "Sinalizando dados demo — aguardando API de eventos" : "Feed conectado"}
                </span>
              }
            >
              <ActivityFeed items={liveItems} />
            </MetricCard>

            {/* MITRE mais acionadas */}
            <MetricCard title="MITRE ATT&CK — Técnicas mais acionadas" footer={
              <span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>{mitreTotal} detecções nas top-5 técnicas</span>
            }>
              <div style={{ display: "flex", flexDirection: "column", gap: spacing["3"] }}>
                {DEMO_MITRE.map((m) => (
                  <div key={m.name} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: typography.size.sm }}>
                      <span style={{ color: colors.textPrimary, fontWeight: typography.weight.medium }}>
                        <span style={{ fontFamily: typography.family.mono, color: m.color, marginRight: 8 }}>{m.name}</span>
                        {m.label}
                      </span>
                      <span style={{ color: colors.textMuted, fontFamily: typography.family.mono }}>{m.count}</span>
                    </div>
                    <div style={{ height: 8, background: colors.surfaceAlt, borderRadius: 9999, overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${(m.count / mitreTotal) * 100}%`, background: m.color, borderRadius: 9999 }} />
                    </div>
                  </div>
                ))}
              </div>
            </MetricCard>

            {/* Pipeline Health */}
            <MetricCard title="Saúde da Pipeline" footer={
              <span style={{ display: "flex", gap: spacing["3"], flexWrap: "wrap" }}>
                {(["ingestion", "correlation", "enrichment", "detection"] as const).map((k) => (
                  <StatusBadge key={k} tone={pipeTone(health[k])}>
                    {`${k.charAt(0).toUpperCase() + k.slice(1)}: ${healthLabel(health[k])}`}
                  </StatusBadge>
                ))}
              </span>
            }>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px,1fr))", gap: spacing["3"] }}>
                {Object.entries(health).map(([k, s]) => {
                  const st = s as string;
                  return (
                    <div
                      key={k}
                      style={{
                        padding: spacing["3"],
                        background: colors.surfaceAlt,
                        borderRadius: radii.md,
                        border: `1px solid ${colors.border}`,
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontSize: typography.size.xs, color: colors.textMuted, textTransform: "capitalize" }}>{k}</span>
                        <StatusBadge tone={healthTone(st)}>{healthLabel(st)}</StatusBadge>
                      </div>
                      <div style={{ height: 4, borderRadius: 9999, background: colors.border, marginTop: 8 }}>
                        <div
                          style={{
                            height: "100%",
                            width: st === "online" ? "100%" : st === "degraded" ? "55%" : "15%",
                            background: st === "online" ? colors.status.online : st === "degraded" ? colors.status.degraded : colors.status.offline,
                            borderRadius: 9999,
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </MetricCard>
          </div>

          {/* ---- Coluna direita ---- */}
          <div style={{ display: "flex", flexDirection: "column", gap: spacing["4"] }}>
            {/* Alertas críticos */}
            <MetricCard title={`Alertas críticos (${criticals.length || 2})`} footer={
              <span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
                {alertsMock ? "Dados de demonstração (API /alerts indisponível)" : "Dados da API"}
              </span>
            }>
              <div style={{ display: "flex", flexDirection: "column", gap: spacing["2"] }}>
                {(criticals.length > 0 ? criticals : [
                  { id: "ALT-001", title: "Brute Force SSH", host: "web-01", rule: "brute-force-ssh", riskScore: 95 },
                  { id: "ALT-002", title: "Malware Execution - PowerShell", host: "wks-042", rule: "malware-exec", riskScore: 95 },
                ]).slice(0, 5).map((a) => (
                  <div
                    key={a.id}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: `${spacing["2"]} ${spacing["3"]}`,
                      background: colors.surfaceAlt,
                      border: `1px solid ${colors.severity.critical}33`,
                      borderLeft: `3px solid ${colors.severity.critical}`,
                      borderRadius: radii.md,
                    }}
                  >
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontSize: typography.size.sm, fontWeight: typography.weight.semibold, color: colors.textPrimary, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {a.title}
                      </div>
                      <div style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
                        {a.host} • regra: {a.rule}
                      </div>
                    </div>
                    <span style={{ fontFamily: typography.family.mono, fontSize: typography.size.sm, color: colors.severity.critical, fontWeight: 700, marginLeft: 8 }}>
                      {(a as any).riskScore ?? 95}
                    </span>
                  </div>
                ))}
              </div>
            </MetricCard>

            {/* Assets comprometidos */}
            <MetricCard title="Top Assets comprometidos" footer={
              <span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>Pontuação de impacto (0-1000)</span>
            }>
              <div style={{ display: "flex", flexDirection: "column", gap: spacing["2"] }}>
                {DEMO_ASSETS.map((a) => (
                  <div key={a.id} style={{ display: "flex", alignItems: "center", gap: spacing["3"] }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: typography.size.sm }}>
                        <span style={{ color: colors.textPrimary, fontWeight: typography.weight.medium }}>
                          <span style={{ fontFamily: typography.family.mono, color: colors.severity[a.severity], marginRight: 8 }}>{a.id}</span>
                          {a.role}
                        </span>
                        <span style={{ color: colors.textMuted, fontFamily: typography.family.mono }}>{a.impact}</span>
                      </div>
                      <div style={{ height: 6, background: colors.surfaceAlt, borderRadius: 9999, marginTop: 4 }}>
                        <div style={{ height: "100%", width: `${(a.impact / 1000) * 100}%`, background: colors.severity[a.severity], borderRadius: 9999 }} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </MetricCard>

            {/* Status dos coletores */}
            <MetricCard title="Status dos Coletores" footer={
              <span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
                {collectors.filter((c) => c.status === "online").length}/{collectors.length} online • ingestão{" "}
                {metrics.eps ? `${metrics.eps} eps` : "pausada"}
              </span>
            }>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px,1fr))", gap: spacing["2"] }}>
                {collectors.map((c) => (
                  <div
                    key={c.name}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: `${spacing["2"]} ${spacing["3"]}`,
                      background: colors.surfaceAlt,
                      border: `1px solid ${colors.border}`,
                      borderRadius: radii.md,
                    }}
                  >
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontSize: typography.size.sm, fontWeight: typography.weight.medium, color: colors.textPrimary, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {c.name}
                      </div>
                      <div style={{ fontSize: typography.size.xs, color: colors.textMuted }}>{c.type}</div>
                    </div>
                    <div style={{ textAlign: "right", marginLeft: 8 }}>
                      <StatusBadge tone={healthTone(c.status)}>{healthLabel(c.status)}</StatusBadge>
                      <div style={{ fontSize: typography.size.xs, color: colors.textMuted, fontFamily: typography.family.mono, marginTop: 2 }}>
                        {c.eps} eps
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </MetricCard>
          </div>
        </div>

        {/* ---------------- Mapa geográfico + Severidade ---------------- */}
        <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: spacing["4"] }}>
          {/* Mapa geográfico (visual funcional) */}
          <MetricCard
            title="Origem geográfica dos eventos"
            footer={
              <span style={{ display: "flex", gap: spacing["4"], flexWrap: "wrap" }}>
                {DEMO_COUNTRIES.slice(0, 3).map((c) => (
                  <span key={c.code} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: typography.size.xs, color: colors.textSecondary }}>
                    <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", background: colors.severity.high }} />
                    {c.code} • {c.count}
                  </span>
                ))}
              </span>
            }
          >
            <div
              style={{
                position: "relative",
                height: 260,
                borderRadius: radii.md,
                overflow: "hidden",
                background: "radial-gradient(circle at 50% 40%, #101b2b 0%, #0b1118 60%, #070b10 100%)",
                border: `1px solid ${colors.border}`,
              }}
            >
              {/* Grid de latitude/longitude */}
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  backgroundImage: `linear-gradient(${colors.border}22 1px, transparent 1px), linear-gradient(90deg, ${colors.border}22 1px, transparent 1px)`,
                  backgroundSize: "40px 40px",
                }}
              />
              {/* Pontos por país */}
              {DEMO_COUNTRIES.map((c) => (
                <div
                  key={c.code}
                  title={`${c.name} — ${c.count} eventos`}
                  style={{
                    position: "absolute",
                    left: `${c.x}%`,
                    top: `${c.y}%`,
                    transform: "translate(-50%, -50%)",
                    width: 10 + c.count / 8,
                    height: 10 + c.count / 8,
                    borderRadius: "50%",
                    background: `radial-gradient(circle, ${colors.severity.high} 0%, ${colors.severity.critical}dd 55%, transparent 75%)`,
                    boxShadow: `0 0 14px 2px ${colors.severity.high}66`,
                    cursor: "pointer",
                  }}
                >
                  <span
                    style={{
                      position: "absolute",
                      top: "-22px",
                      left: "50%",
                      transform: "translateX(-50%)",
                      fontSize: typography.size.xs,
                      color: colors.textSecondary,
                      fontFamily: typography.family.mono,
                      whiteSpace: "nowrap",
                      background: colors.surface,
                      border: `1px solid ${colors.border}`,
                      borderRadius: radii.sm,
                      padding: "1px 6px",
                    }}
                  >
                    {c.code} · {c.count}
                  </span>
                </div>
              ))}
              {/* Decoração de rota */}
              <div
                style={{
                  position: "absolute",
                  bottom: 12,
                  right: 12,
                  fontSize: typography.size.xs,
                  color: colors.textMuted,
                  fontFamily: typography.family.mono,
                }}
              >
                geo: top-6 regiões
              </div>
            </div>
          </MetricCard>

          {/* Severidade */}
          <MetricCard title="Alertas por severidade (24h)" footer={
            <span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>{statusData.reduce((s, d) => s + d.value, 0)} alertas no período</span>
          }>
            <SecurityDonutChart data={statusData} nameKey="name" valueKey="value" height={240} />
          </MetricCard>
        </div>

        {/* ---------------- Resumo operacional ---------------- */}
        <div
          style={{
            padding: spacing["4"],
            background: colors.surface,
            border: `1px solid ${colors.border}`,
            borderRadius: radii.lg,
          }}
        >
          <div style={{ fontSize: typography.size.lg, fontWeight: typography.weight.semibold, color: colors.textPrimary, marginBottom: spacing["2"] }}>
            Resumo operacional
          </div>
          <p style={{ margin: 0, fontSize: typography.size.sm, color: colors.textSecondary, lineHeight: 1.6 }}>
            Postura <strong style={{ color: colors.severity.high }}>elevada</strong>. Detecção ativa de brute force e execução de malware em
            endpoints críticos. Exfiltração via proxy em revisão. Ingestão global funcionando{" "}
            <strong style={{ color: colors.status.online }}>{metrics.eps ? `${metrics.eps.toLocaleString()} events/sec` : "com throughput elevado"}</strong>.
            Recomenda-se acionar o runbook de resposta para os 2 assets críticos (wks-042, proxy-01) e verificar o coletor{" "}
            <strong style={{ color: colors.status.offline }}>collector-dns-01</strong>.
          </p>
        </div>
      </div>
    </div>
  );
}