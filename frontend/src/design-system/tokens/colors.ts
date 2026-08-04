/**
 * Design Tokens — Cores (UI 3.1)
 *
 * Dark theme default (benchmark: Elastic/Falcon). Paleta semântica de
 * severidade única em todo o produto.
 *
 * Low=azul, Medium=âmbar, High=laranja, Critical=vermelho.
 */

export const colors = {
  // Superfícies (dark)
  background: "#0F1218",
  surface: "#161B22",
  surfaceAlt: "#1C2128",
  border: "#262D38",
  borderSubtle: "#1C2128",

  // Texto
  textPrimary: "#E6EDF3",
  textSecondary: "#9DA7B3",
  textMuted: "#6E7681",
  textOnAccent: "#0F1218",

  // Accent (marca — discreto)
  accent: "#2F81F7",
  accentHover: "#58A6FF",
  accentSubtle: "rgba(47, 129, 247, 0.15)",

  // Severidade (semântica — única em todo o produto)
  severity: {
    low: "#58A6FF",
    medium: "#D29922",
    high: "#DB6E28",
    critical: "#F85149",
    info: "#58A6FF",
  },

  // Status operacional
  status: {
    online: "#3FB950",
    degraded: "#D29922",
    offline: "#F85149",
  },

  // Estados
  success: "#3FB950",
  warning: "#D29922",
  danger: "#F85149",
  info: "#58A6FF",
} as const;

export type ColorToken = typeof colors;
export type SeverityColor = keyof typeof colors.severity;
