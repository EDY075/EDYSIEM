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
  /** Ação de retry integrada (estado de falha de API). */
  onRetry?: () => void;
  retryLabel?: string;
  compact?: boolean;
}

export function EmptyState({ title, text, description, icon = "◌", action, onRetry, retryLabel = "Tentar novamente", compact }: EmptyStateProps) {
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
      {!action && onRetry && (
        <button
          type="button"
          onClick={onRetry}
          style={{
            marginTop: spacing["3"],
            padding: "7px 16px",
            border: `1px solid ${colors.border}`,
            borderRadius: radii.md,
            background: colors.surfaceAlt,
            color: colors.textPrimary,
            fontFamily: typography.family.ui,
            fontSize: typography.size.sm,
            fontWeight: typography.weight.semibold,
            cursor: "pointer",
            transition: "background 160ms ease, border-color 160ms ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = colors.border;
            e.currentTarget.style.borderColor = colors.textSecondary;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = colors.surfaceAlt;
            e.currentTarget.style.borderColor = colors.border;
          }}
        >
          ↻ {retryLabel}
        </button>
      )}
    </div>
  );
}

/* --------------------------- Loading Skeleton --------------------------- */

export interface LoadingSkeletonProps {
  /** Quantidade de linhas/blocos de esqueleto. */
  rows?: number;
  /** Altura de cada linha (px). */
  height?: number;
  /** Variante: "lines" (linhas de texto) ou "card" (bloco estilo card com barras internas). */
  variant?: "lines" | "card";
  /** Larguras relativas por linha (0–100). Ex.: [92, 78, 84] → alterna se menor que rows. */
  widths?: number[];
}

const skeletonCss = `
@keyframes skeleton-shimmer {
  0%   { background-position: -320px 0; }
  100% { background-position: 320px 0; }
}
.skeleton-line {
  border-radius: 6px;
  background: linear-gradient(90deg, var(--sk-base, #1a2130) 25%, #222b3d 37%, var(--sk-base, #1a2130) 63%);
  background-size: 640px 100%;
  animation: skeleton-shimmer 1.4s linear infinite;
}
.skeleton-card {
  border-radius: 12px;
  border: 1px solid #202938;
  background: #141a26;
  padding: 18px;
}
@media (prefers-reduced-motion: reduce) {
  .skeleton-line { animation: none; }
}
`;

/** CSS do skeleton (exportado para reuso fora do componente). */
export { skeletonCss };

export function LoadingSkeleton({ rows = 4, height = 16, variant = "lines", widths }: LoadingSkeletonProps) {
  if (variant === "card") {
    return (
      <div role="status" aria-label="Carregando" aria-busy="true" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="skeleton-card">
            <div className="skeleton-line" style={{ height: 14, width: "42%" }} />
            <div className="skeleton-line" style={{ height: 26, width: "86%", marginTop: 12 }} />
            <div className="skeleton-line" style={{ height: 12, width: "64%", marginTop: 10 }} />
          </div>
        ))}
        <style>{skeletonCss}</style>
      </div>
    );
  }
  return (
    <div role="status" aria-label="Carregando" aria-busy="true" style={{ display: "flex", flexDirection: "column", gap: spacing["2"] }}>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="skeleton-line"
          style={{
            height,
            width: widths ? `${widths[i % widths.length]}%` : "100%",
          }}
        />
      ))}
      <style>{skeletonCss}</style>
    </div>
  );
}
