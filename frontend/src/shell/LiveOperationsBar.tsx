/**
 * Live Operations Bar (UI 3.6)
 * Barra de operações em tempo real no topo do dashboard.
 * Mostra status do sistema em tempo real: status, EPS, alertas, casos, ingestão, DB, latência.
 */
import { useState, useEffect } from "react";
import { colors, motion, spacing, typography } from "../design-system";

interface LiveOpsData {
  systemStatus: "online" | "degraded" | "offline";
  eventsPerSecond: number;
  activeAlerts: number;
  openCases: number;
  ingestionStatus: "online" | "degraded" | "offline";
  dbStatus: "online" | "degraded" | "offline";
  apiLatencyMs: number;
}

const MOCK_DATA: LiveOpsData = {
  systemStatus: "online",
  eventsPerSecond: 1247,
  activeAlerts: 23,
  openCases: 5,
  ingestionStatus: "online",
  dbStatus: "online",
  apiLatencyMs: 42,
};

export function LiveOperationsBar() {
  const [data, setData] = useState<LiveOpsData>(MOCK_DATA);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Simular atualizações em tempo real (em produção viria via WebSocket/SSE)
  useEffect(() => {
    const interval = setInterval(() => {
      // Simular pequenas variações nos dados
      setData(prev => ({
        ...prev,
        eventsPerSecond: Math.max(0, prev.eventsPerSecond + Math.floor((Math.random() - 0.5) * 50)),
        activeAlerts: Math.max(0, prev.activeAlerts + Math.floor((Math.random() - 0.3) * 5)),
        openCases: Math.max(0, prev.openCases + Math.floor((Math.random() - 0.4) * 2)),
        apiLatencyMs: Math.max(5, Math.min(200, prev.apiLatencyMs + Math.floor((Math.random() - 0.5) * 20))),
      });
      setLastUpdate(new Date());
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const statusColors = {
    online: colors.status.online,
    degraded: colors.status.degraded,
    offline: colors.status.offline,
  };

  const statusLabels = {
    online: "Sistema Online",
    degraded: "Degradado",
    offline: "Offline",
  };

  const ingestionLabels = {
    online: "Ingestão Normal",
    degraded: "Ingestão Lenta",
    offline: "Ingestão Offline",
  };

  const dbLabels = {
    online: "Banco Online",
    degraded: "Banco Lento",
    offline: "Banco Offline",
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
    if (num >= 1000) return (num / 1000).toFixed(1) + "K";
    return String(num);
  };

  return (
    <div
      style={{
        background: colors.surfaceAlt,
        borderBottom: `1px solid ${colors.border}`,
        padding: `${spacing["2"]} ${spacing["4"]}`,
        display: "flex",
        alignItems: "center",
        gap: spacing["4"],
        flexWrap: "wrap",
        minHeight: 40,
      }}
    >
      {/* Status do Sistema */}
      <div style={{ display: "flex", alignItems: "center", gap: spacing["2"] }}>
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: statusColors[data.systemStatus],
            boxShadow: `0 0 8px ${statusColors[data.systemStatus]}`,
          }}
        />
        <span
          style={{
            fontSize: typography.size.sm,
            fontWeight: typography.weight.semibold,
            color: statusColors[data.systemStatus],
          }}
        >
          {statusLabels[data.systemStatus]}
        </span>
      </div>

      <div
        style={{
          width: 1,
          height: 24,
          background: colors.border,
          marginLeft: spacing["4"],
          marginRight: spacing["4"],
        }}
      />

      {/* Events/sec */}
      <div style={{ display: "flex", alignItems: "center", gap: spacing["1"] }}>
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
        <span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
          eps
        </span>
      </div>

      <div
        style={{
          width: 1,
          height: 24,
          background: colors.border,
          marginLeft: spacing["4"],
          marginRight: spacing["4"],
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
          marginLeft: spacing["4"],
          marginRight: spacing["4"],
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
          marginLeft: spacing["4"],
          marginRight: spacing["4"],
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
          {ingestionLabels[data.ingestionStatus]}
        </span>
      </div>

      <div
        style={{
          width: 1,
          height: 24,
          background: colors.border,
          marginLeft: spacing["4"],
          marginRight: spacing["4"],
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
          {dbLabels[data.dbStatus]}
        </span>
      </div>

      <div
        style={{
          width: 1,
          height: 24,
          background: colors.border,
          marginLeft: spacing["4"],
          marginRight: spacing["4"],
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
            color: data.apiLatencyMs > 100 ? colors.severity.high : colors.textPrimary,
            fontFamily: typography.family.mono,
          }}
        >
          {data.apiLatencyMs}ms
        </span>
      </div>

      <div style={{ flex: 1 }} />

      {/* Última atualização */}
      <span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
        Atualizado: {lastUpdate.toLocaleTimeString()}
      </span>
    </div>
  );
};

const statusColors = {
  online: colors.status.online,
  degraded: colors.status.degraded,
  offline: colors.status.offline,
};

const statusLabels = {
  online: "Sistema Online",
  degraded: "Degradado",
  offline: "Offline",
};

const ingestionLabels = {
  online: "Ingestão Normal",
  degraded: "Ingestão Lenta",
  offline: "Ingestão Offline",
};

const dbLabels = {
  online: "Banco Online",
  degraded: "Banco Lento",
  offline: "Banco Offline",
};

const statusColors = {
  online: colors.status.online,
  degraded: colors.status.degraded,
  offline: colors.status.offline,
};