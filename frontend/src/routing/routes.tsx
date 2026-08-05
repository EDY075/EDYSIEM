/**
 * Routing (UI 3.2 / UI 4.x / Sprint 2.14)
 * Definição de rotas da aplicação conectada às páginas reais.
 *
 * Performance (Sprint 2.14 / WP1): páginas pesadas carregadas via React.lazy
 * (code-splitting). O chunk inicial fica enxuto; cada tela é baixada sob demanda.
 */
import { lazy, Suspense } from "react";
import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "../shell/AppShell";
import { Page } from "../components/Page";
import { colors } from "../design-system/tokens";

const DashboardOverview = lazy(() => import("../pages/DashboardOverview").then((m) => ({ default: m.DashboardOverview })));
const WarRoomPage = lazy(() => import("../pages/WarRoomPage").then((m) => ({ default: m.WarRoomPage })));
const AlertCenterPage = lazy(() => import("../pages/AlertCenterPage").then((m) => ({ default: m.AlertCenterPage })));

/** Fallback global de carregamento de rota (barra fina superior, GPU-friendly). */
function RouteFallback() {
  return (
    <div
      role="status"
      aria-label="Carregando página"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        height: 2,
        zIndex: 999,
        overflow: "hidden",
        background: colors.border,
      }}
    >
      <div
        style={{
          height: "100%",
          width: "40%",
          background: `linear-gradient(90deg, transparent, ${colors.accent}, transparent)`,
          animation: "route-progress 1.1s cubic-bezier(0.4,0,0.2,1) infinite",
        }}
      />
      <style>{`@keyframes route-progress { 0% { transform: translateX(-100%);} 100% { transform: translateX(350%);} }
@media (prefers-reduced-motion: reduce) { [role="status"] { display: none; } }`}</style>
    </div>
  );
}

function withSuspense(node: React.ReactNode) {
  return <Suspense fallback={<RouteFallback />}>{node}</Suspense>;
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: withSuspense(<DashboardOverview />) },
      { path: "war-room", element: withSuspense(<WarRoomPage />) },
      { path: "triage", element: <Page title="Triage" /> },
      { path: "alerts", element: withSuspense(<AlertCenterPage />) },
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
