/**
 * Feedback — Toolbar, Empty State e Loading Skeleton (UI 3.4)
 */
import { CSSProperties, ReactNode } from "react";
import { colors, radii, spacing, typography } from "../tokens";

/* ------------------------------ Toolbar --------------------------------- */

export interface ToolbarProps {
  left?: ReactNode;
  right?: ReactNode;
  style?: CSSProperties;
}

export function Toolbar({ left, right, style }: ToolbarProps) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: spacing["3"],
        padding: `${spacing["2"]} ${spacing["3"]}`,
        background: colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: radii.lg,
        marginBottom: spacing["3"],
        ...style,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: spacing["3"] }}>{left}</div>
      <div style={{ display: "flex", alignItems: "center", gap: spacing["3"] }}>{right}</div>
    </div>
  );
}

/* ----------------------------- Empty State ------------------------------ */

export interface EmptyStateProps {
  title?: string;
  text?: string;
  description?: string;
  icon?: string;
  action?: ReactNode;
  compact?: boolean;
}

export function EmptyState({ title, text, description, icon = "◌", action, compact }: EmptyStateProps) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: spacing["2"],
        padding: compact ? spacing["4"] : spacing["6"],
        textAlign: "center",
        color: colors.textMuted,
      }}
    >
      <div
        aria-hidden
        style={{
          width: 44,
          height: 44,
          borderRadius: radii.full,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 20,
          background: colors.surfaceAlt,
          border: `1px solid ${colors.border}`,
          color: colors.textSecondary,
          marginBottom: spacing["1"],
        }}
      >
        {icon}
      </div>
      {(title || text) && (
        <div style={{ fontSize: typography.size.base, fontWeight: typography.weight.semibold, color: colors.textPrimary }}>
          {title || text}
        </div>
      )}
      {description && (
        <div style={{ fontSize: typography.size.sm, color: colors.textMuted, maxWidth: 260, lineHeight: 1.5 }}>
          {description}
        </div>
      )}
      {action && <div style={{ marginTop: spacing["2"] }}>{action}</div>}
    </div>
  );
}

/* --------------------------- Loading Skeleton --------------------------- */

export interface LoadingSkeletonProps {
  rows?: number;
  height?: number;
}

export function LoadingSkeleton({ rows = 4, height = 16 }: LoadingSkeletonProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: spacing["2"] }}>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          style={{
            height,
            borderRadius: radii.sm,
            background: colors.surfaceAlt,
            animation: "skeleton-pulse 1.2s ease-in-out infinite",
          }}
        />
      ))}
      <style>{`@keyframes skeleton-pulse { 0%,100% {opacity:1} 50% {opacity:0.4} }`}</style>
    </div>
  );
}
