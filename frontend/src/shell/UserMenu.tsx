/**
 * UserMenu + Notifications (UI 3.3)
 * Menu de perfil e notificações no topbar. Estrutura sem dados reais.
 */
import { useState } from "react";
import { colors, motion, radii, spacing, typography } from "../tokens";

/* ------------------------------ UserMenu -------------------------------- */

export function UserMenu() {
  const [open, setOpen] = useState(false);

  return (
    <div style={{ position: "relative" }}>
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: spacing["2"],
          background: colors.surfaceAlt,
          border: `1px solid ${colors.border}`,
          borderRadius: radii.full,
          padding: `${spacing["1"]} ${spacing["2"]}`,
          color: colors.textSecondary,
          cursor: "pointer",
          fontSize: typography.size.sm,
        }}
      >
        <span
          style={{
            width: 24,
            height: 24,
            borderRadius: "50%",
            background: colors.accent,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: colors.textOnAccent,
            fontSize: typography.size.xs,
            fontWeight: typography.weight.semibold,
          }}
        >
          A
        </span>
        <span>analyst@edy</span>
      </button>

      {open && (
        <div
          style={{
            position: "absolute",
            right: 0,
            top: "calc(100% + 4px)",
            width: 200,
            background: colors.surfaceAlt,
            border: `1px solid ${colors.border}`,
            borderRadius: radii.md,
            boxShadow: "0 8px 24px rgba(0,0,0,0.6)",
            zIndex: 400,
            padding: spacing["1"],
          }}
        >
          {["Meu Perfil", "Configurações", "Sair"].map((item) => (
            <button
              key={item}
              style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                background: "transparent",
                border: "none",
                padding: `${spacing["2"]} ${spacing["3"]}`,
                borderRadius: radii.sm,
                color: colors.textPrimary,
                fontSize: typography.size.sm,
                cursor: "pointer",
              }}
            >
              {item}
            </button>
          ))}
        </div>
      )}
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
          {mockNotifications.map((n) => (
            <div
              key={n.id}
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: `${spacing["3"]} ${spacing["4"]}`,
                borderBottom: `1px solid ${colors.borderSubtle}`,
              }}
            >
              <span style={{ fontSize: typography.size.sm, color: colors.textPrimary }}>{n.title}</span>
              <span style={{ fontSize: typography.size.xs, color: colors.textMuted, whiteSpace: "nowrap" }}>{n.time}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
