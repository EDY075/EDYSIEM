/**
 * Security Line Chart / Area Chart / Bar Chart (UI 3.5 / sprint 5.1.1)
 * Grid horizontal discreto, eixo X com intervalo (sem labels sobrepostas),
 * tooltip customizado com tipografia tÃ©cnica e leitura limpa.
 *
 * Sprint 2.14 / WP5: legend interativa (clique alterna sÃ©ries) + estado vazio.
 */
import { useState } from "react";
import { LineChart as RLineChart, Line, AreaChart as RAreaChart, Area, BarChart as RBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { colors as tokens, typography } from "../design-system/tokens";

type ChartDataItem = Record<string, number | string>;

const axisStyle = {
  fontSize: 11,
  fontFamily: typography.family.mono,
  fill: tokens.textMuted,
};
const gridStyle = { stroke: tokens.border, strokeDasharray: "4 4", strokeOpacity: 0.6, vertical: false };

/** Formata nÃºmero de forma compacta (12.4K, 3.1M). */
function fmt(n: number): string {
  if (Math.abs(n) >= 1000000) return (n / 1000000).toFixed(1) + "M";
  if (Math.abs(n) >= 1000) return (n / 1000).toFixed(1) + "K";
  return String(Math.round(n));
}

/* ------------------------------ Legend ----------------------------------- */

interface ChartLegendProps {
  series: { key: string; color: string }[];
  hidden: Set<string>;
  onToggle: (key: string) => void;
}

function ChartLegend({ series, hidden, onToggle }: ChartLegendProps) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 14, flexWrap: "wrap", padding: "4px 8px" }}>
      {series.map((s) => {
        const isHidden = hidden.has(s.key);
        return (
          <button
            key={s.key}
            type="button"
            onClick={() => onToggle(s.key)}
            aria-pressed={!isHidden}
            title={isHidden ? "Exibir sÃ©rie" : "Ocultar sÃ©rie"}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              border: "none",
              background: "transparent",
              cursor: "pointer",
              padding: 0,
              fontFamily: typography.family.ui,
              fontSize: 11,
              color: isHidden ? tokens.textMuted : tokens.textSecondary,
              opacity: isHidden ? 0.55 : 1,
              textDecoration: isHidden ? "line-through" : "none",
              transition: "opacity 140ms ease",
            }}
          >
            <span aria-hidden style={{ width: 9, height: 9, borderRadius: 2, background: s.color, flex: "none" }} />
            {s.key}
          </button>
        );
      })}
    </div>
  );
}

/** Hook que gerencia sÃ©ries ocultas na legend. */
function useSeriesToggle(_yKeys: string[]) {
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const toggle = (key: string) =>
    setHidden((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  return { hidden, toggle };
}

/* ----------------------------- Empty overlay ----------------------------- */

function ChartEmpty({ message }: { message?: string }) {
  return (
    <div
      style={{
        height: "100%",
        minHeight: 120,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        border: `1px dashed ${tokens.border}`,
        borderRadius: 8,
        color: tokens.textMuted,
        fontSize: typography.size.sm,
        fontFamily: typography.family.ui,
      }}
    >
      {message ?? "Sem dados no perÃ­odo"}
    </div>
  );
}

/* -------------------------- Security Line Chart -------------------------- */

export interface SecurityLineChartProps {
  data: ChartDataItem[];
  xKey: string;
  yKeys: string[];
  height?: number;
  colors?: string[];
  smooth?: boolean;
  legend?: boolean;
  emptyMessage?: string;
}

export function SecurityLineChart({ data, xKey, yKeys, height = 240, smooth = true, legend = yKeys.length > 1, colors, emptyMessage }: SecurityLineChartProps) {
  const palette = [tokens.accent, tokens.severity.critical, tokens.severity.high, tokens.severity.low];
  const { hidden, toggle } = useSeriesToggle(yKeys);
  const series = yKeys.map((key, i) => ({ key, color: (colors && colors[i]) || palette[i % palette.length] }));
  if (data.length === 0) return <ChartEmpty message={emptyMessage} />;
  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      {legend && <ChartLegend series={series} hidden={hidden} onToggle={toggle} />}
      <ResponsiveContainer width="100%" height={height}>
        <RLineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid {...gridStyle} />
          <XAxis dataKey={xKey} {...axisStyle} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={28} tickMargin={8} />
          <YAxis {...axisStyle} tickLine={false} axisLine={false} width={42} tickCount={5} tickFormatter={fmt} />
          <Tooltip content={<SecurityTooltip />} cursor={{ stroke: tokens.textMuted, strokeOpacity: 0.4 }} />
          {series.map((s) => (
            <Line
              key={s.key}
              type={smooth ? "monotone" : "linear"}
              dataKey={s.key}
              stroke={s.color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0 }}
              hide={hidden.has(s.key)}
            />
          ))}
        </RLineChart>
      </ResponsiveContainer>
    </div>
  );
}

/* -------------------------- Security Area Chart -------------------------- */

export interface SecurityAreaChartProps {
  data: ChartDataItem[];
  xKey: string;
  yKeys: string[];
  height?: number;
  /** Intervalo entre ticks do eixo X (Ã­ndice). Ex.: 11 â†’ 6 rÃ³tulos em 60 pontos. */
  xInterval?: number;
  legend?: boolean;
  emptyMessage?: string;
}

export function SecurityAreaChart({ data, xKey, yKeys, height = 240, xInterval = 11, legend = yKeys.length > 1, emptyMessage }: SecurityAreaChartProps) {
  const palette = [tokens.accent, tokens.severity.critical];
  const { hidden, toggle } = useSeriesToggle(yKeys);
  const series = yKeys.map((key, i) => ({ key, color: palette[i % palette.length] }));
  if (data.length === 0) return <ChartEmpty message={emptyMessage} />;
  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      {legend && <ChartLegend series={series} hidden={hidden} onToggle={toggle} />}
      <ResponsiveContainer width="100%" height={height}>
        <RAreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid {...gridStyle} />
          <XAxis
            dataKey={xKey}
            {...axisStyle}
            tickLine={false}
            axisLine={false}
            interval={xInterval}
            tickMargin={8}
          />
          <YAxis {...axisStyle} tickLine={false} axisLine={false} width={42} tickCount={4} tickFormatter={fmt} />
          <Tooltip content={<SecurityTooltip valueFormatter={(v) => fmt(Number(v))} />} cursor={{ stroke: tokens.textMuted, strokeOpacity: 0.4 }} />
          {series.map((s) => (
            <Area
              key={s.key}
              type="monotone"
              dataKey={s.key}
              stroke={s.color}
              fill={s.color}
              fillOpacity={0.12}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0 }}
              hide={hidden.has(s.key)}
            />
          ))}
        </RAreaChart>
      </ResponsiveContainer>
    </div>
  );
}

/* --------------------------- Security Bar Chart -------------------------- */

export interface SecurityBarChartProps {
  data: ChartDataItem[];
  xKey: string;
  yKeys: string[];
  height?: number;
  legend?: boolean;
  emptyMessage?: string;
}

export function SecurityBarChart({ data, xKey, yKeys, height = 240, legend = yKeys.length > 1, emptyMessage }: SecurityBarChartProps) {
  const palette = [tokens.accent, tokens.severity.high, tokens.severity.medium];
  const { hidden, toggle } = useSeriesToggle(yKeys);
  const series = yKeys.map((key, i) => ({ key, color: palette[i % palette.length] }));
  if (data.length === 0) return <ChartEmpty message={emptyMessage} />;
  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      {legend && <ChartLegend series={series} hidden={hidden} onToggle={toggle} />}
      <ResponsiveContainer width="100%" height={height}>
        <RBarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid {...gridStyle} />
          <XAxis dataKey={xKey} {...axisStyle} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={28} tickMargin={8} />
          <YAxis {...axisStyle} tickLine={false} axisLine={false} width={42} tickCount={5} tickFormatter={fmt} />
          <Tooltip content={<SecurityTooltip valueFormatter={(v) => fmt(Number(v))} />} cursor={{ fill: tokens.border, fillOpacity: 0.2 }} />
          {series.map((s) => (
            <Bar key={s.key} dataKey={s.key} fill={s.color} radius={[4, 4, 0, 0]} hide={hidden.has(s.key)} />
          ))}
        </RBarChart>
      </ResponsiveContainer>
    </div>
  );
}

/* --------------------------- Security Tooltip ---------------------------- */

interface TooltipPayloadItem {
  dataKey?: string | number;
  name?: string | number;
  value?: number | string;
  color?: string;
  payload?: ChartDataItem;
}

interface SecurityTooltipProps {
  active?: boolean;
  label?: string | number;
  payload?: TooltipPayloadItem[];
  labelFormatter?: (label: string | number) => string;
  valueFormatter?: (value: number | string) => string;
}

export function SecurityTooltip({ active, label, payload, labelFormatter, valueFormatter }: SecurityTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div
      style={{
        background: tokens.surfaceAlt,
        border: `1px solid ${tokens.border}`,
        borderRadius: 8,
        boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
        padding: "8px 12px",
        fontFamily: typography.family.mono,
        fontSize: 12,
        minWidth: 140,
      }}
    >
      {label !== undefined && (
        <div style={{ color: tokens.textMuted, fontSize: 11, marginBottom: 6, letterSpacing: "0.02em" }}>
          {labelFormatter ? labelFormatter(label) : label}
        </div>
      )}
      {payload.map((p, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "2px 0" }}>
          <span style={{ width: 8, height: 8, borderRadius: 2, background: p.color || tokens.accent, flex: "none" }} />
          <span style={{ color: tokens.textSecondary }}>{String(p.name ?? "")}</span>
          <span style={{ marginLeft: "auto", color: tokens.textPrimary, fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>
            {valueFormatter ? valueFormatter(p.value as number | string) : p.value}
          </span>
        </div>
      ))}
    </div>
  );
}
