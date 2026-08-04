/**
 * Card, Input e Table — componentes base (UI 3.1)
 */
import { CSSProperties, ReactNode } from "react";
import { colors, density, motion, radii, spacing, typography } from "../tokens";

/* ------------------------------- Card ----------------------------------- */

export interface CardProps {
  children: ReactNode;
  title?: string;
  style?: CSSProperties;
}

export function Card({ children, title, style }: CardProps) {
  return (
    <section
      style={{
        background: colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: radii.lg,
        padding: spacing["4"],
        ...style,
      }}
    >
      {title ? (
        <h3
          style={{
            margin: 0,
            marginBottom: spacing["3"],
            fontSize: typography.size.lg,
            fontWeight: typography.weight.semibold,
            color: colors.textPrimary,
          }}
        >
          {title}
        </h3>
      ) : null}
      {children}
    </section>
  );
}

/* ------------------------------- Input ---------------------------------- */

export interface InputProps {
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  style?: CSSProperties;
}

export function Input({ placeholder, value, onChange, style }: InputProps) {
  return (
    <input
      placeholder={placeholder}
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
      style={{
        fontFamily: typography.family.ui,
        fontSize: typography.size.sm,
        background: colors.background,
        color: colors.textPrimary,
        border: `1px solid ${colors.border}`,
        borderRadius: radii.md,
        padding: `${spacing["2"]} ${spacing["3"]}`,
        transition: motion.transition.fast,
        outline: "none",
        width: "100%",
        ...style,
      }}
    />
  );
}

/* ------------------------------- Table ---------------------------------- */

export interface TableColumn {
  key: string;
  header: string;
  width?: string;
}

export interface TableProps {
  columns: TableColumn[];
  rows: Array<Record<string, ReactNode>>;
  compact?: boolean;
}

export function Table({ columns, rows, compact = true }: TableProps) {
  const rowHeight = compact ? density.compact : density.comfortable;
  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr>
          {columns.map((c) => (
            <th
              key={c.key}
              style={{
                textAlign: "left",
                fontSize: typography.size.xs,
                fontWeight: typography.weight.semibold,
                color: colors.textMuted,
                padding: spacing["2"],
                borderBottom: `1px solid ${colors.border}`,
                width: c.width,
              }}
            >
              {c.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr
            key={i}
            style={{
              borderBottom: `1px solid ${colors.borderSubtle}`,
              height: rowHeight,
              transition: motion.transition.fast,
            }}
          >
            {columns.map((c) => (
              <td
                key={c.key}
                style={{
                  fontSize: typography.size.sm,
                  color: colors.textPrimary,
                  padding: spacing["2"],
                }}
              >
                {row[c.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export { colors };
