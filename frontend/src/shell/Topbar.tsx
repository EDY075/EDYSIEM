/**
 * Topbar (UI 3.3)
 * Barra superior: Breadcrumb + Global Search + Theme Switch + UserMenu + Notifications.
 */
import { colors, spacing } from "../design-system/tokens";
import { Breadcrumb } from "./Breadcrumb";
import { GlobalSearch } from "./GlobalSearch";
import { UserMenu } from "./UserMenu";
import { Notifications } from "./UserMenu";
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
      <div style={{ flex: "0 0 auto" }}>
        <Breadcrumb
          items={[
            { label: "Overview", to: "/" },
            { label: "Triage", to: "/triage" },
          ]}
        />
      </div>

      <div style={{ flex: 1, maxWidth: 480, marginLeft: spacing["4"] }}>
        <GlobalSearch />
      </div>

      <div style={{ flex: "0 0 auto" }}>
        <ThemeSwitch />
      </div>

      <div style={{ marginLeft: spacing["3"] }}>
        <Notifications />
      </div>

      <div style={{ marginLeft: spacing["3"] }}>
        <UserMenu />
      </div>
    </header>
  );
}
