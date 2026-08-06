/**
 * Contexto operacional de um alerta.
 * As abas preservam a estrutura da investigação sem exibir eventos ou evidências simulados.
 */
import { useState } from "react";
import { colors, motion, radii, spacing, typography } from "../design-system/tokens";
import { Card } from "../design-system/components/primitives";
import { SeverityBadge, StatusBadge } from "../design-system/components/badges";
import { EmptyState } from "../design-system/components/feedback";

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

const detailLabelStyle = {
  display: "block",
  marginBottom: 3,
  color: colors.textMuted,
  fontSize: typography.size.xs,
  fontWeight: typography.weight.medium,
  letterSpacing: "0.06em",
  textTransform: "uppercase" as const,
};

function Detail({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return <div><span style={detailLabelStyle}>{label}</span><span style={{ color: colors.textPrimary, fontSize: typography.size.sm, fontFamily: mono ? typography.family.mono : typography.family.ui, overflowWrap: "anywhere" }}>{value || "Não informado"}</span></div>;
}

function SummaryTab({ alert }: AlertDetailViewProps) {
  return <div style={{ padding: spacing["4"], display: "flex", flexDirection: "column", gap: spacing["4"] }}>
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(132px, 1fr))", gap: spacing["3"] }}>
      <Card><span style={detailLabelStyle}>Score de risco</span><strong style={{ color: alert.riskScore >= 80 ? colors.severity.critical : colors.textPrimary, fontSize: "30px", lineHeight: 1 }}>{alert.riskScore}</strong><span style={{ display: "block", marginTop: 7, color: colors.textMuted, fontSize: typography.size.xs }}>Priorização do alerta</span></Card>
      <Card><span style={detailLabelStyle}>Eventos</span><strong style={{ color: colors.textPrimary, fontSize: "30px", lineHeight: 1 }}>{alert.eventCount}</strong><span style={{ display: "block", marginTop: 7, color: colors.textMuted, fontSize: typography.size.xs }}>Eventos correlacionados</span></Card>
      <Card><span style={detailLabelStyle}>Severidade</span><div style={{ marginTop: 3 }}><SeverityBadge severity={alert.severity}>{alert.severity}</SeverityBadge></div><span style={{ display: "block", marginTop: 10, color: colors.textMuted, fontSize: typography.size.xs }}>Classificação da regra</span></Card>
      <Card><span style={detailLabelStyle}>Status</span><div style={{ marginTop: 3 }}><StatusBadge tone={alert.status.toLowerCase().includes("close") ? "online" : "neutral"}>{alert.status}</StatusBadge></div><span style={{ display: "block", marginTop: 10, color: colors.textMuted, fontSize: typography.size.xs }}>Estado operacional atual</span></Card>
    </div>

    <Card title="Contexto observado">
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: `${spacing["4"]} ${spacing["5"]}` }}>
        <Detail label="Host de origem" value={alert.sourceHost} mono />
        <Detail label="Usuário" value={alert.user || "Não informado"} />
        <Detail label="Regra" value={alert.ruleId} mono />
        <Detail label="Fingerprint" value={alert.fingerprintHash} mono />
        <Detail label="Primeira ocorrência" value={alert.firstSeen} mono />
        <Detail label="Última ocorrência" value={alert.lastSeen} mono />
      </div>
    </Card>

    <Card title="MITRE ATT&CK">
      {alert.mitre.length ? <div style={{ display: "flex", flexWrap: "wrap", gap: spacing["2"] }}>{alert.mitre.map((technique) => <span key={technique} style={{ border: `1px solid ${colors.border}`, borderRadius: radii.full, background: colors.surfaceAlt, color: colors.textSecondary, padding: "5px 9px", fontFamily: typography.family.mono, fontSize: typography.size.xs }}>{technique}</span>)}</div> : <span style={{ color: colors.textMuted, fontSize: typography.size.sm }}>Nenhuma técnica associada a este alerta.</span>}
    </Card>
  </div>;
}

function PendingData({ title, description }: { title: string; description: string }) {
  return <div style={{ padding: spacing["5"] }}><EmptyState title={title} description={description} compact /></div>;
}

export function AlertDetailView({ alert }: AlertDetailViewProps) {
  const [activeTab, setActiveTab] = useState("summary");
  const tabs = [
    { id: "summary", label: "Resumo" },
    { id: "events", label: "Eventos" },
    { id: "evidence", label: "Evidências" },
    { id: "related", label: "Relacionados" },
    { id: "timeline", label: "Linha do tempo" },
  ];

  return <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
    <div role="tablist" aria-label="Contexto do alerta" style={{ display: "flex", overflowX: "auto", borderBottom: `1px solid ${colors.border}`, padding: `0 ${spacing["3"]}` }}>
      {tabs.map((tab) => {
        const active = tab.id === activeTab;
        return <button key={tab.id} type="button" role="tab" aria-selected={active} onClick={() => setActiveTab(tab.id)} style={{ flex: "0 0 auto", padding: `${spacing["3"]} ${spacing["3"]}`, border: "none", borderBottom: active ? `2px solid ${colors.accent}` : "2px solid transparent", background: "transparent", color: active ? colors.textPrimary : colors.textMuted, cursor: "pointer", fontSize: typography.size.sm, fontWeight: active ? typography.weight.semibold : typography.weight.regular, transition: motion.transition.fast }}>{tab.label}</button>;
      })}
    </div>
    <div style={{ flex: 1, minHeight: 0, overflow: "auto" }}>
      {activeTab === "summary" && <SummaryTab alert={alert} />}
      {activeTab === "events" && <PendingData title="Eventos detalhados indisponíveis" description="A consulta de eventos vinculados a este alerta ainda não está disponível no contrato da API." />}
      {activeTab === "evidence" && <PendingData title="Sem evidências detalhadas" description="Hashes, IPs, domínios e processos serão exibidos quando o endpoint de evidências estiver disponível." />}
      {activeTab === "related" && <PendingData title="Correlação indisponível" description="Alertas relacionados aparecerão aqui quando a API fornecer relações de correlação." />}
      {activeTab === "timeline" && <PendingData title="Linha do tempo indisponível" description="Alterações de status e anotações serão exibidas quando houver histórico operacional persistido." />}
    </div>
  </div>;
}