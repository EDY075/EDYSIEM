/**
 * Card, Input e Table — componentes base (UI 3.1)
 */
import { CSSProperties, ReactNode } from "react";
import { colors, density, elevation, motion, radii, spacing, typography } from "../tokens";

/* ------------------------------- Card ----------------------------------- */

export interface CardProps {
  children: ReactNode;
  title?: string;
  style?: CSSProperties;
}

export function Card({ children, title, style }: CardProps) {
  return (
    <section
      className="lumina-card-fade"
      style={{
        position: "relative",
        overflow: "hidden",
        background: `linear-gradient(180deg, ${colors.surface} 0%, color-mix(in srgb, ${colors.surfaceAlt} 28%, ${colors.surface}) 100%)`,
        border: `1px solid ${colors.border}`,
        borderRadius: radii.lg,
        boxShadow: elevation.floating,
        ...style,
      }}
    >
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
            "linear-gradient(90deg, transparent 0%, color-mix(in srgb, var(--color-accent) 50%, transparent) 50%, transparent 100%)",
          opacity: 0.5,
        }}
      />
      {title ? (
        <div style={{ padding: `${spacing["3"]} ${spacing["4"]}`, borderBottom: `1px solid ${colors.borderSubtle}` }}>
          <h3
            style={{
              margin: 0,
              fontSize: typography.size.lg,
              fontWeight: typography.weight.semibold,
              color: colors.textPrimary,
              letterSpacing: "-0.01em",
            }}
          >
            {title}
          </h3>
        </div>
      ) : null}
      <div style={{ padding: spacing["4"] }}>{children}</div>
      <style>
        {`@keyframes luminaCardFade { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: none; } }
          .lumina-card-fade { animation: luminaCardFade 200ms cubic-bezier(0.2, 0, 0, 1) both; }
          @media (prefers-reduced-motion: reduce) { .lumina-card-fade { animation: none !important; } }`}
      </style>
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
      onFocus={(e) => { e.currentTarget.style.borderColor = colors.accent; e.currentTarget.style.boxShadow = elevation.focus; }}
      onBlur={(e) => { e.currentTarget.style.borderColor = colors.border; e.currentTarget.style.boxShadow = "none"; }}
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
