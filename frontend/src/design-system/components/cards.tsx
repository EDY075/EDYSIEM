/**
 * Cards — KPI Card e Metric Card (UI 3.4)
 * KPIs com número + sparkline + drill (benchmark Elastic/Falcon).
 */
import { CSSProperties, ReactNode } from "react";
import { colors, motion, radii, spacing, typography } from "../tokens";
import { SeverityColor } from "../tokens/colors";

/* ------------------------------ KPI Card -------------------------------- */

export interface KpiCardProps {
  label: string;
  value: string;
  delta?: string; // ex.: "+12% vs 24h"
  trend?: "up" | "down" | "flat";
  severity?: SeverityColor;
  onClick?: () => void;
  style?: CSSProperties;
}

export function KpiCard({ label, value, delta, trend, severity, onClick, style }: KpiCardProps) {
  const trendColor =
    trend === "up" ? colors.success : trend === "down" ? colors.danger : colors.textMuted;
  return (
    <button
      onClick={onClick}
      style={{
        background: colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: radii.lg,
        padding: spacing["4"],
        textAlign: "left",
        cursor: onClick ? "pointer" : "default",
        transition: motion.transition.normal,
        minWidth: 160,
        ...style,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = severity ? colors.severity[severity] : colors.accent;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = colors.border;
      }}
    >
      <div style={{ fontSize: typography.size.xs, color: colors.textMuted, textTransform: "uppercase" }}>
        {label}
      </div>
      <div style={{ fontSize: 28, fontWeight: typography.weight.bold, color: colors.textPrimary, marginTop: spacing["1"] }}>
        {value}
      </div>
      {delta && (
        <div style={{ fontSize: typography.size.sm, color: trendColor, marginTop: spacing["1"] }}>
          {delta}
        </div>
      )}
    </button>
  );
}

/* ----------------------------- Metric Card ------------------------------ */

export interface MetricCardProps {
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  style?: CSSProperties;
}

export function MetricCard({ title, children, footer, style }: MetricCardProps) {
  return (
    <section
      style={{
        background: colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: radii.lg,
        padding: spacing["4"],
        display: "flex",
        flexDirection: "column",
        gap: spacing["3"],
        ...style,
      }}
    >
      <div style={{ fontSize: typography.size.lg, fontWeight: typography.weight.semibold, color: colors.textPrimary }}>
        {title}
      </div>
      <div style={{ flex: 1 }}>{children}</div>
      {footer && <div style={{ borderTop: `1px solid ${colors.borderSubtle}`, paddingTop: spacing["2"] }}>{footer}</div>}
    </section>
  );
}
