/**
 * Topbar (UI 3.3)
 * Barra superior: Breadcrumb + Global Search + Theme Switch + UserMenu + Notifications.
 * Sem lógica — apenas estrutura.
 */
import { colors, motion, spacing, typography } from "../design-system";
import { Breadcrumb } from "./Breadcrumb";
import { GlobalSearch } from "./GlobalSearch";
import { UserMenu } from "./UserMenu";
import { Notifications } from "./Notifications";
import { ThemeSwitch } from "./ThemeSwitch";

export function Topbar() {
  return (
    <header
      style={{
        height: 56,
        background: colors.surface,
        borderBottom: `1px solid ${colors.border}`,
        display: "flex",
        alignItems: "center",
        gap: spacing["4"],
        padding: `0 ${spacing["4"]}`,
        position: "sticky",
        top: 0,
        zIndex: 200,
      }}
    >
      {/* Breadcrumb */}
      <div style={{ flex: "0 0 auto" }}>
        <Breadcrumb
          items={[
            { label: "Overview", to: "/" },
            { label: "Triage", to: "/triage" },
          ]}
        />
      </div>

      {/* Global Search */}
      <div style={{ flex: 1, maxWidth: 480, marginLeft: spacing["4"] }}>
        <GlobalSearch />
      </div>

      {/* Theme Switch */}
      <div style={{ flex: "0 0 auto" }}>
        <ThemeSwitch />
      </div>

      {/* Notifications */}
      <div style={{ marginLeft: spacing["3"] }}>
        <Notifications />
      </div>

      {/* User Menu */}
      <div style={{ marginLeft: spacing["3"] }}>
        <UserMenu />
      </div>
    </header>
  );
}
