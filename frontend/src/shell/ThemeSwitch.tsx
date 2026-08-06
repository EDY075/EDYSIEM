/** Visual theme control — compact Echelon console switch. */
import { colors, motion, radii } from "../design-system/tokens";
import { useTheme } from "../theme/ThemeProvider";

function ThemeGlyph({ dark }: { dark: boolean }) {
  return dark ? (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z" /></svg>
  ) : (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" /></svg>
  );
}

export function ThemeSwitch() {
  const { mode, toggle } = useTheme();
  const isDark = mode === "dark";

  return (
    <button
      onClick={toggle}
      aria-label={isDark ? "Alternar para modo claro" : "Alternar para modo escuro"}
      style={{
        width: 38,
        height: 24,
        borderRadius: radii.full,
        background: isDark ? colors.accent : colors.surfaceAlt,
        border: `1px solid ${isDark ? colors.accent : colors.border}`,
        cursor: "pointer",
        position: "relative",
        padding: 0,
        transition: `background ${motion.transition.fast}, border-color ${motion.transition.fast}, box-shadow ${motion.transition.fast}`,
      }}
      onMouseEnter={(e) => { e.currentTarget.style.boxShadow = "0 0 0 3px var(--color-accent-subtle)"; }}
      onMouseLeave={(e) => { e.currentTarget.style.boxShadow = "none"; }}
      onFocus={(e) => { e.currentTarget.style.boxShadow = "0 0 0 3px var(--color-accent-subtle)"; }}
      onBlur={(e) => { e.currentTarget.style.boxShadow = "none"; }}
    >
      <span style={{ position: "absolute", top: 2, left: isDark ? 18 : 2, width: 18, height: 18, borderRadius: "50%", background: colors.background, display: "flex", alignItems: "center", justifyContent: "center", color: isDark ? colors.accent : colors.textMuted, transition: `left ${motion.transition.fast}` }}>
        <ThemeGlyph dark={isDark} />
      </span>
    </button>
  );
}