/**
 * AppShell + Layout (UI 3.3)
 * Shell de 3 zonas: Sidebar + (Topbar + Conteúdo) + Footer.
 * Responsivo: sidebar colapsa em telas pequenas. Rota aninhada via <Outlet/>.
 */
import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import { colors } from "../design-system";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { Footer } from "./Footer";
import { LiveOperationsBar } from "./LiveOperationsBar";

export function AppShell() {
  const [isMobile, setIsMobile] = useState(() => window.matchMedia("(max-width: 768px)").matches);
  const [sidebarVisible, setSidebarVisible] = useState(() => !window.matchMedia("(max-width: 768px)").matches);

  useEffect(() => {
    const query = window.matchMedia("(max-width: 768px)");
    const syncViewport = () => {
      setIsMobile(query.matches);
      setSidebarVisible(!query.matches);
    };
    query.addEventListener("change", syncViewport);
    return () => query.removeEventListener("change", syncViewport);
  }, []);

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {sidebarVisible && (
        <div
          style={isMobile ? {
            position: "fixed",
            inset: "0 auto 0 0",
            zIndex: 700,
            boxShadow: "16px 0 36px rgba(4, 10, 18, 0.28)",
          } : undefined}
        >
          <Sidebar />
        </div>
      )}
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
        aria-label={sidebarVisible ? "Fechar navegação" : "Abrir navegação"}
        style={{
          position: "fixed",
          left: 8,
          bottom: 8,
          zIndex: 800,
          background: colors.surfaceAlt,
          color: colors.textPrimary,
          border: `1px solid ${colors.border}`,
          borderRadius: 6,
          padding: 8,
          cursor: "pointer",
        }}
      >
        {sidebarVisible ? "×" : "☰"}
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
