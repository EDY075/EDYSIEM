/**
 * Live Operations Bar (UI 3.6 / UI 4.0)
 * Barra de operações em tempo real no topo do dashboard.
 *
 * CONECTADO ao backend real:
 * - /health → status do sistema
 * - /health → estado agregado, receptor Shield e storage
 *
 * Nota: não usa WebSocket (não implementado no backend ainda).
 * Atualização via polling de 30 segundos.
 */
import { useEffect, useCallback } from "react";
import { colors, spacing, typography } from "../design-system/tokens";
import { useHealth } from "../hooks";

interface LiveOpsData {
  systemStatus: "online" | "degraded" | "offline";
  ingestionStatus: "online" | "degraded" | "offline";
  dbStatus: "online" | "degraded" | "offline";
}

export function LiveOperationsBar() {
  const { health, loading: healthLoading, error: healthError, lastUpdated: healthUpdatedAt, refetch: refetchHealth } = useHealth();
  const isLoading = healthLoading;
  const hasError = !!healthError;
  const hasKnownHealth = healthUpdatedAt !== null;
  const displayedResponseAt = healthUpdatedAt;

  // Constrói dados a partir dos hooks conectados
  const data: LiveOpsData = {
    systemStatus: healthError
      ? (hasKnownHealth ? "degraded" : "offline")
      : health.overall === "healthy" ? "online" : "degraded",
    ingestionStatus: health.ingestion === "online" ? "online" : health.ingestion === "degraded" ? "degraded" : "offline",
    dbStatus: health.storage === "online" ? "online" : health.storage === "degraded" ? "degraded" : "offline",
  };

  const statusColors = {
    online: colors.status.online,
    degraded: colors.status.degraded,
    offline: colors.status.offline,
  };

  const refetch = useCallback(() => {
    void refetchHealth();
  }, [refetchHealth]);

  useEffect(() => {
    const interval = setInterval(() => {
      refetch();
    }, 30000);

    return () => clearInterval(interval);
  }, [refetch]);

  return (
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
      aria-label="Estado operacional do EDY SIEM"
      style={{
        background: `linear-gradient(90deg, color-mix(in srgb, ${colors.surfaceAlt} 86%, ${colors.surface}) 0%, ${colors.surfaceAlt} 100%)`,
        borderBottom: `1px solid ${colors.border}`,
        padding: `${spacing["2"]} ${spacing["5"]}`,
        display: "flex",
        alignItems: "center",
        gap: 10,
        flexWrap: "wrap",
        minHeight: 42,
        opacity: isLoading ? 0.7 : 1,
        transition: "opacity 0.2s ease",
      }}
    >
      {/* Status do Sistema */}
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: spacing["2"],
          padding: "3px 10px",
          borderRadius: 9999,
          background: `color-mix(in srgb, ${statusColors[data.systemStatus]} 12%, transparent)`,
          border: `1px solid color-mix(in srgb, ${statusColors[data.systemStatus]} 32%, transparent)`,
        }}
      >
        <span
          aria-hidden="true"
          style={{
            width: 7,
            height: 7,
            borderRadius: "50%",
            background: statusColors[data.systemStatus],
            boxShadow: `0 0 0 3px color-mix(in srgb, ${statusColors[data.systemStatus]} 12%, transparent)`,
            flex: "none",
          }}
        />
        <span
          style={{
            fontSize: typography.size.xs,
            fontWeight: typography.weight.semibold,
            color: statusColors[data.systemStatus],
            letterSpacing: "0.02em",
          }}
        >
          {data.systemStatus === "online"
            ? "Operação normal"
            : data.systemStatus === "degraded"
              ? "Operação degradada"
              : "API indisponível"}
        </span>
      </div>

      {health.environment === "development" && (
        <span style={{ fontSize: typography.size.xs, color: colors.textMuted, letterSpacing: "0.06em" }}>
          AMBIENTE LOCAL
        </span>
      )}

      <div
        style={{
          width: 1,
          height: 24,
          background: colors.border,
          marginLeft: 12,
          marginRight: 12,
        }}
      />

      {/* Ingestão */}
      <div style={{ display: "flex", alignItems: "center", gap: spacing["1"] }}>
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: statusColors[data.ingestionStatus],
          }}
        />
        <span
          style={{
            fontSize: typography.size.sm,
            color: statusColors[data.ingestionStatus],
          }}
        >
          {data.ingestionStatus === "online"
            ? "EDY Shield · receptor pronto"
            : data.ingestionStatus === "degraded"
              ? "EDY Shield · receptor degradado"
              : "EDY Shield · receptor indisponível"}
        </span>
      </div>

      <div
        style={{
          width: 1,
          height: 24,
          background: colors.border,
          marginLeft: 12,
          marginRight: 12,
        }}
      />

      {/* Banco de Dados */}
      <div style={{ display: "flex", alignItems: "center", gap: spacing["1"] }}>
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: statusColors[data.dbStatus],
          }}
        />
        <span
          style={{
            fontSize: typography.size.sm,
            color: statusColors[data.dbStatus],
          }}
        >
          {data.dbStatus === "online"
            ? "Banco Online"
            : data.dbStatus === "degraded"
              ? "Banco Lento"
              : "Banco Offline"}
        </span>
      </div>

      {hasError && (
        <span
          style={{
            fontSize: typography.size.xs,
            color: colors.severity.medium,
            padding: "2px 8px",
            background: "color-mix(in srgb, var(--severity-medium) 14%, transparent)",
            borderRadius: 4,
          }}
          title={healthError || ""}
        >
          Dados de saúde desatualizados
        </span>
      )}

      <div style={{ flex: 1 }} />

      {/* Última atualização */}
      <div style={{ display: "flex", alignItems: "center", fontFamily: typography.family.mono, fontSize: typography.size.xs, color: colors.textMuted, whiteSpace: "nowrap" }}>
        <span>{healthError && hasKnownHealth ? "Último estado conhecido" : "Última resposta API"}: {displayedResponseAt ? displayedResponseAt.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23" }) : "—"}</span>
      </div>
    </div>
  );
}
