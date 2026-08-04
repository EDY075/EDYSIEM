/**
 * Global Search (UI 3.3)
 * Barra de busca global com sugestões. Estrutural, sem lógica real.
 */
import { useState } from "react";
import { colors, motion, radii, spacing, typography } from "../design-system";

const suggestions = ["brute-force", "malware", "impossible-travel", "8.8.8.8"];

export function GlobalSearch() {
  const [query, setQuery] = useState("");

  return (
    <div style={{ position: "relative", width: "100%" }}>
      <input
        placeholder="Buscar…  [/]"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        style={{
          width: "100%",
          fontFamily: typography.family.ui,
          fontSize: typography.size.sm,
          background: colors.background,
          color: colors.textPrimary,
          border: `1px solid ${colors.border}`,
          borderRadius: radii.md,
          padding: `${spacing["2"]} ${spacing["3"]}`,
          outline: "none",
          transition: motion.transition.fast,
        }}
      />
      {query && (
        <div
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            left: 0,
            right: 0,
            background: colors.surfaceAlt,
            border: `1px solid ${colors.border}`,
            borderRadius: radii.md,
            boxShadow: "0 8px 24px rgba(0,0,0,0.6)",
            zIndex: 400,
            padding: spacing["1"],
          }}
        >
          {suggestions
            .filter((s) => s.includes(query.toLowerCase()))
            .map((s) => (
              <button
                key={s}
                onClick={() => setQuery(s)}
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  background: "transparent",
                  border: "none",
                  padding: spacing["2"],
                  borderRadius: radii.sm,
                  color: colors.textPrimary,
                  fontSize: typography.size.sm,
                  cursor: "pointer",
                }}
              >
                {s}
              </button>
            ))}
          {suggestions.filter((s) => s.includes(query.toLowerCase())).length === 0 && (
            <div style={{ padding: spacing["2"], color: colors.textMuted, fontSize: typography.size.sm }}>
              Sem resultados
            </div>
          )}
        </div>
      )}
    </div>
  );
}
