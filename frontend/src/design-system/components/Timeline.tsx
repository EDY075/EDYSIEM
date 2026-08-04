/**
 * Timeline e Activity Feed (UI 3.4)
 * Timeline vertical de eventos + feed de atividade (notas, tarefas, auditoria).
 */
import { colors, spacing, typography } from "../tokens";
import { SeverityColor } from "../tokens/colors";

/* ------------------------------ Timeline -------------------------------- */

export interface TimelineItem {
  id: string;
  title: string;
  detail?: string;
  time: string;
  tone?: SeverityColor | "neutral";
  icon?: string;
}

export interface TimelineProps {
  items: TimelineItem[];
}

export function Timeline({ items }: TimelineProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      {items.map((item, i) => {
        const color =
          item.tone === "neutral" || !item.tone ? colors.textMuted : colors.severity[item.tone];
        return (
          <div key={item.id} style={{ display: "flex", gap: spacing["3"] }}>
            {/* rail */}
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
              <div style={{ width: 10, height: 10, borderRadius: "50%", background: color, border: `2px solid ${colors.surface}` }} />
              {i < items.length - 1 && (
                <div style={{ width: 2, flex: 1, minHeight: 24, background: colors.border }} />
              )}
            </div>
            {/* content */}
            <div style={{ paddingBottom: spacing["4"], flex: 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ fontSize: typography.size.sm, fontWeight: typography.weight.medium, color: colors.textPrimary }}>
                  {item.icon && <span style={{ marginRight: 4 }}>{item.icon}</span>}
                  {item.title}
                </span>
                <span style={{ fontSize: typography.size.xs, color: colors.textMuted, fontFamily: typography.family.mono }}>
                  {item.time}
                </span>
              </div>
              {item.detail && (
                <div style={{ fontSize: typography.size.sm, color: colors.textSecondary }}>{item.detail}</div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ---------------------------- Activity Feed ------------------------------ */

export interface ActivityItem {
  id: string;
  actor: string;
  action: string;
  target?: string;
  time: string;
}

export interface ActivityFeedProps {
  items: ActivityItem[];
}

export function ActivityFeed({ items }: ActivityFeedProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      {items.map((item) => (
        <div
          key={item.id}
          style={{
            display: "flex",
            justifyContent: "space-between",
            gap: spacing["3"],
            padding: `${spacing["2"]} 0`,
            borderBottom: `1px solid ${colors.borderSubtle}`,
          }}
        >
          <div style={{ fontSize: typography.size.sm }}>
            <span style={{ color: colors.textPrimary, fontWeight: typography.weight.medium }}>{item.actor}</span>{" "}
            <span style={{ color: colors.textSecondary }}>{item.action}</span>{" "}
            {item.target && <span style={{ color: colors.textMuted }}>{item.target}</span>}
          </div>
          <span style={{ fontSize: typography.size.xs, color: colors.textMuted, fontFamily: typography.family.mono, whiteSpace: "nowrap" }}>
            {item.time}
          </span>
        </div>
      ))}
    </div>
  );
}
