/**
 * Footer discreto (UI 3.3)
 * Barra inferior com informações de sistema. Discreta, sem distração.
 */
import { colors, spacing, typography } from "../tokens";

export function Footer() {
  return (
    <footer
      style={{
        borderTop: `1px solid ${colors.borderSubtle}`,
        padding: `${spacing["1"]} ${spacing["4"]}`,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        fontSize: typography.size.xs,
        color: colors.textMuted,
        fontFamily: typography.family.mono,
      }}
    >
      <span>EDY SIEM v0.1.0</span>
      <span>Uptime: 99.97% · EPS: 1.2k · Storage: 42%</span>
    </footer>
  );
}
