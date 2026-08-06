/**
 * Detection Dashboard (Sprint 2.17 WP5) — agregações reais de /soc/detection.
 * Regras mais acionadas, MITRE, IOCs, assets críticos e tendência temporal.
 */
import { useState } from "react";
import { colors, radii, spacing, typography } from "../design-system/tokens";
import { MetricCard } from "../design-system/components/cards";
import { EmptyState, LoadingSkeleton } from "../design-system/components/feedback";
import { Breadcrumb } from "../shell/Breadcrumb";
import { SecurityBarChart } from "../charts";
import { apiClient } from "../api/client";

interface DetDto {
  top_rules: { rule_id: string; count: number }[];
  top_mitre: { mitre: string; count: number }[];
  top_iocs: { value: string; count: number }[];
  critical_assets: string[];
  alerts_by_rule: Record<string, number>;
  trend: { time: string; events: number }[];
  rules_total: number;
  rules_enabled: number;
}

export function DetectionDashboardPage() {
  const [data, setData] = useState<DetDto | null>(null);
  const [loading, setLoading] = useState(true);

  if (data === null && loading) {
    apiClient.get<DetDto>("/soc/detection").then((r) => { setData(r.success && r.data ? r.data : null); setLoading(false); });
  }

  if (loading) return <LoadingSkeleton rows={8} variant="card" />;
  if (!data) return <EmptyState title="Detection indisponível" description="Execute o fluxo SOC (demo) para gerar dados reais." onRetry={() => { setData(null); setLoading(true); }} />;

  const barData = data.top_rules.map((r) => ({ name: r.rule_id, value: r.count }));

  return (
    <div style={{ background: colors.background, minHeight: "100vh", padding: spacing["4"] }}>
      <Breadcrumb items={[{ label: "Operação", to: "/" }, { label: "Detection", to: "/detection" }]} />
      <h1 style={{ fontSize: typography.size["2xl"], color: colors.textPrimary, margin: "6px 0 16px" }}>Detection Dashboard</h1>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px,1fr))", gap: spacing["3"], marginBottom: spacing["4"] }}>
        <Mini label="Regras" value={String(data.rules_total)} sub={`${data.rules_enabled} habilitadas`} />
        <Mini label="Top MITRE" value={String(data.top_mitre.length)} sub="técnicas" />
        <Mini label="Top IOC" value={String(data.top_iocs.length)} sub="indicadores" />
        <Mini label="Assets críticos" value={String(data.critical_assets.length)} sub="ativos" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: spacing["4"] }}>
        <MetricCard title="Alertas por regra (top)">
          <SecurityBarChart data={barData} xKey="name" yKeys={["value"]} height={220} />
        </MetricCard>
        <MetricCard title="Tendência temporal (eventos/min)">
          <SecurityBarChart data={data.trend.map((t) => ({ ...t }))} xKey="time" yKeys={["events"]} height={220} />
        </MetricCard>
        <MetricCard title="MITRE ATT&CK mais frequente">
          {data.top_mitre.length === 0 ? <Muted /> : data.top_mitre.map((m) => (
            <div key={m.mitre} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", fontSize: typography.size.sm }}>
              <span style={{ fontFamily: typography.family.mono, color: colors.textSecondary }}>{m.mitre}</span>
              <span style={{ color: colors.textPrimary, fontWeight: 600 }}>{m.count}</span>
            </div>
          ))}
        </MetricCard>
        <MetricCard title="IOC mais recorrentes">
          {data.top_iocs.length === 0 ? <Muted /> : data.top_iocs.map((i) => (
            <div key={i.value} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", fontSize: typography.size.sm }}>
              <span style={{ fontFamily: typography.family.mono, color: colors.textSecondary }}>{i.value}</span>
              <span style={{ color: colors.textPrimary, fontWeight: 600 }}>{i.count}</span>
            </div>
          ))}
        </MetricCard>
      </div>
    </div>
  );
}

function Mini({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div style={{ padding: spacing["4"], background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: radii.lg }}>
      <div style={{ fontSize: typography.size.xs, color: colors.textMuted, textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</div>
      <div style={{ fontSize: typography.size.display, fontWeight: 700, color: colors.textPrimary, fontVariantNumeric: "tabular-nums" }}>{value}</div>
      <div style={{ fontSize: typography.size.xs, color: colors.textMuted }}>{sub}</div>
    </div>
  );
}

function Muted() {
  return <div style={{ color: colors.textMuted, fontSize: typography.size.sm }}>Sem dados no período.</div>;
}