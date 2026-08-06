/**
 * EDY SIEM — fundamentos de cor.
 *
 * Os componentes consomem variáveis CSS, não valores estáticos. Assim o mesmo
 * componente respeita os temas dark e light sem bifurcar a interface.
 */
export interface ThemePalette {
  background: string; surface: string; surfaceAlt: string; border: string; borderSubtle: string;
  textPrimary: string; textSecondary: string; textMuted: string; textSubtle: string;
  accent: string; accentHover: string; focusRing: string;
  low: string; medium: string; high: string; critical: string;
  online: string; degraded: string; offline: string;
}

export const darkTheme: ThemePalette = {
  background: "#0A0F17",
  surface: "#111925",
  surfaceAlt: "#182231",
  border: "#273548",
  borderSubtle: "#1C2838",
  textPrimary: "#F4F8FC",
  textSecondary: "#B8C5D5",
  textMuted: "#8292A6",
  textSubtle: "#63758A",
  accent: "#3B9CFF",
  accentHover: "#77B9FF",
  focusRing: "#83C2FF",
  low: "#56B4FF",
  medium: "#E6B64A",
  high: "#F08A4B",
  critical: "#F15B68",
  online: "#42C981",
  degraded: "#E6B64A",
  offline: "#F15B68",
};

export const lightTheme: ThemePalette = {
  background: "#F5F8FC",
  surface: "#FFFFFF",
  surfaceAlt: "#EDF3FA",
  border: "#CFDBE8",
  borderSubtle: "#E3EBF4",
  textPrimary: "#142235",
  textSecondary: "#465970",
  textMuted: "#667A92",
  textSubtle: "#8292A6",
  accent: "#176DCA",
  accentHover: "#0E5BAD",
  focusRing: "#176DCA",
  low: "#176DCA",
  medium: "#A76D00",
  high: "#BE5A17",
  critical: "#C43345",
  online: "#168453",
  degraded: "#A76D00",
  offline: "#C43345",
};

/** Tokens consumidos pelos componentes. */
export const colors = {
  background: "var(--color-bg)",
  surface: "var(--color-surface)",
  surfaceAlt: "var(--color-surface-alt)",
  border: "var(--color-border)",
  borderSubtle: "var(--color-border-subtle)",
  textPrimary: "var(--color-text-primary)",
  textSecondary: "var(--color-text-secondary)",
  textMuted: "var(--color-text-muted)",
  textSubtle: "var(--color-text-subtle)",
  textOnAccent: "var(--color-text-on-accent)",
  focusRing: "var(--color-focus-ring)",
  accent: "var(--color-accent)",
  accentHover: "var(--color-accent-hover)",
  accentSubtle: "var(--color-accent-subtle)",
  chipPositive: "var(--chip-positive)",
  chipPositiveBorder: "var(--chip-positive-border)",
  chipNegative: "var(--chip-negative)",
  chipNegativeBorder: "var(--chip-negative-border)",
  chipNeutral: "var(--chip-neutral)",
  chipNeutralBorder: "var(--chip-neutral-border)",
  severity: {
    low: "var(--severity-low)",
    medium: "var(--severity-medium)",
    high: "var(--severity-high)",
    critical: "var(--severity-critical)",
    info: "var(--severity-info)",
  },
  status: {
    online: "var(--status-online)",
    degraded: "var(--status-degraded)",
    offline: "var(--status-offline)",
  },
  success: "var(--status-online)",
  warning: "var(--severity-medium)",
  danger: "var(--severity-critical)",
  info: "var(--severity-info)",
} as const;

export const gradients = {
  card: "linear-gradient(155deg, color-mix(in srgb, var(--color-accent) 10%, transparent) 0%, transparent 52%)",
  topAccent: "linear-gradient(90deg, transparent 0%, color-mix(in srgb, var(--color-accent) 55%, transparent) 50%, transparent 100%)",
  map: "radial-gradient(circle at 50% 40%, var(--color-map-core) 0%, var(--color-map-edge) 65%, var(--color-bg) 100%)",
} as const;

export const glows = {
  accent: "0 0 20px color-mix(in srgb, var(--color-accent) 20%, transparent)",
  online: "0 0 10px color-mix(in srgb, var(--status-online) 50%, transparent)",
  warning: "0 0 10px color-mix(in srgb, var(--severity-medium) 45%, transparent)",
  critical: "0 0 18px color-mix(in srgb, var(--severity-critical) 30%, transparent)",
  high: "0 0 18px color-mix(in srgb, var(--severity-high) 30%, transparent)",
} as const;

export type ColorToken = typeof colors;
export type SeverityColor = keyof typeof colors.severity;
