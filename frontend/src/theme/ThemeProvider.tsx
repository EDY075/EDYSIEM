/**
 * ThemeProvider (UI 3.2)
 * Injeta os tokens CSS e fornece o tema dark default + opção light.
 * Sem lógica de negócio — apenas infraestrutura de tema.
 */
import { createContext, ReactNode, useContext, useEffect, useState } from "react";
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
  const [mode, setMode] = useState<ThemeMode>("dark");

  useEffect(() => {
    const style = document.createElement("style");
    style.textContent = tokensCss;
    document.head.appendChild(style);
    document.body.dataset.theme = mode;
    return () => {
      document.head.removeChild(style);
    };
  }, [mode]);

  const toggle = () => setMode((m) => (m === "dark" ? "light" : "dark"));

  return <ThemeContext.Provider value={{ mode, toggle }}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  return useContext(ThemeContext);
}

/** Aplicar fundo global do tema. */
export const globalBackground = { background: colors.background, minHeight: "100vh" };
