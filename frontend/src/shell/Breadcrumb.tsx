/**
 * Breadcrumb (UI 3.3 / polish 6.0)
 * Rastreia a navegação. Chevron discreto, hover com accent e item atual destacado.
 */
import { Link } from "react-router-dom";
import { colors, motion, spacing, typography } from "../design-system";

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
          <span
            key={c.label}
            style={{ display: "flex", alignItems: "center", gap: spacing["1"] }}
          >
            {c.to && !last ? (
              <Link
                to={c.to}
                style={{
                  color: colors.textSecondary,
                  textDecoration: "none",
                  fontWeight: typography.weight.medium,
                  borderRadius: 4,
                  padding: "2px 4px",
                  transition: `color ${motion.transition.fast}, background ${motion.transition.fast}`,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = colors.accentHover;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = colors.textSecondary;
                }}
              >
                {c.label}
              </Link>
            ) : (
              <span
                style={{
                  color: last ? colors.textPrimary : colors.textSecondary,
                  fontWeight: last ? typography.weight.semibold : typography.weight.regular,
                  whiteSpace: "nowrap",
                }}
              >
                {c.label}
              </span>
            )}
            {!last && (
              <span
                aria-hidden
                style={{
                  color: colors.textMuted,
                  fontSize: 11,
                  padding: "0 2px",
                  opacity: 0.8,
                }}
              >
                /
              </span>
            )}
          </span>
        );
      })}
    </nav>
  );
}
