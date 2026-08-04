/**
 * ThemeSwitch (UI 3.3)
 * Toggle dark/light mode (persistido no localStorage).
 */
import { useState, useEffect } from "react";
import { colors, radii } from "../design-system/tokens";

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
      style={{
        width: 40,
        height: 24,
        borderRadius: radii.full,
        background: isDark ? colors.accent : colors.textMuted,
        border: "none",
        cursor: "pointer",
        position: "relative",
        padding: 0,
        transition: "background 0.2s",
      }}
      title={isDark ? "Alternar para modo claro" : "Alternar para modo escuro"}
    >
      <span
        style={{
          position: "absolute",
          top: 2,
          left: isDark ? 20 : 2,
          width: 20,
          height: 20,
          borderRadius: "50%",
          background: colors.background,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 12,
        }}
      >
        {isDark ? "🌙" : "☀️"}
      </span>
    </button>
  );
}
