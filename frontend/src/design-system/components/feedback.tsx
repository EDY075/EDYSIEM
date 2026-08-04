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
  text?: string;
  icon?: string;
  action?: ReactNode;
}

export function EmptyState({ text = "Nenhum dado", icon = "◌", action }: EmptyStateProps) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: spacing["3"],
        padding: spacing["8"],
        color: colors.textMuted,
      }}
    >
      <div style={{ fontSize: 32, opacity: 0.6 }}>{icon}</div>
      <div style={{ fontSize: typography.size.base }}>{text}</div>
      {action}
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
