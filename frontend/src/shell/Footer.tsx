/**
 * Footer discreto (UI 3.3)
 * Barra inferior com informações de sistema. Discreta, sem distração.
 */
import { colors, spacing, typography } from "../design-system/tokens";

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
      <span>EDY SIEM v0.3.0</span>
      <span>Dados operacionais via API local · horários no fuso do workspace</span>
    </footer>
  );
}
