/**
 * Toast system (Sprint 2.16 WP7) — feedback visual consistente.
 * Provider global + hook useToast; pilha de notificações top-right com auto-dismiss.
 */
import { createContext, useCallback, useContext, useRef, useState } from "react";
import type { ReactNode } from "react";
import { colors, radii, spacing, typography } from "../design-system/tokens";

type Tone = "success" | "error" | "info";

interface ToastItem {
  id: number;
  tone: Tone;
  message: string;
}

interface ToastApi {
  toast: (message: string, tone?: Tone) => void;
}

const ToastContext = createContext<ToastApi>({ toast: () => {} });

export function useToast(): ToastApi {
  return useContext(ToastContext);
}

const TONE_COLOR: Record<Tone, string> = {
  success: colors.status.online,
  error: colors.severity.critical,
  info: colors.accent,
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const idRef = useRef(0);

  const remove = useCallback((id: number) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    (message: string, tone: Tone = "info") => {
      const id = ++idRef.current;
      setItems((prev) => [...prev, { id, tone, message }]);
      window.setTimeout(() => remove(id), 3600);
    },
    [remove],
  );

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div style={{ position: "fixed", top: 16, right: 16, zIndex: 9999, display: "flex", flexDirection: "column", gap: 8, pointerEvents: "none" }}>
        {items.map((t) => (
          <div
            key={t.id}
            role="status"
            style={{
              pointerEvents: "auto",
              display: "flex",
              alignItems: "center",
              gap: spacing["2"],
              minWidth: 220,
              maxWidth: 340,
              padding: `${spacing["2"]} ${spacing["3"]}`,
              background: colors.surface,
              border: `1px solid ${colors.border}`,
              borderLeft: `3px solid ${TONE_COLOR[t.tone]}`,
              borderRadius: radii.md,
              fontFamily: typography.family.ui,
              fontSize: typography.size.sm,
              color: colors.textPrimary,
              boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
              animation: "toast-in 180ms cubic-bezier(0.2,0,0,1)",
            }}
          >
            <span aria-hidden style={{ flex: "none", color: TONE_COLOR[t.tone] }}>
              {t.tone === "success" ? "✓" : t.tone === "error" ? "⚠" : "ℹ"}
            </span>
            <span style={{ flex: 1 }}>{t.message}</span>
            <button onClick={() => remove(t.id)} style={{ flex: "none", border: "none", background: "transparent", color: colors.textMuted, cursor: "pointer" }} aria-label="Fechar">
              ✕
            </button>
          </div>
        ))}
      </div>
      <style>{`@keyframes toast-in { from { opacity: 0; transform: translateX(12px);} to { opacity: 1; transform: none; } }
@media (prefers-reduced-motion: reduce) { [role="status"] { animation: none !important; } }`}</style>
    </ToastContext.Provider>
  );
}