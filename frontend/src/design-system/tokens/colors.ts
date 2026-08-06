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

  // Texto (contraste elevado p/ dark theme — WCAG AA)
  textPrimary: "#F0F6FC",
  textSecondary: "#B8C2CC",
  textMuted: "#9EA9B4",
  textOnAccent: "#0F1218",

  // Realce de destaque (dados técnicos / primary)
  textSubtle: "#7A8590",

  // Foco / interação
  focusRing: "#58A6FF",

  // Chips de delta (positivo/negativo/neutro)
  chipPositive: "rgba(63, 185, 80, 0.14)",
  chipPositiveBorder: "rgba(63, 185, 80, 0.35)",
  chipNegative: "rgba(248, 81, 73, 0.14)",
  chipNegativeBorder: "rgba(248, 81, 73, 0.35)",
  chipNeutral: "rgba(139, 148, 158, 0.16)",
  chipNeutralBorder: "rgba(139, 148, 158, 0.35)",

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

/** Gradientes discretos reutilizáveis (polish 5.1). */
export const gradients = {
  card: "linear-gradient(165deg, rgba(47,129,247,0.08) 0%, rgba(22,27,34,0) 48%)",
  topAccent: "linear-gradient(90deg, transparent 0%, rgba(47,129,247,0.55) 50%, transparent 100%)",
  map: "radial-gradient(circle at 50% 40%, #101b2b 0%, #0b1118 60%, #070b10 100%)",
} as const;

/** Glows sutis por semântica (polish 5.1). */
export const glows = {
  accent: "0 0 20px rgba(47,129,247,0.18)",
  online: "0 0 10px rgba(63,185,80,0.5)",
  warning: "0 0 10px rgba(210,153,34,0.45)",
  critical: "0 0 18px rgba(248,81,73,0.28)",
  high: "0 0 18px rgba(219,110,40,0.28)",
} as const;

export type ColorToken = typeof colors;
export type SeverityColor = keyof typeof colors.severity;
