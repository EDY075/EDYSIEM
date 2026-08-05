/**
 * Topbar (UI 3.3 / polish 6.0 — Enterprise)
 * Barra superior: Breadcrumb dinâmico por rota + Global Search + Theme Switch + Notificações + User.
 * Polish 6.0: breadcrumb reativo à rota, sombra de elevação sutil,
 * ações com hover/focus ring e hierarquia visual mais limpa.
 */
import { useLocation } from "react-router-dom";
import { colors, spacing } from "../design-system/tokens";
import { Breadcrumb, Crumb } from "./Breadcrumb";
import { GlobalSearch } from "./GlobalSearch";
import { UserMenu, Notifications } from "./UserMenu";
import { ThemeSwitch } from "./ThemeSwitch";

const CRUMB_MAP: Record<string, Crumb[]> = {
  "/": [{ label: "Overview" }],
  "/war-room": [{ label: "Overview", to: "/" }, { label: "War Room" }],
  "/triage": [{ label: "Overview", to: "/" }, { label: "Triage" }],
  "/alerts": [{ label: "Overview", to: "/" }, { label: "Alertas" }],
  "/incidents": [{ label: "Overview", to: "/" }, { label: "Incidentes" }],
  "/investigate": [{ label: "Overview", to: "/" }, { label: "Investigar" }],
  "/cases": [{ label: "Resposta", to: "/" }, { label: "Cases" }],
  "/playbooks": [{ label: "Resposta", to: "/" }, { label: "Playbooks" }],
  "/rules": [{ label: "Gestão", to: "/" }, { label: "Regras" }],
  "/intel": [{ label: "Gestão", to: "/" }, { label: "Intelligence" }],
  "/settings": [{ label: "Gestão", to: "/" }, { label: "Configuração" }],
};

export function Topbar() {
  const { pathname } = useLocation();
  const crumbs = CRUMB_MAP[pathname] ?? [{ label: "Overview" }];

  return (
    <header
      style={{
        height: 56,
        background: colors.surface,
        borderBottom: `1px solid ${colors.border}`,
        boxShadow: "0 1px 0 rgba(0,0,0,0.15)",
        display: "flex",
        alignItems: "center",
        gap: spacing["4"],
        padding: `0 ${spacing["4"]}`,
        position: "sticky",
        top: 0,
        zIndex: 200,
      }}
    >
      <div style={{ flex: "0 0 auto", minWidth: 0 }}>
        <Breadcrumb items={crumbs} />
      </div>

      <div style={{ flex: 1, maxWidth: 460, marginLeft: spacing["2"] }}>
        <GlobalSearch />
      </div>

      <div
        style={{
          flex: "0 0 auto",
          display: "flex",
          alignItems: "center",
          gap: spacing["1"],
          marginLeft: "auto",
          paddingLeft: spacing["3"],
          borderLeft: `1px solid ${colors.borderSubtle}`,
        }}
      >
        <ThemeSwitch />
        <Notifications />
        <div style={{ marginLeft: spacing["1"] }}>
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
