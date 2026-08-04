/**
 * Routing (UI 3.2)
 * Definição de rotas da aplicação. Páginas são stubs estruturais.
 */
import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "../shell/AppShell";
import { Page } from "../components/Page";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <Page title="Overview" /> },
      { path: "triage", element: <Page title="Triage" /> },
      { path: "alerts", element: <Page title="Alertas" /> },
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
