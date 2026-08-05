/**
 * Routing (UI 3.2 / UI 4.x)
 * Definição de rotas da aplicação conectada às páginas reais.
 */
import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "../shell/AppShell";
import { Page } from "../components/Page";
import { DashboardOverview } from "../pages/DashboardOverview";
import { AlertCenterPage } from "../pages/AlertCenterPage";
import { WarRoomPage } from "../pages/WarRoomPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <DashboardOverview /> },
      { path: "war-room", element: <WarRoomPage /> },
      { path: "triage", element: <Page title="Triage" /> },
      { path: "alerts", element: <AlertCenterPage /> },
      { path: "incidents", element: <Page title="Incidentes" /> },
      { path: "investigate", element: <Page title="Investigar" /> },
      { path: "cases", element: <Page title="Cases" /> },
      { path: "playbooks", element: <Page title="Playbooks" /> },
      { path: "rules", element: <Page title="Regras" /> },
      { path: "intel", element: <Page title="Intelligence" /> },
      { path: "settings", element: <Page title="Configuração" /> },
    ],
  },
]);