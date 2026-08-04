/**
 * App (UI 3.2)
 * Provedores raiz: Theme + AppState + Router.
 */
import { RouterProvider } from "react-router-dom";
import { AppStateProvider } from "./state/AppState";
import { ThemeProvider } from "./theme/ThemeProvider";
import { router } from "./routing/routes";
import { colors } from "./design-system";

export default function App() {
  return (
    <ThemeProvider>
      <AppStateProvider>
        <div style={{ background: colors.background, minHeight: "100vh" }}>
          <RouterProvider router={router} />
        </div>
      </AppStateProvider>
    </ThemeProvider>
  );
}
