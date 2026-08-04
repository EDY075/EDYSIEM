/**
 * Design Tokens — CSS Variables
 * Bridge entre tokens TS e CSS para uso em qualquer componente.
 */

import { colors } from "./colors";

export const tokensCss = `:root {
  --color-bg: ${colors.background};
  --color-surface: ${colors.surface};
  --color-surface-alt: ${colors.surfaceAlt};
  --color-border: ${colors.border};
  --color-text-primary: ${colors.textPrimary};
  --color-text-secondary: ${colors.textSecondary};
  --color-text-muted: ${colors.textMuted};
  --color-accent: ${colors.accent};
  --color-accent-hover: ${colors.accentHover};

  --severity-low: ${colors.severity.low};
  --severity-medium: ${colors.severity.medium};
  --severity-high: ${colors.severity.high};
  --severity-critical: ${colors.severity.critical};
  --severity-info: ${colors.severity.info};

  --status-online: ${colors.status.online};
  --status-degraded: ${colors.status.degraded};
  --status-offline: ${colors.status.offline};

  --space-1: 4px; --space-2: 8px; --space-3: 12px;
  --space-4: 16px; --space-5: 24px; --space-6: 32px;
  --space-8: 48px; --space-10: 64px;

  --radius-sm: 4px; --radius-md: 6px; --radius-lg: 8px;

  --shadow-sm: 0 1px 2px rgba(0,0,0,0.4);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.5);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.6);
}`;
