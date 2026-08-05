/**
 * Sidebar (UI 3.2 / polish 6.0 — Enterprise)
 * Navegação por workflow (benchmark): Overview → Triage → Investigate → Respond → Manage.
 * Colapsável (56px / 240px), item ativo com barra accent + gradiente + glow,
 * hover com translateX(2px), badges com glow, logo com gradiente de texto.
 * Polish 6.0: densidade otimizada, ícone em chip, focus-visible ring,
 * contraste do item ativo elevado e microinterações leves.
 */
import { useState } from "react";
import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { colors, motion, spacing, typography, radii } from "../design-system";

type IconName = "overview" | "warroom" | "triage" | "alerts" | "incidents" | "investigate" | "cases" | "playbooks" | "rules" | "intel" | "settings";

interface NavItem {
  to: string;
  label: string;
  icon: IconName;
  badge?: string;
  tone?: "online" | "critical";
  end?: boolean;
}

interface NavSection {
  label: string;
  items: NavItem[];
}

const sections: NavSection[] = [
  {
    label: "Operação",
    items: [
      { to: "/", label: "Overview", icon: "overview", end: true },
      { to: "/war-room", label: "War Room", icon: "warroom", badge: "LIVE", tone: "online" },
      { to: "/triage", label: "Triage", icon: "triage" },
      { to: "/alerts", label: "Alertas", icon: "alerts", badge: "12", tone: "critical" },
      { to: "/incidents", label: "Incidentes", icon: "incidents", badge: "4", tone: "critical" },
      { to: "/investigate", label: "Investigar", icon: "investigate" },
    ],
  },
  {
    label: "Resposta",
    items: [
      { to: "/cases", label: "Cases", icon: "cases" },
      { to: "/playbooks", label: "Playbooks", icon: "playbooks" },
    ],
  },
  {
    label: "Gestão",
    items: [
      { to: "/rules", label: "Regras", icon: "rules" },
      { to: "/intel", label: "Intelligence", icon: "intel" },
      { to: "/settings", label: "Config", icon: "settings" },
    ],
  },
];

/** Ícones SVG consistentes (feather-style), 16px. */
function NavIcon({ name, size = 16 }: { name: IconName; size?: number }) {
  const stroke = { fill: "none", stroke: "currentColor", strokeWidth: 1.75, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  const paths: Record<IconName, ReactNode> = {
    overview: <><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></>,
    warroom: <><polyline points="13 2 3 14 11 14 10 22 21 10 13 10 14 2" /><line x1="4" y1="20" x2="20" y2="4" /></>,
    triage: <><path d="M3 6h10" /><path d="M3 12h7" /><path d="M3 18h4" /><circle cx="17" cy="6" r="2" /><circle cx="15" cy="18" r="2" /><path d="M19 12h2" /></>,
    alerts: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.7 21a2 2 0 0 1-3.4 0" /></>,
    incidents: <><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></>,
    investigate: <><circle cx="11" cy="11" r="7" /><line x1="21" y1="21" x2="16.65" y2="16.65" /><line x1="8" y1="11" x2="14" y2="11" /></>,
    cases: <><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" /></>,
    playbooks: <><polygon points="6 3 20 12 6 21 6 3" /></>,
    rules: <><line x1="4" y1="21" x2="4" y2="14" /><line x1="4" y1="10" x2="4" y2="3" /><line x1="12" y1="21" x2="12" y2="12" /><line x1="12" y1="8" x2="12" y2="3" /><line x1="20" y1="21" x2="20" y2="16" /><line x1="20" y1="12" x2="20" y2="3" /><line x1="1" y1="14" x2="7" y2="14" /><line x1="9" y1="8" x2="15" y2="8" /><line x1="17" y1="16" x2="23" y2="16" /></>,
    intel: <><circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="6" /><circle cx="12" cy="12" r="2" /></>,
    settings: <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /></>,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" style={{ flex: "none" }} {...stroke}>
      {paths[name]}
    </svg>
  );
}

const COLLAPSED = 56;
const EXPANDED = 240;

const sidebarCss = `
@keyframes luminaPulseSide {
  0%, 100% { box-shadow: 0 0 4px currentColor; opacity: 0.65; }
  50%      { box-shadow: 0 0 10px currentColor; opacity: 1; }
}
.lumina-nav {
  position: relative;
  transition: background 140ms cubic-bezier(0.2, 0, 0, 1), color 140ms cubic-bezier(0.2, 0, 0, 1),
              transform 140ms cubic-bezier(0.2, 0, 0, 1), box-shadow 140ms cubic-bezier(0.2, 0, 0, 1);
}
.lumina-nav:hover {
  transform: translateX(2px);
  background: rgba(47, 129, 247, 0.09) !important;
}
.lumina-nav:hover .lumina-nav-icon {
  color: ${colors.accentHover};
}
.lumina-nav:focus-visible {
  outline: 2px solid ${colors.focusRing};
  outline-offset: -2px;
}
.lumina-pulse-side { animation: luminaPulseSide 2s ease-in-out infinite; }
.lumina-sidebar-btn {
  transition: background 140ms cubic-bezier(0.2, 0, 0, 1), color 140ms cubic-bezier(0.2, 0, 0, 1);
}
.lumina-sidebar-btn:hover {
  background: rgba(47, 129, 247, 0.08);
  color: ${colors.textPrimary};
}
.lumina-scroll::-webkit-scrollbar { width: 6px; height: 6px; }
.lumina-scroll::-webkit-scrollbar-thumb { background: ${colors.border}; border-radius: 3px; }
.lumina-scroll::-webkit-scrollbar-thumb:hover { background: ${colors.textMuted}66; }
.lumina-scroll::-webkit-scrollbar-track { background: transparent; }
@media (prefers-reduced-motion: reduce) {
  .lumina-nav:hover { transform: none; }
  .lumina-pulse-side { animation: none !important; }
}
`;

/** Marca SVG discreta (escudo) para o logo. */
function ShieldMark({ size = 18 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      style={{ flex: "none" }}
    >
      <defs>
        <linearGradient id="side-shield" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={colors.accent} />
          <stop offset="100%" stopColor={colors.accentHover} />
        </linearGradient>
      </defs>
      <path
        d="M12 2.5 20 5.6v5.1c0 4.6-3.2 8.7-8 10.8-4.8-2.1-8-6.2-8-10.8V5.6L12 2.5Z"
        stroke="url(#side-shield)"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path
        d="m8.8 11.6 2.2 2.2 4.2-4.6"
        stroke="url(#side-shield)"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      style={{
        width: collapsed ? COLLAPSED : EXPANDED,
        background: colors.surface,
        borderRight: `1px solid ${colors.border}`,
        transition: `width ${motion.transition.normal}`,
        overflow: "hidden",
        height: "100vh",
        position: "sticky",
        top: 0,
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Logo com gradiente de texto + marca */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: spacing["2"],
          padding: collapsed ? `${spacing["3"]} 0` : spacing["3"],
          paddingLeft: collapsed ? 0 : spacing["3"],
          justifyContent: collapsed ? "center" : "flex-start",
          borderBottom: `1px solid ${colors.border}`,
          color: colors.textPrimary,
          fontWeight: typography.weight.bold,
          whiteSpace: "nowrap",
          letterSpacing: collapsed ? "0.02em" : "0.04em",
          fontSize: collapsed ? 15 : 16,
          position: "relative",
          minHeight: 56,
        }}
      >
        <ShieldMark />
        {!collapsed && (
          <span
            style={{
              backgroundImage: `linear-gradient(92deg, ${colors.accent} 0%, ${colors.accentHover} 100%)`,
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              WebkitTextFillColor: "transparent",
              color: "transparent",
            }}
          >
            EDY SIEM
          </span>
        )}
        <span
          aria-hidden
          style={{
            position: "absolute",
            bottom: -1,
            left: 16,
            right: 16,
            height: 1,
            background:
              "linear-gradient(90deg, transparent, rgba(47,129,247,0.5), transparent)",
            opacity: 0.6,
          }}
        />
      </div>

      <nav
        className="lumina-scroll"
        style={{ flex: 1, padding: collapsed ? spacing["2"] : "6px 8px", overflowY: "auto" }}
      >
        {sections.map((section) => (
          <div key={section.label} style={{ marginBottom: collapsed ? spacing["3"] : 12 }}>
            {!collapsed && (
              <div
                style={{
                  fontSize: typography.size.xs,
                  color: colors.textMuted,
                  textTransform: "uppercase",
                  letterSpacing: "0.1em",
                  padding: `8px ${spacing["2"]} 4px`,
                  fontWeight: typography.weight.semibold,
                }}
              >
                {section.label}
              </div>
            )}
            {section.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                title={item.label}
                className="lumina-nav"
              >
                {({ isActive }) => (
                  <span
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: spacing["3"],
                      padding: collapsed ? `${spacing["2"]} 0` : `7px ${spacing["2"]}`,
                      justifyContent: collapsed ? "center" : "flex-start",
                      width: "100%",
                      borderRadius: radii.md,
                      fontSize: typography.size.sm,
                      fontWeight: isActive ? typography.weight.semibold : typography.weight.regular,
                      color: isActive ? colors.accentHover : colors.textSecondary,
                      background: isActive
                        ? `linear-gradient(90deg, rgba(47,129,247,0.16) 0%, rgba(47,129,247,0.05) 100%)`
                        : "transparent",
                      borderLeft: isActive ? `3px solid ${colors.accent}` : "3px solid transparent",
                      boxShadow: isActive
                        ? `inset 0 0 0 1px rgba(47,129,247,0.18), 0 0 12px rgba(47,129,247,0.08)`
                        : "none",
                      whiteSpace: "nowrap",
                    }}
                  >
                    <span
                      className="lumina-nav-icon"
                      style={{
                        width: 20,
                        flex: "none",
                        display: "inline-flex",
                        justifyContent: "center",
                        color: isActive ? colors.accentHover : colors.textMuted,
                        transition: `color ${motion.transition.fast}`,
                      }}
                    >
                      <NavIcon name={item.icon as IconName} />
                    </span>
                    {!collapsed && (
                      <span
                        style={{
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          fontSize: typography.size.sm,
                          letterSpacing: "0.01em",
                        }}
                      >
                        {item.label}
                      </span>
                    )}
                    {item.badge && !collapsed && (
                      <span
                        className={item.tone === "online" ? "lumina-pulse-side" : undefined}
                        style={{
                          marginLeft: "auto",
                          flex: "none",
                          fontSize: typography.size.xs,
                          fontWeight: typography.weight.semibold,
                          padding: "1px 8px",
                          borderRadius: radii.full,
                          background:
                            item.tone === "online"
                              ? "rgba(63,185,80,0.16)"
                              : "rgba(248,81,73,0.16)",
                          color:
                            item.tone === "online"
                              ? colors.status.online
                              : colors.severity.critical,
                          border:
                            item.tone === "online"
                              ? `1px solid ${colors.status.online}55`
                              : `1px solid ${colors.severity.critical}55`,
                          boxShadow:
                            item.tone === "online"
                              ? "0 0 8px rgba(63,185,80,0.35)"
                              : "0 0 6px rgba(248,81,73,0.2)",
                          fontFamily: typography.family.mono,
                        }}
                      >
                        {item.badge}
                      </span>
                    )}
                  </span>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <button
        onClick={() => setCollapsed((c) => !c)}
        className="lumina-sidebar-btn"
        style={{
          padding: spacing["3"],
          background: "transparent",
          border: "none",
          borderTop: `1px solid ${colors.border}`,
          color: colors.textMuted,
          cursor: "pointer",
          fontSize: typography.size.sm,
          fontWeight: typography.weight.medium,
        }}
      >
        {collapsed ? "»" : "« Colapsar"}
      </button>
      <style>{sidebarCss}</style>
    </aside>
  );
}
