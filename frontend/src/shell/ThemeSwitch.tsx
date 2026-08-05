/**
 * ThemeSwitch (UI 3.3)
 * Toggle dark/light mode (persistido no localStorage).
 */
import { useState, useEffect } from "react";
import { colors, motion, radii } from "../design-system/tokens";

export function ThemeSwitch() {
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem("edysiem-theme");
    if (saved === "light") setIsDark(false);
  }, []);

  const toggle = () => {
    const next = !isDark;
    setIsDark(next);
    localStorage.setItem("edysiem-theme", next ? "dark" : "light");
  };

  return (
    <button
      onClick={toggle}
      aria-label={isDark ? "Alternar para modo claro" : "Alternar para modo escuro"}
      style={{
        width: 40,
        height: 24,
        borderRadius: radii.full,
        background: isDark ? colors.accent : colors.textMuted,
        border: `1px solid ${isDark ? colors.accent : colors.border}`,
        cursor: "pointer",
        position: "relative",
        padding: 0,
        transition: `background ${motion.transition.normal}, border-color ${motion.transition.normal}, box-shadow ${motion.transition.fast}`,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = isDark
          ? `0 0 0 3px rgba(47,129,247,0.18)`
          : `0 0 0 3px rgba(139,148,158,0.18)`;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      <span
        style={{
          position: "absolute",
          top: 2,
          left: isDark ? 20 : 2,
          width: 18,
          height: 18,
          borderRadius: "50%",
          background: colors.background,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 11,
          transition: `left ${motion.transition.normal} ${motion.easing.emphasized}`,
        }}
      >
        {isDark ? "🌙" : "☀️"}
      </span>
    </button>
  );
}
