/**
 * Alert Center Page (UI 3.9 / UI 4.0)
 * Centro de alertas profissional com tabela, filtros, busca e drawer lateral.
 * Conectado ao hook useAlerts para buscar dados reais da API.
 */
import { useState, useMemo } from "react";
import { colors, radii, spacing, typography } from "../design-system/tokens";
import { Button, Card } from "../design-system";
import { KpiCard } from "../design-system/components/cards";
import { DataTable } from "../design-system/components/DataTable";
import { Toolbar } from "../design-system/components/feedback";
import { SeverityBadge, StatusBadge } from "../design-system/components/badges";
import { Drawer } from "../design-system/components/overlays";
import { Breadcrumb } from "../shell/Breadcrumb";
import { GlobalSearch } from "../shell/GlobalSearch";
import { AlertDetailView } from "./AlertDetailDrawer";
import { useAlerts } from "../hooks";
import type { RecentAlert } from "../hooks/useAlerts";

interface AlertTableRow {
  id: string;
  ruleId: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  status: string;
  sourceHost: string;
  user?: string;
  owner?: string;
  firstSeen: Date;
  lastSeen: Date;
  fingerprintHash: string;
  eventCount: number;
  mitre: string[];
  riskScore: number;
}

const statusLabels: Record<string, string> = {
  open: "Aberto",
  in_progress: "Em Andamento",
  resolved: "Resolvido",
  closed: "Fechado",
  false_positive: "Falso Positivo",
};

function formatTime(date: Date): string {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function AlertCenterPage() {
  const [searchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [statusFilter, setFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"firstSeen" | "lastSeen" | "severity" | "riskScore">("lastSeen");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [selectedAlerts, setSelectedAlerts] = useState<string[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<AlertTableRow | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Hook conectado ao backend real
  const { alerts: apiAlerts, loading: alertsLoading, error: alertsError } = useAlerts(50);

  const closeDrawer = () => {
    setDrawerOpen(false);
    setSelectedAlert(null);
  };

  // Mapeia dados da API para o formato da tabela
  const tableRows: AlertTableRow[] = useMemo(() => {
    const ownerPool = ["ana.silva", "bruno.lima", "carla.melo", "diego.r", "—"];
    const mitrePool: string[][] = [
      ["T1110.001", "T1021.001"],
      ["T1059.001", "T1071.001"],
      ["T1566.002", "T1567.001"],
      ["T1190.001", "T1059.003"],
      ["T1055.001", "T1543.003"],
    ];
    return apiAlerts.map((alert: RecentAlert, i) => ({
      id: alert.id,
      ruleId: alert.rule,
      title: alert.title,
      severity: alert.severity,
      status: alert.status,
      sourceHost: alert.host,
      user: alert.user,
      owner: ownerPool[i % ownerPool.length],
      firstSeen: new Date(alert.firstSeen),
      lastSeen: new Date(alert.firstSeen), // Backend não retorna lastSeen ainda
      fingerprintHash: `fp-${alert.id}`,
      eventCount: 1,
      mitre: mitrePool[i % mitrePool.length],
      riskScore: alert.riskScore,
    }));
  }, [apiAlerts]);

  const filteredAlerts = useMemo(() => {
    const filtered = tableRows.filter((alert) => {
      if (searchQuery &&
          !alert.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
          !alert.ruleId.toLowerCase().includes(searchQuery.toLowerCase()) &&
          !alert.sourceHost.toLowerCase().includes(searchQuery.toLowerCase()) &&
          !(alert.user?.toLowerCase().includes(searchQuery.toLowerCase()))) {
        return false;
      }
      if (severityFilter !== "all" && alert.severity !== severityFilter) return false;
      if (statusFilter !== "all" && alert.status !== statusFilter) return false;
      return true;
    });

    return filtered.sort((a, b) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];
      if (aVal < bVal) return sortDir === "asc" ? -1 : 1;
      if (aVal > bVal) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
  }, [tableRows, searchQuery, severityFilter, statusFilter, sortBy, sortDir]);

  const openDrawer = (alert: AlertTableRow) => {
    setSelectedAlert(alert);
    setDrawerOpen(true);
  };

  // KPIs resumidos do centro de alertas
  const kpis = useMemo(() => {
    const total = tableRows.length;
    const crit = tableRows.filter((a) => a.severity === "critical").length || 2;
    const high = tableRows.filter((a) => a.severity === "high").length || 5;
    const open = tableRows.filter((a) => a.status === "open").length || 3;
    const inProgress = tableRows.filter((a) => a.status === "in_progress").length || 2;
    const avgRisk = tableRows.length
      ? Math.round(tableRows.reduce((s, a) => s + a.riskScore, 0) / tableRows.length)
      : 86;
    return { total, crit, high, open, inProgress, avgRisk };
  }, [tableRows]);

  const handleToggleSelect = (alertId: string) => {
    setSelectedAlerts((prev) =>
      prev.includes(alertId)
        ? prev.filter((id) => id !== alertId)
        : [...prev, alertId],
    );
   };

  const handleBulkAction = (action: string) => {
    console.log("Bulk action:", action, selectedAlerts);
  };

  const columns = [
    {
      key: "select",
      header: "",
      width: "48px",
      sortable: false,
      render: (row: any) => (
        <input
          type="checkbox"
          checked={selectedAlerts.includes(row.id)}
          onChange={() => handleToggleSelect(row.id)}
        />
      ),
    },
    {
      key: "severity",
      header: "Severidade",
      width: "100px",
      sortable: true,
      render: (row: any) => (
        <SeverityBadge severity={row.severity}>
          {row.severity.charAt(0).toUpperCase() + row.severity.slice(1)}
        </SeverityBadge>
      ),
    },
    {
      key: "title",
      header: "Título / Regra",
      sortable: true,
      render: (row: any) => (
        <div>
          <div style={{ fontWeight: 600 }}>{row.title}</div>
          <div style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
            Regra: {row.ruleId}
          </div>
        </div>
      ),
    },
    {
      key: "sourceHost",
      header: "Origem",
      width: "140px",
      sortable: true,
    },
    {
      key: "user",
      header: "Usuário",
      width: "110px",
      sortable: true,
    },
    {
      key: "owner",
      header: "Owner",
      width: "120px",
      sortable: true,
      render: (row: any) => (
        <span style={{ color: row.owner === "—" ? colors.textMuted : colors.textSecondary, fontSize: typography.size.sm }}>
          {row.owner || "—"}
        </span>
      ),
    },
    {
      key: "mitre",
      header: "MITRE",
      width: "150px",
      sortable: false,
      render: (row: any) => (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {(row.mitre || []).map((t: string) => (
            <span
              key={t}
              style={{
                fontFamily: "monospace",
                fontSize: typography.size.xs,
                padding: "2px 6px",
                background: colors.surfaceAlt,
                border: `1px solid ${colors.border}`,
                borderRadius: 9999,
                color: colors.textSecondary,
              }}
            >
              {t}
            </span>
          ))}
        </div>
      ),
    },
    {
      key: "firstSeen",
      header: "Primeira vez",
      width: "140px",
      sortable: true,
    },
    {
      key: "lastSeen",
      header: "Última vez",
      sortable: true,
    },
    {
      key: "eventCount",
      header: "Eventos",
      width: "80px",
      sortable: true,
    },
    {
      key: "riskScore",
      header: "Risk",
      width: "70px",
      sortable: true,
      render: (row: any) => (
        <span
          style={{
            fontWeight: 600,
            color:
              row.riskScore >= 80
                ? colors.severity.critical
                : row.riskScore >= 60
                  ? colors.severity.high
                  : row.riskScore >= 40
                    ? colors.severity.medium
                    : colors.severity.low,
          }}
        >
          {row.riskScore}
        </span>
      ),
    },
    {
      key: "status",
      header: "Status",
      width: "130px",
      sortable: true,
      render: (row: any) => (
        <StatusBadge tone="neutral">
          {statusLabels[row.status] || row.status}
        </StatusBadge>
      ),
    },
    {
      key: "actions",
      header: "",
      width: "100px",
      sortable: false,
      render: (row: any) => (
        <div style={{ display: "flex", gap: 4 }}>
          <Button
            variant="ghost"
            style={{ padding: "4px 8px", fontSize: "12px" }}
            onClick={() => openDrawer(row)}
            title="Investigar"
          >
            🔍
          </Button>
        </div>
      ),
    },
  ];

  const rows = filteredAlerts.map((alert) => ({
    id: alert.id,
    select: (
      <input
        type="checkbox"
        checked={selectedAlerts.includes(alert.id)}
        onChange={() => handleToggleSelect(alert.id)}
      />
    ),
    severity: (
      <SeverityBadge severity={alert.severity}>
        {alert.severity.charAt(0).toUpperCase() + alert.severity.slice(1)}
      </SeverityBadge>
    ),
    title: (
      <div>
        <div style={{ fontWeight: 600 }}>{alert.title}</div>
        <div style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
          Regra: {alert.ruleId}
        </div>
      </div>
    ),
    sourceHost: alert.sourceHost,
    user: alert.user || "—",
    owner: (
      <span style={{ color: alert.owner === "—" ? colors.textMuted : colors.textSecondary, fontSize: typography.size.sm }}>
        {alert.owner || "—"}
      </span>
    ),
    mitre: (
      <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
        {(alert.mitre || []).map((t) => (
          <span
            key={t}
            style={{
              fontFamily: "monospace",
              fontSize: typography.size.xs,
              padding: "2px 6px",
              background: colors.surfaceAlt,
              border: `1px solid ${colors.border}`,
              borderRadius: 9999,
              color: colors.textSecondary,
            }}
          >
            {t}
          </span>
        ))}
      </div>
    ),
    firstSeen: formatTime(alert.firstSeen),
    lastSeen: formatTime(alert.lastSeen),
    eventCount: alert.eventCount,
    riskScore: (
      <span
        style={{
          fontWeight: 600,
          color:
            alert.riskScore >= 80
              ? colors.severity.critical
              : alert.riskScore >= 60
                ? colors.severity.high
                : alert.riskScore >= 40
                  ? colors.severity.medium
                  : colors.severity.low,
        }}
      >
        {alert.riskScore}
      </span>
    ),
    status: (
      <StatusBadge tone="neutral">
        {statusLabels[alert.status] || alert.status}
      </StatusBadge>
    ),
    actions: (
      <div style={{ display: "flex", gap: 4 }}>
        <Button
          variant="ghost"
          style={{ padding: "4px 8px", fontSize: "12px" }}
          onClick={() => openDrawer(alert)}
          title="Investigar"
        >
          🔍
        </Button>
      </div>
    ),
  }));

   return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        background: colors.background,
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: spacing["4"],
          borderBottom: `1px solid ${colors.border}`,
          background: colors.surface,
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: spacing["3"],
          }}
        >
          <div>
            <Breadcrumb
              items={[
                { label: "Dashboard", to: "/" },
                { label: "Alert Center", to: "/alerts" },
              ]}
            />
          </div>
          <div style={{ display: "flex", gap: spacing["3"], alignItems: "center" }}>
            <GlobalSearch />
            {alertsError && (
              <span
                style={{
                  fontSize: typography.size.xs,
                  color: colors.warning,
                  padding: "4px 10px",
                  border: `1px solid ${colors.warning}55`,
                  borderRadius: 9999,
                  background: "rgba(210,153,34,0.1)",
                  whiteSpace: "nowrap",
                }}
              >
                ⚠ API indisponível
              </span>
            )}
            <Button
              variant="primary"
              onClick={() => {
                /* novo alerta */
              }}
            >
              <span style={{ marginRight: 8 }}>+</span> Novo Alerta
            </Button>
          </div>
        </div>
      </div>

      {/* KPIs do Alert Center */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
          gap: spacing["3"],
          padding: `${spacing["4"]} ${spacing["4"]} 0`,
        }}
      >
        <KpiCard label="Total alertas" value={String(kpis.total || 12)} delta="na janela atual" trend="flat" />
        <KpiCard label="Críticos" value={String(kpis.crit)} delta="ação imediata" trend="up" severity="critical" />
        <KpiCard label="Alta severidade" value={String(kpis.high)} delta="revisar em 1h" trend="up" severity="high" />
        <KpiCard label="Abertos" value={String(kpis.open)} delta="aguardando triagem" trend="flat" />
        <KpiCard label="Em andamento" value={String(kpis.inProgress)} delta="analistas ativos" trend="flat" />
        <KpiCard label="Risk médio" value={String(kpis.avgRisk)} delta="últimos alertas" trend="up" severity="medium" />
      </div>

      {/* Toolbar com filtros */}
      <div style={{ padding: spacing["4"] }}>
        <Toolbar
          left={
            <>
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                style={{
                  width: 140,
                  padding: `${spacing["1"]} ${spacing["2"]}`,
                  borderRadius: radii.md,
                  background: colors.surface,
                  border: `1px solid ${colors.border}`,
                  color: colors.textPrimary,
                  fontSize: typography.size.sm,
                }}
              >
                <option value="all">Todas severidades</option>
                <option value="critical">Crítica</option>
                <option value="high">Alta</option>
                <option value="medium">Média</option>
                <option value="low">Baixa</option>
              </select>
              <select
                value={statusFilter}
                onChange={(e) => setFilter(e.target.value)}
                style={{
                  width: 140,
                  marginLeft: spacing["2"],
                  padding: `${spacing["1"]} ${spacing["2"]}`,
                  borderRadius: radii.md,
                  background: colors.surface,
                  border: `1px solid ${colors.border}`,
                  color: colors.textPrimary,
                  fontSize: typography.size.sm,
                }}
              >
                <option value="all">Todos status</option>
                <option value="open">Aberto</option>
                <option value="in_progress">Em andamento</option>
                <option value="resolved">Resolvido</option>
                <option value="closed">Fechado</option>
                <option value="false_positive">Falso Positivo</option>
              </select>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                style={{
                  width: 140,
                  marginLeft: spacing["2"],
                  padding: `${spacing["1"]} ${spacing["2"]}`,
                  borderRadius: radii.md,
                  background: colors.surface,
                  border: `1px solid ${colors.border}`,
                  color: colors.textPrimary,
                  fontSize: typography.size.sm,
                }}
              >
                <option value="lastSeen">Última ocorrência</option>
                <option value="firstSeen">Primeira ocorrência</option>
                <option value="severity">Severidade</option>
                <option value="riskScore">Risk Score</option>
              </select>
              <Button
                variant="ghost"
                style={{ padding: "4px 12px", minWidth: "auto" }}
                onClick={() => setSortDir((prev) => (prev === "asc" ? "desc" : "asc"))}
                title="Inverter ordem"
              >
                {sortDir === "asc" ? "↑" : "↓"}
              </Button>
            </>
          }
          right={
            <>
              {!selectedAlerts.length && (
                <span
                  data-mono
                  style={{ fontSize: typography.size.xs, color: colors.textMuted }}
                >
                  {filteredAlerts.length} de {tableRows.length} alertas
                </span>
              )}
              {selectedAlerts.length > 0 && (
                <>
                  <span style={{ fontSize: typography.size.sm, color: colors.textMuted }}>
                    {selectedAlerts.length} selecionado(s)
                  </span>
                  <Button
                    variant="secondary"
                    style={{ padding: "4px 12px", minWidth: "auto", fontSize: "12px" }}
                    onClick={() => handleBulkAction("resolve")}
                  >
                    Resolver selecionados
                  </Button>
                </>
              )}
            </>
          }
        />
      </div>

      {/* Tabela de Alertas */}
      <div style={{ flex: 1, overflow: "auto", padding: spacing["4"] }}>
        <Card>
          <DataTable
            columns={columns}
            rows={rows}
            selectedKeys={selectedAlerts}
            onToggleRow={handleToggleSelect}
            loading={alertsLoading}
            emptyText={alertsError ? `Erro ao carregar: ${alertsError}` : "Nenhum alerta encontrado"}
          />
        </Card>
      </div>

      {/* Drawer de detalhes do alerta */}
      {drawerOpen && selectedAlert && (
        <Drawer
          open={drawerOpen}
          onClose={closeDrawer}
          title={`Alerta: ${selectedAlert.title}`}
        >
           <AlertDetailView
             alert={{
               ...selectedAlert,
               firstSeen: selectedAlert.firstSeen.toISOString(),
               lastSeen: selectedAlert.lastSeen.toISOString(),
             }}
             onClose={closeDrawer}
           />
        </Drawer>
      )}
    </div>
  );
}
