/**
 * AppState — estado global (UI 3.2)
 * Contexto global de estado da aplicação. Estrutura vazia, sem lógica.
 * Contém apenas a forma (auth stub, density, time range) para futura conexão.
 */
import { createContext, ReactNode, useContext, useState } from "react";
import { density } from "../design-system";

export type DensityMode = "compact" | "comfortable";

interface AppStateValue {
  density: DensityMode;
  setDensity: (d: DensityMode) => void;
  currentUserId: string | null;
  setCurrentUserId: (id: string | null) => void;
}

const AppStateContext = createContext<AppStateValue>({
  density: "compact",
  setDensity: () => {},
  currentUserId: null,
  setCurrentUserId: () => {},
});

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [densityMode, setDensityMode] = useState<DensityMode>("compact");
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);

  return (
    <AppStateContext.Provider
      value={{
        density: densityMode,
        setDensity: setDensityMode,
        currentUserId,
        setCurrentUserId,
      }}
    >
      {children}
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  return useContext(AppStateContext);
}

export { density };
