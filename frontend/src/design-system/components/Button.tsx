/**
 * Button — componente base (UI 3.1)
 * Variantes: primary, secondary, ghost, danger. Densidade compacta.
 */
import { CSSProperties, ReactNode } from "react";
import { colors, motion, radii, spacing, typography } from "../tokens";

type Variant = "primary" | "secondary" | "ghost" | "danger";

export interface ButtonProps {
  children: ReactNode;
  variant?: Variant;
  disabled?: boolean;
  onClick?: () => void;
  style?: CSSProperties;
  title?: string;
}

const variants: Record<Variant, CSSProperties> = {
  primary: {
    background: colors.accent,
    color: colors.textOnAccent,
    boxShadow: "0 1px 0 color-mix(in srgb, var(--color-accent-hover) 45%, transparent), 0 4px 12px color-mix(in srgb, var(--color-accent) 18%, transparent)",
  },
  secondary: {
    background: colors.surfaceAlt,
    color: colors.textPrimary,
    border: `1px solid ${colors.border}`,
  },
  ghost: {
    background: "transparent",
    color: colors.textSecondary,
  },
  danger: {
    background: colors.danger,
    color: "#fff",
  },
};

export function Button({ children, variant = "primary", disabled, onClick, style, title }: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      onMouseEnter={(event) => { if (!disabled) { event.currentTarget.style.transform = "translateY(-1px)"; event.currentTarget.style.filter = "brightness(1.06)"; } }}
      onMouseLeave={(event) => { event.currentTarget.style.transform = "none"; event.currentTarget.style.filter = "none"; }}
      onFocus={(event) => { event.currentTarget.style.boxShadow = `0 0 0 3px color-mix(in srgb, ${colors.focusRing} 30%, transparent)`; }}
      onBlur={(event) => { event.currentTarget.style.boxShadow = variants[variant].boxShadow as string || "none"; }}
      style={{
        fontFamily: typography.family.ui,
        fontSize: typography.size.sm,
        fontWeight: typography.weight.medium,
        padding: `${spacing["2"]} ${spacing["4"]}`,
        borderRadius: radii.md,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
        transition: `background ${motion.transition.fast}, border-color ${motion.transition.fast}, color ${motion.transition.fast}, box-shadow ${motion.transition.fast}, transform ${motion.transition.fast}`,
        border: "none",
        ...variants[variant],
        ...style,
      }}
    >
      {children}
    </button>
  );
}
