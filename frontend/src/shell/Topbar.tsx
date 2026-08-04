/**
 * Topbar (UI 3.2)
 * Barra superior: global search, time range, contador de alertas, user menu.
 * Sem lógica — apenas estrutura.
 */
import { colors, motion, spacing, typography } from "../design-system";
import { Input } from "../design-system";
import { useTheme } from "../theme/ThemeProvider";

export function Topbar() {
  const { mode, toggle } = useTheme();

  return (
    <header
      style={{
        height: 56,
        background: colors.surface,
        borderBottom: `1px solid ${colors.border}`,
        display: "flex",
        alignItems: "center",
        gap: spacing["4"],
        padding: `0 ${spacing["4"]}`,
        position: "sticky",
        top: 0,
        zIndex: 200,
      }}
    >
      {/* Global search */}
      <div style={{ flex: 1, maxWidth: 480 }}>
        <Input placeholder="Buscar (kql…)  [/]" />
      </div>

      {/* Time range */}
      <span
        style={{
          fontSize: typography.size.sm,
          color: colors.textSecondary,
          border: `1px solid ${colors.border}`,
          padding: `${spacing["2"]} ${spacing["3"]}`,
          borderRadius: 6,
        }}
      >
        24h ▾
      </span>

      {/* Alertas count (stub) */}
      <span
        style={{
          fontSize: typography.size.xs,
          color: colors.severity.critical,
          border: `1px solid ${colors.severity.critical}40`,
          background: `${colors.severity.critical}1f`,
          padding: `${spacing["1"]} ${spacing["2"]}`,
          borderRadius: 999,
          fontWeight: typography.weight.semibold,
        }}
      >
        12
      </span>

      {/* Theme toggle + user */}
      <button
        onClick={toggle}
        style={{
          background: "transparent",
          border: "none",
          color: colors.textSecondary,
          cursor: "pointer",
          transition: motion.transition.fast,
        }}
        title="Alternar tema"
      >
        {mode === "dark" ? "☾" : "☀"}
      </button>

      <span
        style={{
          fontSize: typography.size.sm,
          color: colors.textSecondary,
        }}
      >
        analyst@edy
      </span>
    </header>
  );
}
