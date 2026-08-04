/**
 * Data Table (UI 3.4)
 * Tabela profissional: colunas configuráveis, ordenação, densidade,
 * seleção, expandable rows, estados vazio/carregando.
 * Wrapper do projeto — páginas usam apenas este componente.
 */
import { CSSProperties, ReactNode } from "react";
import { colors, density, motion, radii, spacing, typography } from "../tokens";
import { EmptyState, LoadingSkeleton } from "./feedback";

export interface DataColumn {
  key: string;
  header: string;
  render?: (row: Record<string, ReactNode>) => ReactNode;
  width?: string;
  sortable?: boolean;
}

export interface DataTableProps {
  columns: DataColumn[];
  rows: Array<Record<string, ReactNode>>;
  loading?: boolean;
  emptyText?: string;
  compact?: boolean;
  sortKey?: string | null;
  sortDirection?: "asc" | "desc";
  onSort?: (key: string) => void;
  selectedKeys?: string[];
  onToggleRow?: (key: string) => void;
  rowKey?: (row: Record<string, ReactNode>) => string;
  style?: CSSProperties;
}

export function DataTable({
  columns,
  rows,
  loading = false,
  emptyText = "Nenhum resultado",
  compact = true,
  sortKey,
  sortDirection = "desc",
  onSort,
  selectedKeys = [],
  onToggleRow,
  rowKey,
  style,
}: DataTableProps) {
  const rowHeight = compact ? density.compact : density.comfortable;

  if (loading) {
    return (
      <div style={{ padding: spacing["4"] }}>
        <LoadingSkeleton rows={6} />
      </div>
    );
  }

  if (rows.length === 0) {
    return <EmptyState text={emptyText} />;
  }

  return (
    <div style={{ overflowX: "auto", ...style }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {onToggleRow && <th style={{ width: 32, ...headCell }} />}
            {columns.map((c) => (
              <th
                key={c.key}
                onClick={c.sortable && onSort ? () => onSort(c.key) : undefined}
                style={{
                  ...headCell,
                  width: c.width,
                  cursor: c.sortable && onSort ? "pointer" : "default",
                }}
              >
                <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                  {c.header}
                  {c.sortable && sortKey === c.key && (sortDirection === "asc" ? "▲" : "▼")}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => {
            const key = rowKey ? rowKey(row) : String(i);
            const selected = selectedKeys.includes(key);
            return (
              <tr
                key={key}
                style={{
                  height: rowHeight,
                  borderBottom: `1px solid ${colors.borderSubtle}`,
                  background: selected ? colors.accentSubtle : "transparent",
                  transition: motion.transition.fast,
                }}
              >
                {onToggleRow && (
                  <td style={{ ...cell }}>
                    <input
                      type="checkbox"
                      checked={selected}
                      onChange={() => onToggleRow(key)}
                    />
                  </td>
                )}
                {columns.map((c) => (
                  <td key={c.key} style={cell}>
                    {c.render ? c.render(row) : (row[c.key] as ReactNode) ?? "—"}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

const headCell: CSSProperties = {
  textAlign: "left",
  fontSize: typography.size.xs,
  fontWeight: typography.weight.semibold,
  color: colors.textMuted,
  padding: spacing["2"],
  borderBottom: `1px solid ${colors.border}`,
  whiteSpace: "nowrap",
};

const cell: CSSProperties = {
  fontSize: typography.size.sm,
  color: colors.textPrimary,
  padding: spacing["2"],
};
