/**
 * ThemeProvider (UI 3.2)
 * Injeta os tokens CSS e fornece o tema dark default + opção light.
 * Sem lógica de negócio — apenas infraestrutura de tema.
 */
import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";
import { colors, tokensCss } from "../design-system";

export type ThemeMode = "dark" | "light";

interface ThemeContextValue {
  mode: ThemeMode;
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  mode: "dark",
  toggle: () => {},
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>(() => localStorage.getItem("edysiem-theme") === "light" ? "light" : "dark");

  useEffect(() => {
    document.body.dataset.theme = mode;
    localStorage.setItem("edysiem-theme", mode);
  }, [mode]);

  const toggle = () => setMode((m) => (m === "dark" ? "light" : "dark"));

  const value = useMemo(() => ({ mode, toggle }), [mode]);
  return <ThemeContext.Provider value={value}><style>{tokensCss}</style>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  return useContext(ThemeContext);
}

/** Aplicar fundo global do tema. */
export const globalBackground = { background: colors.background, minHeight: "100vh" };
