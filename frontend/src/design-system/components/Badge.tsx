/**
 * Badge — componente base (UI 3.1)
 * Badge de severidade com a paleta semântica única do produto.
 */
import { CSSProperties, ReactNode } from "react";
import { colors, radii, spacing, typography } from "../tokens";
import { SeverityColor } from "../tokens/colors";

export interface BadgeProps {
  children: ReactNode;
  severity?: SeverityColor;
  style?: CSSProperties;
}

export function Badge({ children, severity = "medium", style }: BadgeProps) {
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
        background: `${color}1f`, // 12% alpha
        border: `1px solid ${color}40`, // 25% alpha
        textTransform: "uppercase",
        letterSpacing: "0.04em",
        whiteSpace: "nowrap",
        ...style,
      }}
    >
      {children}
    </span>
  );
}
