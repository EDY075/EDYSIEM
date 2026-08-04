/**
 * Security Line Chart / Area Chart / Bar Chart (UI 3.5)
 * Wrappers próprios do projeto — Recharts apenas internamente.
 */
import { CSSProperties } from "react";
import {
  LineChart as RLineChart,
  Line,
  AreaChart as RAreaChart,
  Area,
  BarChart as RBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { colors, radii, typography } from "../tokens";

type ChartDataItem = Record<string, number | string>;

const axisStyle = {
  fontSize: 11,
  fontFamily: typography.family.mono,
  fill: colors.textMuted,
};
const gridStyle = { stroke: colors.borderSubtle };

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
      <RLineChart data={data}>
        <CartesianGrid {...gridStyle} strokeDasharray="3 3" />
        <XAxis dataKey={xKey} {...axisStyle} />
        <YAxis {...axisStyle} />
        <Tooltip contentStyle={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: 6, fontFamily: typography.family.mono, fontSize: 12 }} />
        {yKeys.map((key, i) => (
          <Line
            key={key}
            type={smooth ? "monotone" : "linear"}
            dataKey={key}
            stroke={palette[i % palette.length]}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
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
}

export function SecurityAreaChart({ data, xKey, yKeys, height = 240 }: SecurityAreaChartProps) {
  const palette = [colors.accent, colors.severity.critical];
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RAreaChart data={data}>
        <CartesianGrid {...gridStyle} strokeDasharray="3 3" />
        <XAxis dataKey={xKey} {...axisStyle} />
        <YAxis {...axisStyle} />
        <Tooltip contentStyle={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: 6, fontFamily: typography.family.mono, fontSize: 12 }} />
        {yKeys.map((key, i) => (
          <Area key={key} type="monotone" dataKey={key} stroke={palette[i % palette.length]} fill={palette[i % palette.length]} fillOpacity={0.15} strokeWidth={2} dot={false} />
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
      <RBarChart data={data}>
        <CartesianGrid {...gridStyle} strokeDasharray="3 3" />
        <XAxis dataKey={xKey} {...axisStyle} />
        <YAxis {...axisStyle} />
        <Tooltip contentStyle={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: 6, fontFamily: typography.family.mono, fontSize: 12 }} />
        {yKeys.map((key, i) => (
          <Bar key={key} dataKey={key} fill={palette[i % palette.length]} radius={[radii.sm, radii.sm, 0, 0]} />
        ))}
      </RBarChart>
    </ResponsiveContainer>
  );
}