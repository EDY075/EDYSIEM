/**
 * Badges — Status e Severity (UI 3.4)
 * Paleta semântica única em todo o produto.
 */
import { CSSProperties } from "react";
import { colors, radii, spacing, typography } from "../tokens";
import { SeverityColor } from "../tokens/colors";

/* --------------------------- Severity Badge ----------------------------- */

export interface SeverityBadgeProps {
  severity: SeverityColor;
  children?: string;
  style?: CSSProperties;
}

export function SeverityBadge({ severity, children, style }: SeverityBadgeProps) {
  const color = colors.severity[severity];
  return (
    <span
      style={{
        fontFamily: typography.family.ui,
        fontSize: typography.size.xs,
        fontWeight: typography.weight.semibold,
        padding: `${spacing["1"]} ${spacing["2"]}`,
        borderRadius: radii.full,
        color,
        background: `color-mix(in srgb, ${color} 14%, transparent)`,
        border: `1px solid color-mix(in srgb, ${color} 34%, transparent)`,
        textTransform: "uppercase",
        letterSpacing: "0.04em",
        whiteSpace: "nowrap",
        ...style,
      }}
    >
      {children ?? severity}
    </span>
  );
}

/* ---------------------------- Status Badge ------------------------------ */

export type StatusTone = "online" | "degraded" | "offline" | "neutral";

export interface StatusBadgeProps {
  tone?: StatusTone;
  children: string;
  style?: CSSProperties;
}

const statusColor: Record<StatusTone, string> = {
  online: colors.status.online,
  degraded: colors.status.degraded,
  offline: colors.status.offline,
  neutral: colors.textMuted,
};

export function StatusBadge({ tone = "neutral", children, style }: StatusBadgeProps) {
  const color = statusColor[tone];
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: spacing["2"],
        fontFamily: typography.family.ui,
        fontSize: typography.size.xs,
        fontWeight: typography.weight.medium,
        color: colors.textSecondary,
        whiteSpace: "nowrap",
        ...style,
      }}
    >
      <span style={{ width: 7, height: 7, borderRadius: "50%", background: color, display: "inline-block", boxShadow: `0 0 0 3px color-mix(in srgb, ${color} 12%, transparent)` }} />
      {children}
    </span>
  );
}
