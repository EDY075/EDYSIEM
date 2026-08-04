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
      style={{
        fontFamily: typography.family.ui,
        fontSize: typography.size.sm,
        fontWeight: typography.weight.medium,
        padding: `${spacing["2"]} ${spacing["4"]}`,
        borderRadius: radii.md,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
        transition: motion.transition.normal,
        border: "none",
        ...variants[variant],
        ...style,
      }}
    >
      {children}
    </button>
  );
}
