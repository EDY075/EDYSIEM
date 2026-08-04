/**
 * Breadcrumb (UI 3.3)
 * Rastreia a navegação. Estrutural, sem lógica real.
 */
import { Link } from "react-router-dom";
import { colors, spacing, typography } from "../design-system";

export interface Crumb {
  label: string;
  to?: string;
}

export function Breadcrumb({ items }: { items: Crumb[] }) {
  return (
    <nav
      aria-label="Breadcrumb"
      style={{ display: "flex", alignItems: "center", gap: spacing["1"], fontSize: typography.size.sm }}
    >
      {items.map((c, i) => {
        const last = i === items.length - 1;
        return (
          <span key={c.label} style={{ display: "flex", alignItems: "center", gap: spacing["1"] }}>
            {c.to && !last ? (
              <Link to={c.to} style={{ color: colors.textSecondary, textDecoration: "none" }}>
                {c.label}
              </Link>
            ) : (
              <span style={{ color: last ? colors.textPrimary : colors.textSecondary }}>{c.label}</span>
            )}
            {!last && <span style={{ color: colors.textMuted }}>/</span>}
          </span>
        );
      })}
    </nav>
  );
}
