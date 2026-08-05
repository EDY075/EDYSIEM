/**
 * Design Tokens — Tipografia, Espaçamento, Radii, Shadows (UI 3.1)
 *
 * Base 4px. Inter (UI) + JetBrains Mono (dados técnicos).
 * Densidade compacta default com opção comfortable.
 */

export { colors } from "./colors";
export type { SeverityColor } from "./colors";
export { motion } from "./motion";

export const typography = {
  family: {
    ui: "'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
    mono: "'JetBrains Mono', 'Roboto Mono', ui-monospace, 'SF Mono', monospace",
  },
  size: {
    xs: "12px",
    sm: "13px",
    base: "14px",
    lg: "16px",
    xl: "18px",
    "2xl": "22px",
    "3xl": "28px",
    display: "30px",
  },
  weight: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.7,
  },
} as const;

export const spacing = {
  "1": "4px",
  "2": "8px",
  "3": "12px",
  "4": "16px",
  "5": "24px",
  "6": "32px",
  "8": "48px",
  "10": "64px",
} as const;

/** Densidade de linha em tabelas/listas. */
export const density = {
  compact: "28px",
  comfortable: "40px",
} as const;

export const radii = {
  sm: "4px",
  md: "6px",
  lg: "8px",
  full: "9999px",
} as const;

export const shadows = {
  sm: "0 1px 2px rgba(0,0,0,0.4)",
  md: "0 4px 12px rgba(0,0,0,0.5)",
  lg: "0 8px 24px rgba(0,0,0,0.6)",
  glow: "0 0 0 1px rgba(47,129,247,0.4), 0 0 12px rgba(47,129,247,0.3)",
} as const;

export const zIndex = {
  sidebar: 100,
  topbar: 200,
  flyout: 300,
  modal: 400,
  toast: 500,
} as const;
