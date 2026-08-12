import { useLocation } from "react-router-dom";
import { colors, spacing, typography } from "../design-system/tokens";
import { Breadcrumb, Crumb } from "./Breadcrumb";
import { GlobalSearch } from "./GlobalSearch";
import { Notifications, UserMenu } from "./UserMenu";
import { ThemeSwitch } from "./ThemeSwitch";

const crumbs: Record<string, Crumb[]> = {
  "/": [{ label: "Overview" }],
  "/war-room": [{ label: "Operação", to: "/" }, { label: "War Room" }],
  "/triage": [{ label: "Operação", to: "/" }, { label: "Triage" }],
  "/alerts": [{ label: "Operação", to: "/" }, { label: "Alertas" }],
  "/incidents": [{ label: "Operação", to: "/" }, { label: "Incidentes" }],
  "/investigate": [{ label: "Operação", to: "/" }, { label: "Investigar" }],
  "/cases": [{ label: "Resposta", to: "/" }, { label: "Cases" }],
  "/playbooks": [{ label: "Resposta", to: "/" }, { label: "Playbooks" }],
  "/rules": [{ label: "Detecção", to: "/" }, { label: "Regras" }],
  "/intel": [{ label: "Detecção", to: "/" }, { label: "Intelligence" }],
  "/settings": [{ label: "Administração", to: "/" }, { label: "Configurações" }],
};

export function Topbar() {
  const location = useLocation();
  const currentCrumbs = crumbs[location.pathname] ?? [{ label: "Overview" }];

  return <header className="edy-topbar" style={{ minHeight: 72, display: "flex", alignItems: "center", gap: spacing["4"], padding: `0 ${spacing["5"]}`, position: "sticky", top: 0, zIndex: 200, borderBottom: `1px solid ${colors.border}`, background: `linear-gradient(90deg, ${colors.surface} 0%, color-mix(in srgb, ${colors.surfaceAlt} 45%, ${colors.surface}) 100%)`, boxShadow: "0 8px 24px color-mix(in srgb, var(--color-text-primary) 6%, transparent)" }}>
    <div className="workspace-context" style={{ minWidth: 184, paddingRight: spacing["4"], borderRight: `1px solid ${colors.borderSubtle}` }}>
      <div style={{ color: colors.textMuted, fontSize: 10, fontWeight: typography.weight.semibold, letterSpacing: "0.12em" }}>WORKSPACE</div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 3 }}><span style={{ color: colors.textPrimary, fontSize: typography.size.sm, fontWeight: typography.weight.semibold, letterSpacing: "0.02em" }}>EDY / PRIMARY SOC</span></div>
      <div className="workspace-breadcrumb" style={{ marginTop: 4 }}><Breadcrumb items={currentCrumbs} /></div>
    </div>
    <div className="edy-topbar-search" style={{ flex: 1, maxWidth: 620, minWidth: 220 }}><GlobalSearch /></div>
    <div className="edy-topbar-actions" style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: spacing["2"] }}>
      <span className="header-mode-label" style={{ color: colors.textMuted, paddingRight: spacing["2"], borderRight: `1px solid ${colors.borderSubtle}`, fontFamily: typography.family.mono, fontSize: 10, letterSpacing: "0.07em" }}>SOC · LIVE</span>
      <ThemeSwitch />
      <Notifications />
      <UserMenu />
    </div>
    <style>{`@media (max-width: 980px) { .workspace-context { min-width: 150px !important; padding-right: 12px !important; } .workspace-context > div:nth-child(2) > span:nth-child(1) { font-size: 11px !important; } .header-mode-label { display: none; } } @media (max-width: 900px) { .edy-topbar { min-height: 58px !important; gap: 8px !important; padding: 0 12px !important; } .workspace-context { min-width: 82px !important; border-right: 0 !important; padding-right: 0 !important; } .workspace-context > div:first-child, .workspace-breadcrumb, .edy-topbar-search { display: none !important; } .workspace-context > div:nth-child(2) > span:nth-child(1) { font-size: 10px !important; } .edy-topbar-actions { gap: 5px !important; min-width: 0 !important; } [data-user-label] { display: none !important; } }`}</style>
  </header>;
}
