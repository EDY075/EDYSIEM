/**
 * Data Table (UI 3.4)
 * Tabela profissional: colunas configuráveis, ordenação, densidade,
 * seleção, expandable rows, estados vazio/carregando.
 * Wrapper do projeto — páginas usam apenas este componente.
 */
import { CSSProperties, ReactNode } from "react";
import { colors, density, motion, spacing, typography } from "../tokens";
import { EmptyState, LoadingSkeleton } from "./feedback";

export interface DataColumn {
  key: string;
  header: string;
  render?: (row: Record<string, ReactNode>) => ReactNode;
  width?: string;
  sortable?: boolean;
  /** Aplica tipografia técnica (JetBrains Mono) nas células — IPs, hashes, timestamps, métricas. */
  mono?: boolean;
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
    <div style={{ overflowX: "auto", maxHeight: "65vh", overflowY: "auto", borderTop: `1px solid ${colors.borderSubtle}`, ...style }}>
      <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: 0 }}>
        <thead>
          <tr>
            {onToggleRow && <th scope="col" style={{ width: 32, ...headCell }} />}
            {columns.map((c) => (
              <th
                key={c.key}
                scope="col"
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
                  transition: `background ${motion.transition.fast}, box-shadow ${motion.transition.fast}`,
                }}
                onMouseEnter={(e) => {
                  if (!selected) {
                    e.currentTarget.style.background = `color-mix(in srgb, var(--color-accent) 4%, ${colors.surfaceAlt})`;
                    e.currentTarget.style.boxShadow = `inset 2px 0 0 var(--color-accent)`;
                  }
                }}
                onMouseLeave={(e) => {
                  if (!selected) {
                    e.currentTarget.style.background = "transparent";
                    e.currentTarget.style.boxShadow = "none";
                  }
                }}
              >
                {onToggleRow && (
                  <td style={{ ...cell }}>
                    <input
                      type="checkbox"
                      aria-label={`Selecionar linha ${i + 1}`}
                      checked={selected}
                      onChange={() => onToggleRow(key)}
                    />
                  </td>
                )}
                {columns.map((c) => (
                  <td
                    key={c.key}
                    style={{
                      ...cell,
                      fontFamily: c.mono ? typography.family.mono : typography.family.ui,
                      fontVariantNumeric: c.mono ? "tabular-nums" : undefined,
                    }}
                  >
                    {c.render ? c.render(row) : cellValue(row[c.key])}
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

/** Célula vazia discreta (evita o "—" ruidoso repetido). */
function cellValue(value: ReactNode): ReactNode {
  if (value === null || value === undefined || value === "") {
    return <span style={{ color: colors.textSubtle, fontSize: typography.size.xs }}>—</span>;
  }
  return value as ReactNode;
}

const headCell: CSSProperties = {
  textAlign: "left",
  fontSize: "10px",
  fontWeight: typography.weight.semibold,
  color: colors.textSubtle,
  padding: `${spacing["3"]} ${spacing["3"]}`,
  textTransform: "uppercase",
  letterSpacing: "0.075em",
  borderBottom: `1px solid ${colors.border}`,
  whiteSpace: "nowrap",
  position: "sticky",
  top: 0,
  background: `color-mix(in srgb, ${colors.surfaceAlt} 52%, ${colors.surface})`,
  zIndex: 1,
};

const cell: CSSProperties = {
  fontSize: typography.size.sm,
  color: colors.textPrimary,
  padding: spacing["2"],
  verticalAlign: "middle",
};
