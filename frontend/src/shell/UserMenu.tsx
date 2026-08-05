/**
 * UserMenu + Notifications (UI 3.3)
 * Menu de perfil e notificações no topbar. Estrutura sem dados reais.
 */
import { useState } from "react";
import { colors, motion, radii, spacing, typography } from "../design-system/tokens";

/* ------------------------------ UserMenu -------------------------------- */

export function UserMenu() {
  const [open, setOpen] = useState(false);

  return (
    <div style={{ position: "relative" }}>
      <button
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        title="Conta"
        style={{
          display: "flex",
          alignItems: "center",
          gap: spacing["2"],
          background: "transparent",
          border: `1px solid ${colors.border}`,
          borderRadius: radii.full,
          padding: `3px 6px 3px 3px`,
          color: colors.textSecondary,
          cursor: "pointer",
          fontSize: typography.size.sm,
          transition: `border-color ${motion.transition.fast}, background ${motion.transition.fast}, box-shadow ${motion.transition.fast}`,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = colors.border;
          e.currentTarget.style.background = colors.surfaceAlt;
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = colors.border;
          e.currentTarget.style.background = "transparent";
        }}
      >
        <span
          style={{
            width: 26,
            height: 26,
            borderRadius: "50%",
            background: `linear-gradient(135deg, ${colors.accent}, ${colors.accentHover})`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: colors.textOnAccent,
            fontSize: typography.size.xs,
            fontWeight: typography.weight.bold,
            flex: "none",
          }}
        >
          A
        </span>
        <span style={{ whiteSpace: "nowrap" }}>analyst@edy</span>
      </button>

      {open && (
        <div
          role="menu"
          style={{
            position: "absolute",
            right: 0,
            top: "calc(100% + 6px)",
            width: 220,
            background: colors.surfaceAlt,
            border: `1px solid ${colors.border}`,
            borderRadius: radii.md,
            boxShadow: "0 12px 32px rgba(0,0,0,0.6)",
            zIndex: 400,
            padding: spacing["1"],
            animation: "luminaMenu 160ms cubic-bezier(0.2,0,0,1) both",
          }}
        >
          <div
            style={{
              padding: `${spacing["2"]} ${spacing["3"]} ${spacing["1"]}`,
              marginBottom: 4,
              borderBottom: `1px solid ${colors.borderSubtle}`,
            }}
          >
            <div style={{ fontWeight: typography.weight.semibold, fontSize: typography.size.sm, color: colors.textPrimary }}>
              Edy Analytics
            </div>
            <div style={{ fontSize: typography.size.xs, color: colors.textMuted }}>analyst@edy</div>
          </div>
          {["Meu Perfil", "Configurações", "Sair"].map((item) => (
            <button
              key={item}
              role="menuitem"
              style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                background: "transparent",
                border: "none",
                padding: `${spacing["2"]} ${spacing["3"]}`,
                borderRadius: radii.sm,
                color: item === "Sair" ? colors.severity.critical : colors.textPrimary,
                fontSize: typography.size.sm,
                cursor: "pointer",
                transition: `background ${motion.transition.fast}`,
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = colors.accentSubtle)}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
              {item}
            </button>
          ))}
        </div>
      )}
      <style>{`@keyframes luminaMenu { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: none; } }`}</style>
    </div>
  );
}

/* --------------------------- Notifications ------------------------------- */

const mockNotifications = [
  { id: "n1", title: "Novo alerta: Brute Force SSH", time: "2m atrás", tone: "critical" as const },
  { id: "n2", title: "Incidente resolvido", time: "15m atrás", tone: "online" as const },
  { id: "n3", title: "Regra atualizada", time: "1h atrás", tone: "neutral" as const },
];

export function Notifications() {
  const [open, setOpen] = useState(false);

  return (
    <div style={{ position: "relative" }}>
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          position: "relative",
          background: "transparent",
          border: "none",
          color: colors.textSecondary,
          cursor: "pointer",
          fontSize: typography.size.lg,
          padding: spacing["2"],
        }}
        title="Notificações"
      >
        🔔
        <span
          style={{
            position: "absolute",
            top: 0,
            right: 0,
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: colors.severity.critical,
          }}
        />
      </button>

      {open && (
        <div
          style={{
            position: "absolute",
            right: 0,
            top: "calc(100% + 4px)",
            width: 340,
            background: colors.surfaceAlt,
            border: `1px solid ${colors.border}`,
            borderRadius: radii.md,
            boxShadow: "0 8px 24px rgba(0,0,0,0.6)",
            zIndex: 400,
          }}
        >
          <div
            style={{
              padding: `${spacing["3"]} ${spacing["4"]}`,
              borderBottom: `1px solid ${colors.border}`,
              fontWeight: typography.weight.semibold,
              fontSize: typography.size.sm,
              color: colors.textPrimary,
            }}
          >
            Notificações
          </div>
          {mockNotifications.map((n) => {
            const toneColor =
              n.tone === "critical"
                ? colors.severity.critical
                : n.tone === "online"
                  ? colors.status.online
                  : colors.textMuted;
            return (
              <button
                key={n.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: spacing["3"],
                  width: "100%",
                  textAlign: "left",
                  padding: `${spacing["2"]} ${spacing["3"]}`,
                  background: "transparent",
                  border: "none",
                  borderBottom: `1px solid ${colors.borderSubtle}`,
                  cursor: "pointer",
                  transition: `background ${motion.transition.fast}`,
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = colors.surfaceAlt)}
                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
              >
                <span
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: toneColor,
                    flex: "none",
                    boxShadow: `0 0 6px ${toneColor}80`,
                  }}
                />
                <span style={{ flex: 1, minWidth: 0, fontSize: typography.size.sm, color: colors.textPrimary }}>
                  {n.title}
                </span>
                <span style={{ fontSize: typography.size.xs, color: colors.textMuted, whiteSpace: "nowrap" }}>{n.time}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
