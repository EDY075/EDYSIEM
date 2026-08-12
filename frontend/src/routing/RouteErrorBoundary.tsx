import { isRouteErrorResponse, useRouteError } from "react-router-dom";
import { Button, colors, radii, spacing, typography } from "../design-system";

/** Estado seguro para falhas inesperadas de rota, sem expor stack ao analista. */
export function RouteErrorBoundary() {
  const error = useRouteError();
  const unavailable = isRouteErrorResponse(error) && error.status >= 500;
  const title = unavailable ? "Área temporariamente indisponível" : "Não foi possível abrir esta área";
  const description = unavailable
    ? "O serviço local não respondeu como esperado. Tente novamente ou volte à visão operacional."
    : "A navegação foi interrompida antes de carregar esta área. Nenhum dado operacional foi alterado.";

  return (
    <main
      aria-labelledby="route-error-title"
      style={{
        display: "grid",
        minHeight: "100vh",
        placeItems: "center",
        padding: spacing["5"],
        background: colors.background,
      }}
    >
      <section
        role="alert"
        aria-live="assertive"
        style={{
          width: "min(100%, 520px)",
          padding: spacing["6"],
          border: `1px solid ${colors.border}`,
          borderRadius: radii.xl,
          background: colors.surface,
          boxShadow: "var(--elevation-overlay)",
        }}
      >
        <p style={{ margin: 0, color: colors.accent, fontSize: typography.size.xs, fontWeight: typography.weight.bold, letterSpacing: ".12em" }}>
          EDY SIEM · RECUPERAÇÃO SEGURA
        </p>
        <h1 id="route-error-title" style={{ margin: `${spacing["2"]} 0 ${spacing["2"]}`, color: colors.textPrimary, fontSize: typography.size["2xl"] }}>
          {title}
        </h1>
        <p style={{ margin: 0, color: colors.textSecondary, fontSize: typography.size.base, lineHeight: typography.lineHeight.relaxed }}>
          {description}
        </p>
        <div style={{ display: "flex", flexWrap: "wrap", gap: spacing["2"], marginTop: spacing["5"] }}>
          <Button onClick={() => window.location.reload()}>Tentar novamente</Button>
          <Button variant="secondary" onClick={() => { window.location.assign("/"); }}>Voltar ao Overview</Button>
        </div>
      </section>
    </main>
  );
}
