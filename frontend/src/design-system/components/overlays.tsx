/**
 * Overlays — Drawer e Modal (UI 3.4)
 * Wrappers do projeto (nenhuma lib externa). Estrutura sem lógica de negócio.
 */
import { ReactNode } from "react";
import { colors, motion, radii, spacing, typography } from "../tokens";

/* ------------------------------ Drawer ---------------------------------- */

export interface DrawerProps {
  open: boolean;
  title?: string;
  onClose?: () => void;
  side?: "right" | "left";
  children: ReactNode;
}

export function Drawer({ open, title, onClose, side = "right", children }: DrawerProps) {
  if (!open) return null;
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 300,
        display: "flex",
        justifyContent: side === "right" ? "flex-end" : "flex-start",
      }}
    >
      <div
        onClick={onClose}
        style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.5)" }}
      />
      <aside
        style={{
          position: "relative",
          width: 420,
          maxWidth: "90vw",
          height: "100%",
          background: colors.surface,
          borderLeft: side === "right" ? `1px solid ${colors.border}` : "none",
          borderRight: side === "left" ? `1px solid ${colors.border}` : "none",
          boxShadow: "0 8px 24px rgba(0,0,0,0.6)",
          display: "flex",
          flexDirection: "column",
          animation: `drawer-in ${motion.duration.normal} ${motion.easing.standard}`,
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: spacing["4"],
            borderBottom: `1px solid ${colors.border}`,
          }}
        >
          <span style={{ fontWeight: typography.weight.semibold, color: colors.textPrimary }}>{title}</span>
          {onClose && (
            <button onClick={onClose} style={closeBtn}>✕</button>
          )}
        </div>
        <div style={{ flex: 1, overflowY: "auto", padding: spacing["4"] }}>{children}</div>
      </aside>
      <style>{`@keyframes drawer-in { from { opacity:0; transform: translateX(24px);} to { opacity:1; transform:none;} }`}</style>
    </div>
  );
}

/* ------------------------------- Modal ----------------------------------- */

export interface ModalProps {
  open: boolean;
  title?: string;
  onClose?: () => void;
  children: ReactNode;
  width?: number;
}

export function Modal({ open, title, onClose, children, width = 560 }: ModalProps) {
  if (!open) return null;
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 400,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div onClick={onClose} style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.6)" }} />
      <div
        role="dialog"
        style={{
          position: "relative",
          width,
          maxWidth: "90vw",
          background: colors.surface,
          border: `1px solid ${colors.border}`,
          borderRadius: radii.lg,
          boxShadow: "0 16px 48px rgba(0,0,0,0.7)",
          animation: `modal-in ${motion.duration.fast} ${motion.easing.standard}`,
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: spacing["4"],
            borderBottom: `1px solid ${colors.border}`,
          }}
        >
          <span style={{ fontWeight: typography.weight.semibold, color: colors.textPrimary }}>{title}</span>
          {onClose && <button onClick={onClose} style={closeBtn}>✕</button>}
        </div>
        <div style={{ padding: spacing["4"] }}>{children}</div>
      </div>
      <style>{`@keyframes modal-in { from { opacity:0; transform: scale(0.96);} to { opacity:1; transform:none;} }`}</style>
    </div>
  );
}

const closeBtn = {
  background: "transparent",
  border: "none",
  color: colors.textMuted,
  cursor: "pointer",
  fontSize: typography.size.lg,
  transition: motion.transition.fast,
};
