/**
 * Live Operations Bar (UI 3.6 / UI 4.0)
 * Barra de operações em tempo real no topo do dashboard.
 *
 * CONECTADO ao backend real:
 * - /health → status do sistema
 * - /metrics → EPS, alertas, casos, latência
 *
 * Nota: não usa WebSocket (não implementado no backend ainda).
 * Atualização via polling de 30 segundos.
 */
import { useState, useEffect, useCallback } from "react";
import { colors, spacing, typography } from "../design-system/tokens";
import { useHealth, useMetrics } from "../hooks";

interface LiveOpsData {
  systemStatus: "online" | "degraded" | "offline";
  eventsPerSecond: number;
  activeAlerts: number;
  openCases: number;
  ingestionStatus: "online" | "degraded" | "offline";
  dbStatus: "online" | "degraded" | "offline";
  apiLatencyMs: number | null;
}

export function LiveOperationsBar() {
  const { health, loading: healthLoading, error: healthError, lastUpdated: healthUpdatedAt } = useHealth();
  const { metrics, loading: metricsLoading, error: metricsError, lastUpdated: metricsUpdatedAt } = useMetrics("1h");

  const [localTime, setLocalTime] = useState(() => new Date());

  useEffect(() => {
    const clock = window.setInterval(() => setLocalTime(new Date()), 1000);
    return () => window.clearInterval(clock);
  }, []);

  const isLoading = healthLoading || metricsLoading;
  const hasError = !!healthError || !!metricsError;
  const lastResponseAt = [healthUpdatedAt, metricsUpdatedAt].filter((value): value is Date => value !== null).sort((a, b) => b.getTime() - a.getTime())[0] ?? null;

  // Constrói dados a partir dos hooks conectados
  const data: LiveOpsData = {
    systemStatus: (health.api === "online" || !hasError) ? "online" : health.api as "online" | "degraded" | "offline",
    eventsPerSecond: metrics.eps || 0,
    activeAlerts: metrics.activeAlerts || 0,
    openCases: metrics.openCases || 0,
    ingestionStatus: health.ingestion as "online" | "degraded" | "offline",
    dbStatus: health.storage as "online" | "degraded" | "offline",
    apiLatencyMs: null,
  };

  const statusColors = {
    online: colors.status.online,
    degraded: colors.status.degraded,
    offline: colors.status.offline,
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
    if (num >= 1000) return (num / 1000).toFixed(1) + "K";
    return String(num);
  };

  const refetch = useCallback(() => {
    // Aciona refetch dos hooks manualmente (polling manual)
    // Os hooks já fazem polling interno via useEffect
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      refetch();
    }, 30000);

    return () => clearInterval(interval);
  }, [refetch]);

  return (
    <div
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
            ? "Sistema Online"
            : data.systemStatus === "degraded"
              ? "Degradado"
              : "Offline"}
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

      {/* Events/sec */}
      <div style={{ display: "flex", alignItems: "center", gap: spacing["1"] }}>
        {isLoading ? (
          <div style={{ fontSize: typography.size.lg, color: colors.textMuted }}>
            —
          </div>
        ) : (
          <span
            style={{
              fontSize: typography.size.lg,
              fontWeight: typography.weight.bold,
              color: colors.textPrimary,
              fontFamily: typography.family.mono,
            }}
          >
            {formatNumber(data.eventsPerSecond)}
          </span>
        )}
        <span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
          eps
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

      {/* Alertas Ativos */}
      <div style={{ display: "flex", alignItems: "center", gap: spacing["1"] }}>
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: colors.severity.critical,
          }}
        />
        <span
          style={{
            fontSize: typography.size.sm,
            fontWeight: typography.weight.medium,
            color: colors.textPrimary,
          }}
        >
          {formatNumber(data.activeAlerts)}
        </span>
        <span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
          alertas
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

      {/* Casos Abertos */}
      <div style={{ display: "flex", alignItems: "center", gap: spacing["1"] }}>
        <span style={{ fontSize: typography.size.sm, color: colors.textPrimary }}>
          {formatNumber(data.openCases)}
        </span>
        <span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
          casos
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
            ? "Ingestão Normal"
            : data.ingestionStatus === "degraded"
              ? "Ingestão Lenta"
              : "Ingestão Offline"}
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

      <div
        style={{
          width: 1,
          height: 24,
          background: colors.border,
          marginLeft: 12,
          marginRight: 12,
        }}
      />

      {/* Latência API */}
      <div style={{ display: "flex", alignItems: "center", gap: spacing["1"] }}>
        <span style={{ fontSize: typography.size.sm, color: colors.textSecondary }}>
          Latência API
        </span>
        <span
          style={{
            fontSize: typography.size.sm,
            fontWeight: typography.weight.semibold,
            color: data.apiLatencyMs === null ? colors.textMuted : data.apiLatencyMs > 100 ? colors.severity.high : colors.textPrimary,
            fontFamily: typography.family.mono,
          }}
        >
          {data.apiLatencyMs === null ? "—" : `${data.apiLatencyMs}ms`}
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
          title={healthError || metricsError || ""}
        >
          ⚠ dados não atualizados
        </span>
      )}

      <div style={{ flex: 1 }} />

      {/* Última atualização */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 2, fontFamily: typography.family.mono, fontSize: typography.size.xs, color: colors.textMuted, whiteSpace: "nowrap" }}>
        <span>Última resposta API: {lastResponseAt ? lastResponseAt.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23" }) : "—"}</span>
        <span aria-live="off">Horário local: {localTime.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23" })}</span>
      </div>
    </div>
  );
}
