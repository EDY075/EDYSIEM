/**
 * Alert Center Page (UI 3.9)
 * Centro de alertas profissional com tabela, filtros, busca e drawer lateral.
 */
import { useState, useMemo } from "react";
import { colors, radii, spacing, typography } from "../design-system/tokens";
import { Button, Card } from "../design-system";
import { DataTable } from "../design-system/components/DataTable";
import { Toolbar } from "../design-system/components/feedback";
import { SeverityBadge, StatusBadge } from "../design-system/components/badges";
import { Drawer } from "../design-system/components/overlays";
import { Breadcrumb } from "../shell/Breadcrumb";
import { GlobalSearch } from "../shell/GlobalSearch";
import { AlertDetailView } from "./AlertDetailDrawer";

type Severity = "critical" | "high" | "medium" | "low" | "info";

interface AlertTableRow {
  id: string;
  ruleId: string;
  title: string;
  severity: Severity;
  status: string;
  sourceHost: string;
  user?: string;
  firstSeen: Date;
  lastSeen: Date;
  fingerprintHash: string;
  eventCount: number;
  mitre: string[];
  riskScore: number;
}

const MOCK_ALERTS: AlertTableRow[] = [
  {
    id: "ALT-20260804-001",
    ruleId: "brute-force-ssh",
    title: "Brute Force SSH - Múltiplas falhas",
    severity: "high",
    status: "open",
    sourceHost: "web-01",
    user: "root",
    firstSeen: new Date("2026-08-04T10:15:00"),
    lastSeen: new Date("2026-08-04T10:45:00"),
    fingerprintHash: "fp-abc123",
    eventCount: 47,
    mitre: ["T1110.001"],
    riskScore: 85,
  },
  {
    id: "ALT-20260804-002",
    ruleId: "malware-execution",
    title: "Execução suspeita - PowerShell encoded",
    severity: "critical",
    status: "open",
    sourceHost: "wks-042",
    user: "john.doe",
    firstSeen: new Date("2026-08-04T14:22:00"),
    lastSeen: new Date("2026-08-04T14:22:00"),
    fingerprintHash: "fp-xyz789",
    eventCount: 3,
    mitre: ["T1059.001"],
    riskScore: 95,
  },
  {
    id: "ALT-20260804-003",
    ruleId: "impossible-travel",
    title: "Impossible Travel - Login geo-impossível",
    severity: "high",
    status: "in_progress",
    sourceHost: "vpn-gateway",
    user: "jane.smith",
    firstSeen: new Date("2026-08-04T08:15:00"),
    lastSeen: new Date("2026-08-04T10:30:00"),
    fingerprintHash: "fp-geo-001",
    eventCount: 2,
    mitre: ["T1110.001"],
    riskScore: 78,
  },
];

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

  const closeDrawer = () => {
    setDrawerOpen(false);
    setSelectedAlert(null);
  };

  const filteredAlerts = useMemo(() => {
    const filtered = MOCK_ALERTS.filter((alert) => {
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
  }, [searchQuery, severityFilter, statusFilter, sortBy, sortDir]);

  const openDrawer = (alert: AlertTableRow) => {
    setSelectedAlert(alert);
    setDrawerOpen(true);
  };

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
      width: "120px",
      sortable: true,
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
            loading={false}
            emptyText="Nenhum alerta encontrado"
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
