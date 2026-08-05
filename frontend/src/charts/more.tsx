/**
 * Security Donut Chart / Timeline Chart / Heatmap (UI 3.5)
 */
 import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { SecurityAreaChart } from "./basic";
import { SecurityTooltip } from "./basic";
 import { colors, typography } from "../design-system/tokens";

type ChartDataItem = Record<string, number | string>;

/* --------------------------- Security Donut ------------------------------ */

const palette = [colors.accent, colors.severity.critical, colors.severity.high, colors.severity.medium, colors.severity.low, "#8B5CF6"];

export interface SecurityDonutChartProps {
  data: ChartDataItem[];
  nameKey: string;
  valueKey: string;
  height?: number;
  innerRadius?: number;
  outerRadius?: number;
}

export function SecurityDonutChart({ data, nameKey, valueKey, height = 200, innerRadius = 50, outerRadius = 80 }: SecurityDonutChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie data={data} dataKey={valueKey} nameKey={nameKey} cx="50%" cy="50%" innerRadius={innerRadius} outerRadius={outerRadius} strokeWidth={0}>
          {data.map((_d, i) => (
            <Cell key={i} fill={palette[i % palette.length]} />
          ))}
        </Pie>
        <Tooltip
          content={
            <SecurityTooltip
              valueFormatter={(v) => String(v)}
              labelFormatter={() => "Severidade"}
            />
          }
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

/* ------------------------- Security Timeline Chart ----------------------- */

export interface SecurityTimelineChartProps {
  data: ChartDataItem[];
  xKey: string;
  yKeys: string[];
  height?: number;
}

export function SecurityTimelineChart({ data, xKey, yKeys, height = 200 }: SecurityTimelineChartProps) {
  return <SecurityAreaChart data={data} xKey={xKey} yKeys={yKeys} height={height} />;
}

/* --------------------------- Security Heatmap ---------------------------- */

export interface HeatmapCell {
  row: string;
  col: string;
  value: number;
}

export interface SecurityHeatmapProps {
  rows: string[];
  cols: string[];
  cells: HeatmapCell[];
}

export function SecurityHeatmap({ rows, cols, cells }: SecurityHeatmapProps) {
  const cellMap: Record<string, number> = {};
  cells.forEach((c) => {
    cellMap[`${c.row}::${c.col}`] = c.value;
  });
  const max = Math.max(...cells.map((c) => c.value), 1);

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: typography.size.xs }}>
        <thead>
          <tr>
            <th />
            {cols.map((c) => (
              <th key={c} style={{ color: colors.textMuted, padding: 4, textAlign: "center" }}>
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r}>
              <td style={{ color: colors.textSecondary, padding: 4, textAlign: "right" }}>
                {r}
              </td>
              {cols.map((c) => {
                const v = cellMap[`${r}::${c}`] ?? 0;
                const intensity = v / max;
                return (
                  <td
                    key={c}
                    style={{
                      background: `rgba(47,129,247,${(intensity * 0.8).toFixed(2)})`,
                      borderRadius: 2,
                      textAlign: "center",
                      padding: 6,
                      color: colors.textPrimary,
                      fontFamily: typography.family.mono,
                      fontSize: typography.size.xs,
                      minWidth: 28,
                    }}
                  >
                    {v}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
