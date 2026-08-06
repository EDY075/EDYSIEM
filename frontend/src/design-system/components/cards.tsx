/**
 * Cards — KPI Card e Metric Card (UI 3.4 / polish 5.1)
 * KPIs premium: número + sparkline (SVG inline) + drill + glow + delta com seta.
 * Metric Card enterprise: header separado + micro borda superior + footer strip.
 */
import { CSSProperties, ReactNode } from "react";
import { colors, motion, radii, spacing, typography } from "../tokens";
import { SeverityColor } from "../tokens/colors";

/* ------------------------------------------------------------------ */
/*  Micro-animações auxiliares (inline via <style>, escopo classe)     */
/* ------------------------------------------------------------------ */
const microAnimCss = `
@keyframes luminaFade {
  from { opacity: 0; transform: translateY(5px); }
  to   { opacity: 1; transform: none; }
}
@keyframes luminaPulse {
  0%, 100% { box-shadow: 0 0 4px currentColor; opacity: 0.65; }
  50%      { box-shadow: 0 0 10px currentColor; opacity: 1; }
}
/* Spotlight que segue o cursor (gradiente radial) — Sprint 2.14 / WP2 */
.lumina-card { position: relative; }
.lumina-spotlight {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  background: radial-gradient(280px circle at var(--spot-x, 50%) var(--spot-y, 50%), color-mix(in srgb, var(--color-accent) 7%, transparent), transparent 68%);
  opacity: 0;
  transition: opacity 0.28s ease;
}
.lumina-card:hover .lumina-spotlight, .lumina-card:focus-visible .lumina-spotlight { opacity: 1; }
.lumina-fadein { animation: luminaFade 200ms cubic-bezier(0.2, 0, 0, 1) both; }
.lumina-pulse  { animation: luminaPulse 2s ease-in-out infinite; color: inherit; }
@media (prefers-reduced-motion: reduce) {
  .lumina-fadein, .lumina-pulse, .lumina-spotlight { animation: none !important; opacity: 0 !important; }
}
`;

/** Atualiza as CSS vars de posição do cursor para o spotlight. */
function trackSpotlight(e: React.MouseEvent<HTMLElement>) {
  const r = e.currentTarget.getBoundingClientRect();
  e.currentTarget.style.setProperty("--spot-x", `${e.clientX - r.left}px`);
  e.currentTarget.style.setProperty("--spot-y", `${e.clientY - r.top}px`);
}

/* Deterministic sparkline from a seed string (no lib, no state). */
function hashSeed(str: string): number {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function sparklinePath(
  seed: string,
  dir: "up" | "down" | "flat",
  count = 20,
): { points: string; area: string } {
  let h = hashSeed(`${seed}:${dir}`);
  const raw = Array.from({ length: count }, () => {
    h = (Math.imul(h, 1103515245) + 12345) >>> 0;
    return (h % 1000) / 1000;
  });
  // Morph towards the trend direction so the sparkline "reads" the delta.
  const trended = raw.map((v, i) => {
    const progress = i / (count - 1);
    if (dir === "up") return v * 0.65 + progress * 0.35;
    if (dir === "down") return v * 0.65 + (1 - progress) * 0.35;
    return v;
  });
  const min = Math.min(...trended);
  const max = Math.max(...trended);
  const span = max - min || 1;
  const H = 26;
  const W = 72;
  const step = W / (count - 1);
  const pts = trended.map((v, i) => ({
    x: i * step,
    y: H - ((v - min) / span) * (H - 6) - 3,
  }));

  // Curva suave via Catmull-Rom → Bezier
  let d = `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(i - 1, 0)];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[Math.min(i + 2, pts.length - 1)];
    const cp1x = p1.x + (p2.x - p0.x) / 6;
    const cp1y = p1.y + (p2.y - p0.y) / 6;
    const cp2x = p2.x - (p3.x - p1.x) / 6;
    const cp2y = p2.y - (p3.y - p1.y) / 6;
    d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
  }
  const area = `${d} L ${W} ${H} L 0 ${H} Z`;
  return { points: d, area };
}

/* ------------------------------ KPI Card -------------------------------- */

export interface KpiCardProps {
  label: string;
  value: string;
  icon?: ReactNode; // ícone pequeno opcional (glyph/SVG)
  delta?: string; // ex.: "+12% vs 24h"
  trend?: "up" | "down" | "flat";
  severity?: SeverityColor;
  mono?: boolean; // usa tipografia técnica no valor (métricas técnicas)
  onClick?: () => void;
  style?: CSSProperties;
}

function deltaChipColors(trend: "up" | "down" | "flat") {
  switch (trend) {
    case "up": return { bg: colors.chipPositive, border: colors.chipPositiveBorder, fg: colors.success };
    case "down": return { bg: colors.chipNegative, border: colors.chipNegativeBorder, fg: colors.danger };
    default: return { bg: colors.chipNeutral, border: colors.chipNeutralBorder, fg: colors.textMuted };
  }
}


function AutoKpiGlyph({ label }: { label: string }) {
  const key = label.toLocaleLowerCase();
  const stroke = { fill: "none", stroke: "currentColor", strokeWidth: 1.65, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  const shape = key.includes("alert") || key.includes("crít") ? <><path d="M18 9a6 6 0 0 0-12 0c0 7-3 8-3 8h18s-3-1-3-8" /><path d="M10 21h4" /></>
    : key.includes("cas") ? <><rect x="3" y="5" width="18" height="15" rx="2" /><path d="M8 5V3h8v2M8 11h8" /></>
    : key.includes("mttr") || key.includes("mtta") ? <><circle cx="12" cy="12" r="8" /><path d="M12 8v4l3 2" /></>
    : key.includes("score") || key.includes("risk") ? <><path d="M4 18a8 8 0 0 1 16 0" /><path d="m12 12 4-3" /><path d="M4 18h16" /></>
    : key.includes("saúde") || key.includes("health") ? <><path d="M3 12h4l2-5 4 10 2-5h4" /><circle cx="12" cy="12" r="9" /></>
    : <><path d="M3 15h3l2-7 4 11 3-7h6" /></>;
  return <svg width="15" height="15" viewBox="0 0 24 24" aria-hidden="true" {...stroke}>{shape}</svg>;
}
export function KpiCard({ label, value, icon, delta, trend = "flat", severity, mono, onClick, style }: KpiCardProps) {
  const accent = severity ? colors.severity[severity] : colors.accent;
  const dirArrow = trend === "up" ? "▲" : trend === "down" ? "▼" : "•";
  const sp = sparklinePath(`${label}:${value}`, trend);
  const gradId = `kpi-${label.replace(/\W+/g, "")}`;
  const chip = delta ? deltaChipColors(trend) : null;
  const visualIcon = icon ?? <AutoKpiGlyph label={label} />;

  return (
    <button
      onClick={onClick}
      className="lumina-fadein lumina-card"
      aria-label={delta ? `${label}: ${value} (${delta})` : `${label}: ${value}`}
      onMouseMove={trackSpotlight}
      style={{
        position: "relative",
        overflow: "hidden",
        fontFamily: typography.family.ui,
        background: `linear-gradient(142deg, color-mix(in srgb, ${accent} 10%, ${colors.surface}) 0%, ${colors.surface} 48%, color-mix(in srgb, ${colors.surfaceAlt} 42%, ${colors.surface}) 100%)`,
        border: `1px solid ${colors.border}`,
        borderRadius: radii.lg,
        padding: `${spacing["3"]} ${spacing["4"]} ${spacing["4"]}`,
        textAlign: "left",
        cursor: onClick ? "pointer" : "default",
        transition: `transform ${motion.transition.fast}, border-color ${motion.transition.fast}, box-shadow ${motion.transition.fast}, background ${motion.transition.fast}`,
        minWidth: 160,
        minHeight: 126,
        ...style,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-1px)";
        e.currentTarget.style.borderColor = `color-mix(in srgb, ${accent} 36%, transparent)`;
        e.currentTarget.style.boxShadow = `0 10px 26px color-mix(in srgb, ${accent} 12%, transparent), 0 0 0 1px color-mix(in srgb, ${accent} 10%, transparent)`;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "none";
        e.currentTarget.style.borderColor = colors.border;
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      <div
        aria-hidden
        className="lumina-spotlight"
      />
      {/* micro borda superior com gradiente */}
      <div
        aria-hidden
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: 3,
          height: "100%",
          background: `linear-gradient(180deg, ${accent}, color-mix(in srgb, ${accent} 0%, transparent) 76%)`,
          opacity: 0.92,
        }}
      />

      {/* Linha: label (esquerda) + ícone (direita) */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: spacing["2"] }}>
        <div
          style={{
            fontSize: typography.size.xs,
            color: colors.textMuted,
            textTransform: "uppercase",
            letterSpacing: "0.07em",
            fontWeight: typography.weight.semibold,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {label}
        </div>
        {visualIcon && (
          <span
            aria-hidden
            style={{ width: 25, height: 25, display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 13, color: accent, background: `color-mix(in srgb, ${accent} 11%, transparent)`, border: `1px solid color-mix(in srgb, ${accent} 24%, transparent)`, borderRadius: radii.md, flex: "none", lineHeight: 1 }}
          >
            {visualIcon}
          </span>
        )}
      </div>

      {/* Linha: valor (esquerda) + sparkline (direita), alinhados ao centro */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: spacing["3"], marginTop: spacing["2"] }}>
        <div
          style={{
            fontSize: mono ? typography.size["3xl"] : typography.size.display,
            fontWeight: typography.weight.bold,
            color: colors.textPrimary,
            letterSpacing: mono ? "-0.02em" : "-0.035em",
            fontVariantNumeric: "tabular-nums",
            fontFamily: mono ? typography.family.mono : typography.family.ui,
            lineHeight: 1.1,
            whiteSpace: "nowrap",
          }}
        >
          {value}
        </div>
        <svg
          width={70}
          height={30}
          viewBox={`0 0 72 26`}
          aria-hidden="true"
          style={{ display: "block", flex: "none", opacity: 0.9, marginTop: 2 }}
        >
          <defs>
            <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={accent} stopOpacity="0.4" />
              <stop offset="100%" stopColor={accent} stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d={sp.area} fill={`url(#${gradId})`} />
          <path
            d={sp.points}
            fill="none"
            stroke={accent}
            strokeWidth={1.75}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>

      {delta && chip && (
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 5,
            marginTop: spacing["3"],
            padding: "3px 0 0",
            borderRadius: 0,
            background: "transparent",
            border: "none",
            fontSize: typography.size.xs,
            fontWeight: typography.weight.semibold,
            color: chip.fg,
          }}
        >
          <span style={{ fontSize: 8, opacity: 0.9 }}>{dirArrow}</span>
          <span style={{ fontVariantNumeric: "tabular-nums", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {delta}
          </span>
        </div>
      )}
    </button>
  );
}

/* ----------------------------- Metric Card ------------------------------ */

export interface MetricCardProps {
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  style?: CSSProperties;
}

export function MetricCard({ title, children, footer, style }: MetricCardProps) {
  return (
    <section
      className="lumina-fadein lumina-card"
      onMouseMove={trackSpotlight}
      style={{
        position: "relative",
        overflow: "hidden",
        background: `linear-gradient(180deg, ${colors.surface} 0%, color-mix(in srgb, ${colors.surfaceAlt} 34%, ${colors.surface}) 100%)`,
        border: `1px solid ${colors.border}`,
        borderRadius: radii.lg,
        display: "flex",
        flexDirection: "column",
        ...style,
      }}
    >
      <div aria-hidden className="lumina-spotlight" />
      {/* micro borda superior com gradiente accent */}
      <div
        aria-hidden
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 1,
          background:
            "linear-gradient(90deg, transparent 0%, color-mix(in srgb, var(--color-accent) 58%, transparent) 50%, transparent 100%)",
          opacity: 0.72,
        }}
      />
      {/* Header separado */}
      <div
        style={{
          padding: `${spacing["3"]} ${spacing["4"]}`,
          borderBottom: `1px solid ${colors.borderSubtle}`,
        }}
      >
        <h3
          style={{
            margin: 0,
            fontSize: typography.size.base,
            fontWeight: typography.weight.semibold,
            color: colors.textPrimary,
            letterSpacing: "-0.015em",
          }}
        >
          {title}
        </h3>
      </div>
      {/* Body */}
      <div style={{ flex: 1, padding: spacing["4"] }}>{children}</div>
      {/* Footer strip enterprise */}
      {footer && (
        <div
          style={{
            padding: `${spacing["2"]} ${spacing["4"]}`,
            borderTop: `1px solid ${colors.borderSubtle}`,
            background: colors.surfaceAlt,
            display: "flex",
            alignItems: "center",
            flexWrap: "wrap",
            gap: spacing["2"],
            fontSize: typography.size.xs,
            color: colors.textMuted,
            borderBottomLeftRadius: radii.lg,
            borderBottomRightRadius: radii.lg,
          }}
        >
          {footer}
        </div>
      )}
    </section>
  );
}

/** Injete uma vez no app para evitar repetir o mesmo CSS dentro de cada card. */
export const cardMotionCss = microAnimCss;
