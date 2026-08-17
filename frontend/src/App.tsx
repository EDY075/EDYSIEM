/**
 * App (UI 3.2 / Sprint 2.14 WP9)
 * Provedores raiz: Theme + AppState + Router. Estilos globais de acessibilidade/scroll.
 */
import { RouterProvider } from "react-router-dom";
import { AppStateProvider } from "./state/AppState";
import { ToastProvider } from "./state/toast";
import { ThemeProvider } from "./theme/ThemeProvider";
import { router } from "./routing/routes";
import { colors } from "./design-system";
import { cardMotionCss } from "./design-system/components/cards";
import { AuthGate } from "./auth/AuthGate";

/** Estilos globais de acessibilidade + scrollbar enterprise (Sprint 2.14 / WP9). */
const globalStyle = `
:root { color-scheme: dark; }
*, *::before, *::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
:focus-visible { outline: 2px solid ${colors.accent} !important; outline-offset: 2px; border-radius: 4px; }
#root { min-height: 100vh; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: ${colors.border}; border-radius: 6px; border: 2px solid transparent; background-clip: content-box; }
::-webkit-scrollbar-thumb:hover { background: ${colors.textSecondary}; background-clip: content-box; }
::-webkit-scrollbar-track { background: transparent; }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; scroll-behavior: auto !important; }
}
`;

export default function App() {
  return (
    <ThemeProvider>
      <AppStateProvider>
        <style>{globalStyle}</style>
        <style>{cardMotionCss}</style>
        <AuthGate>
          <div style={{ background: colors.background, minHeight: "100vh" }}>
            <ToastProvider>
              <RouterProvider router={router} />
            </ToastProvider>
          </div>
        </AuthGate>
      </AppStateProvider>
    </ThemeProvider>
  );
}
