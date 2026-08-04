/**
 * Alert Center Page (UI 3.9)
 * Centro de alertas profissional com tabela, filtros, busca e drawer lateral
 */
import { useState, useMemo } from "react";
import { Alert, AlertSeverity, AlertLifecycle } from "../../alerts";
import { DataTable, DataColumn } from "../design-system/components/DataTable";
import { Toolbar } from "../design-system/components/feedback";
import { SeverityBadge, StatusBadge } from "../design-system/components/badges";
import { Breadcrumb } from "../shell/Breadcrumb";
import { GlobalSearch } from "../shell/GlobalSearch";
import { Button, Badge, Card } from "../design-system";
import { Alert, AlertSeverity, AlertLifecycle } from "../../alerts";

interface AlertTableRow {
  id: string;
  ruleId: string;
  title: string;
  severity: AlertSeverity;
  status: AlertLifecycle;
  sourceHost: string;
  user?: string;
  firstSeen: Date;
  lastSeen: Date;
  fingerprintHash: string;
  eventCount: number;
  mitre: string[];
  riskScore: number;
}

const MOCK_ALERTS = [
  {
    id: "ALT-20260804-001",
    ruleId: "brute-force-ssh",
    title: "Brute Force SSH - Múltiplas falhas",
    severity: "high" as const,
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
  {
    id: "ALT-20260804-004",
    ruleId: "data-exfiltration",
    title: "Exfiltração de dados - Upload massivo para cloud",
    severity: "critical",
    status: "in_progress",
    sourceHost: "wks-087",
    user: "jane.doe",
    firstSeen: new Date("2026-08-04T09:00:00"),
    lastSeen: new Date("2026-08-04T11:30:00"),
    fingerprintHash: "fp-dataexfil-001",
    eventCount: 12,
    mitre: ["T1041", "T1048"],
    riskScore: 92,
  },
  {
    id: "ALT-20260804-005",
    ruleId: "crypto-miner",
    title: "Crypto Miner detectado - XMRig",
    severity: "high",
    status: "open",
    sourceHost: "wks-033",
    user: "svc-backup",
    firstSeen: new Date("2026-08-04T06:00:00"),
    lastSeen: new Date("2026-08-04T06:00:00"),
    fingerprintHash: "fp-cryptominer-001",
    eventCount: 1,
    mitre: ["T1496"],
    riskScore: 88,
  },
];

export function AlertCenterPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"firstSeen" | "lastSeen" | "severity" | "riskScore">("lastSeen");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [selectedAlerts, setSelectedAlerts] = useState<string[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<any | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const filteredAlerts = useMemo(() => {
    return ALERTS_MOCK.filter(alert => {
      if (searchQuery && !alert.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
          !alert.ruleId.toLowerCase().includes(searchQuery.toLowerCase()) &&
          !alert.sourceHost.toLowerCase().includes(searchQuery.toLowerCase()) &&
          !alert.user?.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      if (severityFilter !== "all" && alert.severity !== severityFilter) return false;
      if (statusFilter !== "all" && alert.status !== statusFilter) return false;
      return true;
    }).sort((a, b) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];
      if (aVal < bVal) return sortDir === "asc" ? -1 : 1;
      if (aVal > bVal) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
  }, [searchQuery, severityFilter, statusFilter, sortBy, sortDir]);

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedAlerts, setSelectedAlerts] = useState<string[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<any | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const severityColors: Record<string, string> = {
    critical: "#F85149",
    high: "#DB6E28",
    medium: "#D29922",
    low: "#58A6FF",
    info: "#58A6FF",
  };

  const statusColors: Record<string, string> = {
    open: "#58A6FF",
    in_progress: "#D29922",
    resolved: "#3FB950",
    closed: "#6E7681",
    false_positive: "#9DA7B3",
  };

  const statusLabels: Record<string, string> = {
    open: "Aberto",
    in_progress: "Em Andamento",
    resolved: "Resolvido",
    closed: "Fechado",
    false_positive: "Falso Positivo",
  };

  const severityColors: Record<string, string> = {
    critical: "#F85149",
    high: "#DB6E28",
    medium: "#D29922",
    low: "#58A6FF",
    info: "#58A6FF",
  };

  const severityLabels: Record<string, string> = {
    critical: "Crítico",
    high: "Alto",
    medium: "Médio",
    low: "Baixo",
    info: "Info",
  };

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(date));
  };

  const handleRowClick = (alert: any) => {
    setSelectedAlert(alert);
    setDrawerOpen(true);
  };

  const handleSelectionChange = (alertId: string) => {
    setSelectedAlerts(prev => 
      prev.includes(alertId) 
        ? prev.filter(id => id !== alert.id)
        : [...prev, alert.id]
    );
  };

  const handleSelectAll = () => {
    if (selectedAlerts.length === filteredAlerts.length) {
      setSelectedAlerts([]);
    } else {
      setSelectedAlerts(filteredAlerts.map(a => a.id));
    }
  };

  const handleBulkAction = (action: "resolve" | "assign" | "suppress" | "delete") => {
    // TODO: Implementar ações em lote
    console.log("Bulk action:", action, selectedAlerts);
  };

  const openDrawer = (alert: any) => {
    setSelectedAlert(alert);
    setDrawerOpen(true);
  };

  const closeDrawer = () => {
    setSelectedAlert(null);
    setDrawerOpen(false);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: colors.background }}>
      {/* Header com breadcrumb e busca */}
      <div style={{ 
        padding: spacing["4"], 
        borderBottom: `1px solid ${colors.border}`,
        background: colors.surface,
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: spacing["3"] }}>
          <div>
            <Breadcrumb items={[
              { label: "Dashboard", to: "/" },
              { label: "Alert Center", to: "/alerts" },
            ]} />
          </div>
          <div style={{ display: "flex", gap: spacing["3"], alignItems: "center" }}>
            <GlobalSearch />
            <Button variant="primary" onClick={() => { /* novo alerta */ }}>
              <span style={{ marginRight: 8 }}>+</span> Novo Alerta
            </Button>
          </div>
        </div>
      </div>

      {/* Toolbar com filtros */}
      <Toolbar
        left={
          <>
            <Select
              value={severityFilter}
              onChange={e => setSeverityFilter(e.target.value)}
              style={{ width: 140 }}
              placeholder="Todas severidades"
              options={[
                { value: "all", label: "Todas severidades" },
                { value: "critical", label: "Crítica" },
                { value: "high", label: "Alta" },
                { value: "medium", label: "Média" },
                { low: "low", label: "Baixa" },
              ]}
            />
            <Select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              style={{ width: 140, marginLeft: spacing["2"] }}
              placeholder="Todos status"
              options={[
                { value: "all", label: "Todos status" },
                { value: "open", label: "Aberto" },
                { value: "in_progress", label: "Em andamento" },
                { value: "resolved", label: "Resolvido" },
                { value: "closed", label: "Fechado" },
                { value: "false_positive", label: "Falso Positivo" },
              ]}
            />
            <Select
              value={sortBy}
              onChange={e => setSortBy(e.target.value as any)}
              style={{ width: 140, marginLeft: spacing["2"] }}
              placeholder="Ordenar por"
              options={[
                { value: "lastSeen", label: "Última ocorrência" },
                { value: "firstSeen", label: "Primeira ocorrência" },
                { value: "severity", label: "Severidade" },
                { value: "riskScore", label: "Risk Score" },
              ]}
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSortDir(prev => prev === "asc" ? "desc" : "asc")}
              title="Inverter ordem"
            >
              {sortDir === "asc" ? "↑" : "↓"}
            </Button>
          </>
        </div>
      </div>

      {/* Tabela de Alertas */}
      <div style={{ flex: 1, overflow: "auto", padding: spacing["4"] }}>
        <Card>
          <DataTable
            columns={[
              { key: "select", header: "", width: "48px", sortable: false },
              { key: "severity", header: "Severidade", width: "100px", sortable: true },
              { key: "title", header: "Título / Regra", sortable: true },
              { key: "sourceHost", header: "Origem", width: "140px", sortable: true },
              { key: "user", header: "Usuário", width: "120px", sortable: true },
              { key: "firstSeen", header: "Primeira vez", width: "140px", sortable: true },
              { key: "lastSeen", header: "Última vez", sortable: true },
              { key: "eventCount", header: "Eventos", width: "80px", sortable: true },
              { key: "riskScore", header: "Risk", width: "70px", sortable: true },
              { key: "status", header: "Status", width: "130px", sortable: true },
              { key: "actions", header: "", width: "100px", sortable: false },
            ]
            rows={filteredAlerts.map(alert => ({
              id: alert.id,
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
              firstSeen: new Date(alert.firstSeen).toLocaleString("pt-BR"),
              lastSeen: new Date(alert.lastSeen).toLocaleString("pt-BR"),
              eventCount: alert.eventCount,
              riskScore: (
                <span style={{ 
                  fontWeight: 600, 
                  color: alert.riskScore >= 80 ? colors.severity.critical : 
                           alert.riskScore >= 60 ? colors.severity.high : 
                           alert.riskScore >= 40 ? colors.severity.medium : colors.severity.low
                }}>
                  {alert.riskScore}
                </span>
              ),
              status: (
                <StatusBadge tone={alert.status as any}>
                  {alert.status.replace("_", " ").replace(/\b\w/g, c => c.toUpperCase())}
                </StatusBadge>
              ),
              actions: (
                <div style={{ display: "flex", gap: 4 }}>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => openDrawer(alert)}
                    title="Investigar"
                    title="Investigar"
                  >
                    <MagnifyingGlassIcon size={16} />
                  </Button>
                  <Dropdown
                    trigger={<Button size="sm" variant="ghost"><MoreHorizontalIcon size={16} /></Button>}
                    items={[
                      { label: "Investigar", onClick: () => openDrawer(alert) },
                      { label: "Atribuir a mim", onClick: () => {} },
                      { label: "Marcar como FP", onClick: () => {} },
                      { label: "Suprimir regra", onClick: () => {} },
                      { label: "Exportar", onClick: () => {} },
                      { label: "Excluir", variant: "destructive", onClick: () => {} },
                    ]}
                  />
                </Button>
              )},
            )}
            rows={filteredAlerts.map(alert => ({
              id: alert.id,
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
              firstSeen: new Date(alert.firstSeen).toLocaleString("pt-BR"),
              lastSeen: new Date(alert.lastSeen).toLocaleString("pt-BR"),
              eventCount: alert.eventCount,
              riskScore: (
                <span style={{ 
                  fontWeight: 600, 
                  color: alert.riskScore >= 80 ? colors.severity.critical : 
                           alert.riskScore >= 60 ? colors.severity.high : 
                           alert.riskScore >= 40 ? colors.severity.medium : colors.severity.low
                }}>
                  {alert.riskScore}
                </span>
              ),
              status: (
                <StatusBadge tone={alert.status as any}>
                  {alert.status.replace("_", " ").replace(/\b\w/g, c => c.toUpperCase())}
                </StatusBadge>
              ),
              actions: (
                <div style={{ display: "flex", gap: 4 }}>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => openDrawer(alert)}
                    aria-label="Investigar"
                  >
                    <SearchIcon size={16} />
                  </Button>
                  <Dropdown
                    trigger={<Button size="sm" variant="ghost"><MoreHorizontalIcon size={16} /></Button>}
                    items={[
                      { label: "Investigar", onClick: () => openDrawer(alert) },
                      { label: "Atribuir a mim", onClick: () => {} },
                      { label: "Marcar como FP", onClick: () => {} },
                      { label: "Suprimir regra", onClick: () => {} },
                      { label: "Exportar", onClick: () => {} },
                      { label: "Excluir", variant: "destructive", onClick: () => {} },
                    ]}
                  />
                </Button>
              )},
            )}
            rows={filteredAlerts}
            selectedKeys={selectedAlerts}
            onSelectionChange={setSelectedAlerts}
            sortKey={sortBy}
            sortDirection={sortDir}
            onSort={setSortBy}
            onSortDirectionChange={setSortDir}
            onRowClick={handleRowClick}
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
          title={`Alerta: ${selectedAlert?.title}`}
          width={900}
        >
          <AlertDetailView alert={selectedAlert} onClose={closeDrawer} />
        </Drawer>
      )}
    </div>
  );
}

// Mock data para demonstração
const ALERTS_MOCK = [
  {
    id: "ALT-20260804-001",
    ruleId: "brute-force-ssh",
    title: "Brute Force SSH - Múltiplas falhas",
    severity: "high" as const,
    status: "open",
    sourceHost: "web-01",
    user: "admin",
    firstSeen: new Date("2026-08-04T10:15:00"),
    lastSeen: new Date("2026-08-04T10:45:00"),
    fingerprintHash: "fp-abc123",
    eventCount: 47,
    mitre: ["T1110.001"],
    riskScore: 85,
  },
  // ... outros alertas mock
] as const;

export { AlertCenterPage };