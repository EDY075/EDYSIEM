/**
 * Security Line Chart / Area Chart / Bar Chart (UI 3.5 / sprint 5.1.1)
 * Grid horizontal discreto, eixo X com intervalo (sem labels sobrepostas),
 * tooltip customizado com tipografia técnica e leitura limpa.
 */
import { LineChart as RLineChart, Line, AreaChart as RAreaChart, Area, BarChart as RBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { colors, typography } from "../design-system/tokens";

type ChartDataItem = Record<string, number | string>;

const axisStyle = {
  fontSize: 11,
  fontFamily: typography.family.mono,
  fill: colors.textMuted,
};
const gridStyle = { stroke: colors.border, strokeDasharray: "4 4", strokeOpacity: 0.6, vertical: false };

/** Formata número de forma compacta (12.4K, 3.1M). */
function fmt(n: number): string {
  if (Math.abs(n) >= 1000000) return (n / 1000000).toFixed(1) + "M";
  if (Math.abs(n) >= 1000) return (n / 1000).toFixed(1) + "K";
  return String(Math.round(n));
}

/** Tooltip customizado — fundo sólido, tipografia técnica, dados formatados. */
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
        background: colors.surfaceAlt,
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
        boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
        padding: "8px 12px",
        fontFamily: typography.family.mono,
        fontSize: 12,
        minWidth: 140,
      }}
    >
      {label !== undefined && (
        <div style={{ color: colors.textMuted, fontSize: 11, marginBottom: 6, letterSpacing: "0.02em" }}>
          {labelFormatter ? labelFormatter(label) : label}
        </div>
      )}
      {payload.map((p, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "2px 0" }}>
          <span style={{ width: 8, height: 8, borderRadius: 2, background: p.color || colors.accent, flex: "none" }} />
          <span style={{ color: colors.textSecondary }}>{String(p.name ?? "")}</span>
          <span style={{ marginLeft: "auto", color: colors.textPrimary, fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>
            {valueFormatter ? valueFormatter(p.value as number | string) : p.value}
          </span>
        </div>
      ))}
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
}

export function SecurityLineChart({ data, xKey, yKeys, height = 240, smooth = true }: SecurityLineChartProps) {
  const palette = [colors.accent, colors.severity.critical, colors.severity.high, colors.severity.low];
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RLineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid {...gridStyle} />
        <XAxis dataKey={xKey} {...axisStyle} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={28} tickMargin={8} />
        <YAxis {...axisStyle} tickLine={false} axisLine={false} width={42} tickCount={5} tickFormatter={fmt} />
        <Tooltip content={<SecurityTooltip />} cursor={{ stroke: colors.textMuted, strokeOpacity: 0.4 }} />
        {yKeys.map((key, i) => (
          <Line
            key={key}
            type={smooth ? "monotone" : "linear"}
            dataKey={key}
            stroke={palette[i % palette.length]}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, strokeWidth: 0 }}
          />
        ))}
      </RLineChart>
    </ResponsiveContainer>
  );
}

/* -------------------------- Security Area Chart -------------------------- */

export interface SecurityAreaChartProps {
  data: ChartDataItem[];
  xKey: string;
  yKeys: string[];
  height?: number;
  /** Intervalo entre ticks do eixo X (índice). Ex.: 11 → 6 rótulos em 60 pontos. */
  xInterval?: number;
}

export function SecurityAreaChart({ data, xKey, yKeys, height = 240, xInterval = 11 }: SecurityAreaChartProps) {
  const palette = [colors.accent, colors.severity.critical];
  return (
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
        <Tooltip content={<SecurityTooltip valueFormatter={(v) => fmt(Number(v))} />} cursor={{ stroke: colors.textMuted, strokeOpacity: 0.4 }} />
        {yKeys.map((key, i) => (
          <Area
            key={key}
            type="monotone"
            dataKey={key}
            stroke={palette[i % palette.length]}
            fill={palette[i % palette.length]}
            fillOpacity={0.12}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, strokeWidth: 0 }}
          />
        ))}
      </RAreaChart>
    </ResponsiveContainer>
  );
}

/* --------------------------- Security Bar Chart -------------------------- */

export interface SecurityBarChartProps {
  data: ChartDataItem[];
  xKey: string;
  yKeys: string[];
  height?: number;
}

export function SecurityBarChart({ data, xKey, yKeys, height = 240 }: SecurityBarChartProps) {
  const palette = [colors.accent, colors.severity.high, colors.severity.medium];
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RBarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid {...gridStyle} />
        <XAxis dataKey={xKey} {...axisStyle} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={28} tickMargin={8} />
        <YAxis {...axisStyle} tickLine={false} axisLine={false} width={42} tickCount={5} tickFormatter={fmt} />
        <Tooltip content={<SecurityTooltip valueFormatter={(v) => fmt(Number(v))} />} cursor={{ fill: colors.border, fillOpacity: 0.2 }} />
        {yKeys.map((key, i) => (
          <Bar key={key} dataKey={key} fill={palette[i % palette.length]} radius={[4, 4, 0, 0]} />
        ))}
      </RBarChart>
    </ResponsiveContainer>
  );
}
