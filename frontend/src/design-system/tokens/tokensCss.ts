import { darkTheme, lightTheme } from "./colors";
import type { ThemePalette } from "./colors";

function themeVariables(theme: ThemePalette) {
  return `
  --color-bg: ${theme.background}; --color-surface: ${theme.surface}; --color-surface-alt: ${theme.surfaceAlt};
  --color-border: ${theme.border}; --color-border-subtle: ${theme.borderSubtle};
  --color-text-primary: ${theme.textPrimary}; --color-text-secondary: ${theme.textSecondary};
  --color-text-muted: ${theme.textMuted}; --color-text-subtle: ${theme.textSubtle}; --color-text-on-accent: #FFFFFF;
  --color-accent: ${theme.accent}; --color-accent-hover: ${theme.accentHover}; --color-focus-ring: ${theme.focusRing};
  --color-accent-subtle: color-mix(in srgb, ${theme.accent} 14%, transparent);
  --severity-low: ${theme.low}; --severity-medium: ${theme.medium}; --severity-high: ${theme.high}; --severity-critical: ${theme.critical}; --severity-info: ${theme.low};
  --status-online: ${theme.online}; --status-degraded: ${theme.degraded}; --status-offline: ${theme.offline};
  --chip-positive: color-mix(in srgb, ${theme.online} 15%, transparent); --chip-positive-border: color-mix(in srgb, ${theme.online} 38%, transparent);
  --chip-negative: color-mix(in srgb, ${theme.critical} 14%, transparent); --chip-negative-border: color-mix(in srgb, ${theme.critical} 38%, transparent);
  --chip-neutral: color-mix(in srgb, ${theme.textMuted} 16%, transparent); --chip-neutral-border: color-mix(in srgb, ${theme.textMuted} 35%, transparent);
  --color-map-core: ${theme.background}; --color-map-edge: ${theme.surfaceAlt};` + `\n  --elevation-floating: 0 8px 22px color-mix(in srgb, ${theme.textPrimary} 8%, transparent); --elevation-overlay: 0 20px 48px color-mix(in srgb, ${theme.textPrimary} 18%, transparent);`;
}

export const tokensCss = `
:root { color-scheme: dark; ${themeVariables(darkTheme)} }
body[data-theme="light"] { color-scheme: light; ${themeVariables(lightTheme)} }
body { margin: 0; background: var(--color-bg); color: var(--color-text-primary); font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
button, input, select, textarea { font: inherit; }
`;
