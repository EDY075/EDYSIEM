/**
 * AppShell + Layout (UI 3.3)
 * Shell de 3 zonas: Sidebar + (Topbar + Conteúdo) + Footer.
 * Responsivo: sidebar colapsa em telas pequenas. Rota aninhada via <Outlet/>.
 */
import { useState } from "react";
import { Outlet } from "react-router-dom";
import { colors } from "../design-system";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { Footer } from "./Footer";
import { LiveOperationsBar } from "./LiveOperationsBar";

export function AppShell() {
  const [sidebarVisible, setSidebarVisible] = useState(true);

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {sidebarVisible && <Sidebar />}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <Topbar />
        <LiveOperationsBar />
        <main style={{ flex: 1, padding: 20, minWidth: 0 }}>
          <Outlet />
        </main>
        <Footer />
      </div>

      {/* Responsividade: toggle da sidebar em telas pequenas */}
      <button
        onClick={() => setSidebarVisible((v) => !v)}
        data-floating
        style={{
          position: "fixed",
          left: 8,
          bottom: 8,
          zIndex: 500,
          background: colors.surfaceAlt,
          color: colors.textPrimary,
          border: `1px solid ${colors.border}`,
          borderRadius: 6,
          padding: 8,
          cursor: "pointer",
        }}
      >
        \u2630
      </button>

      <style>{`
        @media (min-width: 769px) {
          button[data-floating] { display: none; }
        }
      `}</style>
    </div>
  );
}

/** Layout simples de conteúdo (ex.: master-detail). */
export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>{children}</div>
  );
}