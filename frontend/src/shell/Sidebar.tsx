/**
 * Sidebar (UI 3.2)
 * Navegação por workflow (benchmark): Overview → Triage → Investigate → Respond → Manage.
 * Colapsável (56px / 240px), ícone + label, sem lógica.
 */
import { useState } from "react";
import { NavLink } from "react-router-dom";
import { colors, motion, spacing, typography } from "../design-system";

const sections = [
  {
    label: "Operação",
    items: [
      { to: "/", label: "Overview", icon: "◧" },
      { to: "/triage", label: "Triage", icon: "◉" },
      { to: "/alerts", label: "Alertas", icon: "⚠" },
      { to: "/incidents", label: "Incidentes", icon: "▣" },
      { to: "/investigate", label: "Investigar", icon: "◈" },
    ],
  },
  {
    label: "Resposta",
    items: [
      { to: "/cases", label: "Cases", icon: "▤" },
      { to: "/playbooks", label: "Playbooks", icon: "▶" },
    ],
  },
  {
    label: "Gestão",
    items: [
      { to: "/rules", label: "Regras", icon: "⚙" },
      { to: "/intel", label: "Intelligence", icon: "◎" },
      { to: "/settings", label: "Config", icon: "☰" },
    ],
  },
];

const COLLAPSED = 56;
const EXPANDED = 240;

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      style={{
        width: collapsed ? COLLAPSED : EXPANDED,
        background: colors.surface,
        borderRight: `1px solid ${colors.border}`,
        transition: motion.transition.normal,
        overflow: "hidden",
        height: "100vh",
        position: "sticky",
        top: 0,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          padding: spacing["3"],
          borderBottom: `1px solid ${colors.border}`,
          color: colors.textPrimary,
          fontWeight: typography.weight.bold,
          whiteSpace: "nowrap",
        }}
      >
        {collapsed ? "ES" : "EDY SIEM"}
      </div>

      <nav style={{ flex: 1, padding: spacing["2"], overflowY: "auto" }}>
        {sections.map((section) => (
          <div key={section.label} style={{ marginBottom: spacing["4"] }}>
            {!collapsed && (
              <div
                style={{
                  fontSize: typography.size.xs,
                  color: colors.textMuted,
                  textTransform: "uppercase",
                  padding: `${spacing["1"]} ${spacing["2"]}`,
                }}
              >
                {section.label}
              </div>
            )}
            {section.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                title={item.label}
                style={({ isActive }) => ({
                  display: "flex",
                  alignItems: "center",
                  gap: spacing["3"],
                  padding: spacing["2"],
                  marginBottom: spacing["1"],
                  borderRadius: "6px",
                  textDecoration: "none",
                  fontSize: typography.size.sm,
                  color: isActive ? colors.accentHover : colors.textSecondary,
                  background: isActive ? colors.accentSubtle : "transparent",
                  whiteSpace: "nowrap",
                })}
              >
                <span style={{ width: 20, textAlign: "center" }}>{item.icon}</span>
                {!collapsed && item.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <button
        onClick={() => setCollapsed((c) => !c)}
        style={{
          padding: spacing["3"],
          background: "transparent",
          border: "none",
          borderTop: `1px solid ${colors.border}`,
          color: colors.textMuted,
          cursor: "pointer",
        }}
      >
        {collapsed ? "»" : "« Colapsar"}
      </button>
    </aside>
  );
}
