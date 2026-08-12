import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { apiClient } from "../api/client";
import { SeverityBadge } from "../design-system/components/badges";
import { Button } from "../design-system/components/Button";
import { EmptyState, LoadingSkeleton } from "../design-system/components/feedback";
import { colors, radii, spacing, typography } from "../design-system/tokens";
import type { SeverityColor } from "../design-system/tokens/colors";

interface ShieldSource {
  product: string;
  product_version: string;
  component: string;
  instance_id: string;
}

interface ShieldAsset {
  asset_id: string;
  hostname: string;
  ip?: string;
  os?: string;
}

interface LinkedCase {
  case_id: string;
  title: string;
  status: string;
  owner?: string | null;
  evidence_count: number;
  sla?: {
    state: "ok" | "warning" | "overdue" | "met" | "missed";
    deadline: string;
    remaining_seconds?: number;
  };
}

interface MitreMapping {
  technique_id: string;
  name?: string;
  tactic?: string;
  source: string;
}

interface EntityContext {
  inventory_status: "registered" | "not_registered";
  inventory: {
    hostname: string;
    ip: string;
    os: string;
    criticality: string;
    owner: string;
    status: string;
    last_seen: string;
  } | null;
  related_incidents: number;
  related_cases: number;
  related_file?: string | null;
}

interface ShieldInvestigation {
  event_id: string;
  schema_version: string;
  timestamp: string;
  received_at: string;
  processing_status: string;
  sequence: number;
  event_type: string;
  severity: SeverityColor;
  source: ShieldSource;
  asset: ShieldAsset;
  evidence: Record<string, unknown>;
  metadata: Record<string, unknown>;
  mitre?: MitreMapping[];
  entity?: EntityContext;
  normalized: Record<string, unknown>;
  case: LinkedCase | null;
  case_created?: boolean;
}

type ViewState = "loading" | "ready" | "invalid" | "not-ingested" | "wrong-source" | "error";

const UUID4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const CURRENT_ANALYST = "analista.soc";
const EVENT_LABELS: Record<string, string> = {
  "shield.fim.baseline.created": "Baseline criada",
  "shield.fim.file.added": "Novo arquivo detectado",
  "shield.fim.file.modified": "Arquivo modificado",
  "shield.fim.file.removed": "Arquivo removido",
  "shield.hash.mismatch": "Hash divergente",
  "shield.fim.scan.completed": "Varredura FIM concluída",
  "shield.alert.created": "Alerta de segurança criado",
  "shield.alert.updated": "Alerta de segurança atualizado",
};

function asText(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function formatTime(value?: string): string {
  if (!value) return "Sem marca temporal adicional";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "medium" });
}

function DataRow({ label, value, mono = false }: { label: string; value: unknown; mono?: boolean }) {
  const text = value === undefined || value === null || value === "" ? "Não informado" : String(value);
  return <div className="shield-data-row"><span>{label}</span><strong className={mono ? "mono" : ""} title={text}>{text}</strong></div>;
}

function slaLabel(sla?: LinkedCase["sla"]): string {
  if (!sla) return "SLA indisponível";
  if (sla.state === "overdue" || sla.state === "missed") return "SLA vencido";
  if (sla.state === "warning") return "SLA próximo";
  if (sla.state === "met") return "SLA atendido";
  return "Dentro do SLA";
}

function slaDetail(sla?: LinkedCase["sla"]): string {
  if (!sla?.deadline) return "Prazo não informado";
  const deadline = new Date(sla.deadline).getTime();
  if (Number.isNaN(deadline)) return "Prazo não informado";
  const totalMinutes = Math.max(0, Math.floor(Math.abs(deadline - Date.now()) / 60000));
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  const duration = hours ? `${hours}h ${minutes}min` : `${minutes}min`;
  return deadline < Date.now() ? `Vencido há ${duration}` : `Vence em ${duration}`;
}

function processingLabel(value: string): string {
  return value === "pending" ? "Recebido · pendente" : value === "processed" ? "Processado" : value;
}

function caseStatusLabel(value: string): string {
  return value === "open" ? "Aberto" : value === "in_progress" ? "Em tratamento" : value === "on_hold" ? "Em espera" : value === "resolved" ? "Resolvido" : value === "closed" ? "Encerrado" : value;
}

function CopyButton({ value, copied, onCopy }: { value: string; copied: boolean; onCopy: (value: string) => void }) {
  return <button type="button" className="shield-copy" aria-label="Copiar hash" onClick={() => onCopy(value)}>{copied ? "Copiado" : "Copiar"}</button>;
}

function Panel({ title, eyebrow, children }: { title: string; eyebrow?: string; children: React.ReactNode }) {
  return <section className="shield-panel">
    <header>{eyebrow && <span>{eyebrow}</span>}<h2>{title}</h2></header>
    <div className="shield-panel-body">{children}</div>
  </section>;
}

export function ShieldEventInvestigationPage() {
  const { eventId = "" } = useParams();
  const navigate = useNavigate();
  const [viewState, setViewState] = useState<ViewState>(UUID4.test(eventId) ? "loading" : "invalid");
  const [data, setData] = useState<ShieldInvestigation | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [creatingCase, setCreatingCase] = useState(false);
  const [assigningCase, setAssigningCase] = useState(false);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  const load = useCallback(async (signal?: AbortSignal) => {
    if (!UUID4.test(eventId)) {
      setViewState("invalid");
      return;
    }
    setViewState("loading");
    setErrorMessage("");
    const response = await apiClient.get<ShieldInvestigation>(
      `/investigation/sources/edy-shield/events/${encodeURIComponent(eventId)}`,
      { signal },
    );
    if (signal?.aborted) return;
    if (response.success && response.data) {
      if (response.data.source?.product !== "edy-shield") {
        setViewState("wrong-source");
        return;
      }
      setData(response.data);
      setViewState("ready");
      return;
    }
    if (response.error?.code === "wrong_source") {
      setViewState("wrong-source");
      return;
    }
    if (response.error?.code === "shield_event_not_found" || response.error?.status === 404) {
      setViewState("not-ingested");
      return;
    }
    if (response.error?.code === "invalid_event_id" || response.error?.status === 422) {
      setViewState("invalid");
      return;
    }
    setErrorMessage("A consulta falhou temporariamente. Nenhum dado parcial foi exibido.");
    setViewState("error");
  }, [eventId]);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const createCase = async () => {
    if (!data || creatingCase || data.case) return;
    setCreatingCase(true);
    const response = await apiClient.post<ShieldInvestigation>(
      `/investigation/sources/edy-shield/events/${encodeURIComponent(eventId)}/cases`,
    );
    setCreatingCase(false);
    if (response.success && response.data) {
      setData(response.data);
      return;
    }
    setErrorMessage("Não foi possível criar o caso. Tente novamente sem recarregar o evento.");
  };

  const assumeCase = async () => {
    if (!data?.case || data.case.owner || assigningCase) return;
    setAssigningCase(true);
    setErrorMessage("");
    const response = await apiClient.post(
      `/soc/cases/${encodeURIComponent(data.case.case_id)}/assign?${new URLSearchParams({ owner: CURRENT_ANALYST }).toString()}`,
    );
    if (response.success) await load();
    else setErrorMessage("Não foi possível assumir o caso. Tente novamente.");
    setAssigningCase(false);
  };

  const copyHash = useCallback(async (value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopiedHash(value);
      window.setTimeout(() => setCopiedHash((current) => current === value ? null : current), 1600);
    } catch {
      setErrorMessage("Não foi possível copiar o hash neste navegador.");
    }
  }, []);

  if (viewState === "loading") {
    return <div className="shield-investigation-state"><LoadingSkeleton rows={4} variant="card" /></div>;
  }
  if (viewState !== "ready" || !data) {
    const stateContent: Partial<Record<ViewState, [string, string]>> = {
      invalid: ["Acesso inválido", "O link não contém um identificador UUIDv4 válido."],
      "not-ingested": ["Evento ainda não ingerido", "O Shield pode estar com o envio pendente. Aguarde a entrega e tente novamente."],
      "wrong-source": ["Origem incompatível", "O evento encontrado não pertence ao EDY Shield."],
      error: ["API de investigação indisponível", errorMessage || "Tente novamente em alguns instantes."],
    };
    const content = stateContent[viewState] ?? ["Investigação indisponível", "Não foi possível abrir este evento."];
    return <div className="shield-investigation-state"><EmptyState title={content[0]} description={content[1]} action={
      <div style={{ display: "flex", gap: spacing["2"] }}>
        {viewState !== "invalid" && <Button variant="secondary" onClick={() => void load()}>Tentar novamente</Button>}
        <Button variant="ghost" onClick={() => navigate("/investigate")}>Ir para Investigações</Button>
      </div>
    } /></div>;
  }

  const filePath = asText(data.evidence.file_path);
  const previousHash = asText(data.evidence.previous_hash);
  const currentHash = asText(data.evidence.current_hash);
  const baselineStatus = asText(data.evidence.baseline_status);
  const baselineId = asText(data.evidence.baseline_id);
  const scanId = asText(data.evidence.scan_id);
  const hashAlgorithm = asText(data.evidence.hash_algorithm);
  const fileSize = typeof data.evidence.file_size_bytes === "number" ? `${data.evidence.file_size_bytes.toLocaleString("pt-BR")} bytes` : null;
  const fileMtime = asText(data.evidence.mtime);
  const evidenceDetails = data.evidence.details && typeof data.evidence.details === "object" ? data.evidence.details as Record<string, unknown> : {};
  const changeSummary = asText(evidenceDetails.description) || asText(data.evidence.change);
  const title = EVENT_LABELS[data.event_type] || data.event_type;
  const mitre = data.mitre ?? [];
  const entity = data.entity ?? {
    inventory_status: "not_registered" as const,
    inventory: null,
    related_incidents: 0,
    related_cases: data.case ? 1 : 0,
    related_file: filePath,
  };
  const timeline = [
    { title: "Shield registrou o evento", time: data.timestamp, detail: `${title} · sequência ${data.sequence}` },
    { title: "SIEM recebeu o evento", time: data.received_at, detail: "Persistido de forma idempotente no inbox" },
    { title: "Estado atual", time: "", detail: data.processing_status === "pending" ? "Recebido · aguardando correlação downstream" : data.processing_status },
  ];

  return <div className="shield-investigation-page">
    <header className="shield-investigation-hero">
      <div className="shield-provenance"><span className="shield-source-mark">S</span><span>EDY Shield</span><i aria-hidden="true" /> <span>Ingestão v{data.schema_version}</span><i aria-hidden="true" /> <span className="mono">{data.event_id}</span></div>
      <div className="shield-title-row"><div><p>ALERTA · INVESTIGAÇÃO DE ENDPOINT</p><h1>{title}</h1><span>{filePath || "Evento de endpoint sem caminho de arquivo"}</span></div><SeverityBadge severity={data.severity}>{data.severity}</SeverityBadge></div>
      <div className="shield-operational-strip" aria-label="Contexto operacional">
        <div><span>Ativo</span><strong>{data.asset.hostname}</strong></div>
        <div><span>Ocorrido</span><strong>{formatTime(data.timestamp)}</strong></div>
        <div><span>Recebido no SIEM</span><strong>{formatTime(data.received_at)}</strong></div>
        <div><span>Estado</span><strong>{processingLabel(data.processing_status)}</strong></div>
        <div><span>Responsável</span><strong>{data.case?.owner || "Não atribuído"}</strong></div>
        <div><span>SLA</span><strong>{data.case ? slaLabel(data.case.sla) : "Inicia ao criar caso"}</strong></div>
      </div>
    </header>

    <div className="shield-investigation-layout">
      <main className="shield-investigation-main">
        <Panel eyebrow="EVIDÊNCIA" title={filePath ? "Mudança e integridade do arquivo" : "Contexto recebido do endpoint"}>
          {filePath ? <div className="shield-file-path"><span>ARQUIVO AFETADO</span><code>{filePath}</code></div> : <div className="shield-evidence-empty"><strong>Sem evidência de arquivo neste evento</strong><p>O Shield não informou caminho ou hash para este tipo de telemetria. A origem, o ativo e a cadeia de recebimento permanecem disponíveis.</p></div>}
          {(previousHash || currentHash) && <div className="shield-hash-compare">
            <div><div className="shield-hash-label"><span>HASH ANTERIOR</span>{previousHash && <CopyButton value={previousHash} copied={copiedHash === previousHash} onCopy={(value) => void copyHash(value)} />}</div><code>{previousHash || "Não informado pelo evento"}</code></div>
            <span className="shield-hash-arrow" aria-hidden="true">→</span>
            <div><div className="shield-hash-label"><span>HASH ATUAL</span>{currentHash && <CopyButton value={currentHash} copied={copiedHash === currentHash} onCopy={(value) => void copyHash(value)} />}</div><code>{currentHash || "Não informado pelo evento"}</code></div>
          </div>}
          {changeSummary && <div className="shield-change-summary"><span>MUDANÇA REGISTRADA</span><p>{changeSummary}</p></div>}
          <div className="shield-data-grid">
            <DataRow label="Algoritmo" value={hashAlgorithm} mono />
            <DataRow label="Baseline" value={baselineStatus} />
            <DataRow label="Baseline ID" value={baselineId} mono />
            <DataRow label="Scan relacionado" value={scanId} mono />
            <DataRow label="Tamanho" value={fileSize} mono />
            <DataRow label="Última modificação" value={fileMtime ? formatTime(fileMtime) : null} />
          </div>
        </Panel>

        <Panel eyebrow="CADEIA DE CUSTÓDIA" title="Timeline do evento">
          <div className="shield-timeline">{timeline.map((item, index) => <div key={item.title} className="shield-timeline-item">
            <span className="shield-timeline-dot" /><div><strong>{item.title}</strong><p>{item.detail}</p>{item.time && <time>{formatTime(item.time)}</time>}</div>{index < timeline.length - 1 && <i aria-hidden="true" />}
          </div>)}</div>
        </Panel>

        <Panel eyebrow="CONTEXTO RECEBIDO" title="Metadados e normalização">
          <details className="shield-json"><summary>Visualizar metadados técnicos</summary><pre>{JSON.stringify({ metadata: data.metadata, normalized: data.normalized }, null, 2)}</pre></details>
        </Panel>
      </main>

      <aside className="shield-investigation-aside">
        <Panel eyebrow="ENTIDADE · ENDPOINT" title={data.asset.hostname}>
          <div className="shield-entity-source"><span className="shield-source-mark">S</span><div><strong>EDY Shield</strong><span>{data.source.component} · versão {data.source.product_version}</span></div></div>
          <DataRow label="Asset ID" value={data.asset.asset_id} mono />
          <DataRow label="IP" value={data.asset.ip} mono />
          <DataRow label="Sistema" value={data.asset.os} />
          <DataRow label="Inventário SIEM" value={entity.inventory_status === "registered" ? "Ativo registrado" : "Ainda não registrado"} />
          {entity.inventory && <><DataRow label="Criticidade" value={entity.inventory.criticality} /><DataRow label="Estado inventário" value={entity.inventory.status} /><DataRow label="Última observação" value={formatTime(entity.inventory.last_seen)} /></>}
          <div className="shield-entity-relations"><span>{entity.related_incidents} incidente(s)</span><span>{entity.related_cases} caso(s)</span></div>
        </Panel>
        <Panel eyebrow="MITRE ATT&CK" title="Associação técnica">
          {mitre.length ? <div className="shield-mitre-list">{mitre.map((mapping) => <article key={mapping.technique_id}><code>{mapping.technique_id}</code>{mapping.name && <strong>{mapping.name}</strong>}{mapping.tactic && <span>Tática · {mapping.tactic}</span>}<small>Origem · {mapping.source}</small></article>)}</div> : <p className="shield-muted">Técnica MITRE ainda não associada a este evento.</p>}
        </Panel>
        <Panel eyebrow="DECISÃO" title="Próxima decisão">
          {data.case ? <div className="shield-case-linked"><span>CASO VINCULADO</span><strong>{data.case.title}</strong><code>{data.case.case_id}</code><div className="shield-decision-status"><div><span>Responsável</span><strong>{data.case.owner || "Sem responsável"}</strong></div><div className={`sla-${data.case.sla?.state || "none"}`}><span>{slaLabel(data.case.sla)}</span><strong>{slaDetail(data.case.sla)}</strong></div></div><div className="shield-case-facts"><DataRow label="Status" value={caseStatusLabel(data.case.status)} /><DataRow label="Prazo" value={data.case.sla?.deadline ? formatTime(data.case.sla.deadline) : null} /><DataRow label="Evidências" value={data.case.evidence_count} /></div><div className="shield-decision-actions">{!data.case.owner && <Button disabled={assigningCase} onClick={() => void assumeCase()}>{assigningCase ? "Assumindo…" : "Assumir"}</Button>}<Button variant={data.case.owner ? "primary" : "secondary"} onClick={() => navigate(`/investigate?case=${encodeURIComponent(data.case!.case_id)}`)}>Continuar investigação</Button><Button variant="ghost" onClick={() => navigate(`/cases?case=${encodeURIComponent(data.case!.case_id)}`)}>Abrir caso existente</Button></div></div> : <div className="shield-decision-copy"><p>Revise a evidência acima e crie um caso rastreável quando a mudança exigir tratamento operacional.</p><div className="shield-decision-actions"><Button disabled={creatingCase} onClick={() => void createCase()}>{creatingCase ? "Criando caso…" : "Criar caso"}</Button><Button variant="ghost" onClick={() => document.querySelector(".shield-investigation-main")?.scrollIntoView({ behavior: "smooth", block: "start" })}>Revisar evidência</Button></div></div>}
          {errorMessage && <p role="alert" className="shield-inline-error">{errorMessage}</p>}
        </Panel>
      </aside>
    </div>

    <style>{`
      .shield-investigation-page{max-width:1500px;margin:0 auto;color:${colors.textPrimary}}
      .shield-investigation-state{max-width:920px;margin:40px auto;padding:${spacing["5"]};border:1px solid ${colors.border};border-radius:${radii.xl};background:${colors.surface}}
      .shield-investigation-hero{padding:20px 22px;border:1px solid ${colors.border};border-radius:${radii.xl};background:linear-gradient(125deg,color-mix(in srgb,${colors.accent} 10%,${colors.surface}),${colors.surface} 58%);box-shadow:0 18px 42px color-mix(in srgb,${colors.textPrimary} 7%,transparent)}
      .shield-provenance{display:flex;align-items:center;gap:9px;color:${colors.textMuted};font-size:11px;min-width:0}.shield-provenance i{width:3px;height:3px;border-radius:50%;background:${colors.border}}.shield-provenance .mono{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
      .shield-source-mark{display:grid;place-items:center;width:22px;height:22px;border-radius:6px;background:${colors.accent};color:${colors.textOnAccent};font-weight:800}
      .shield-title-row{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;margin-top:18px}.shield-title-row p{margin:0 0 7px;color:${colors.accentHover};font-size:10px;font-weight:700;letter-spacing:.16em}.shield-title-row h1{margin:0;color:${colors.textPrimary};font-size:clamp(24px,3vw,38px);letter-spacing:-.035em}.shield-title-row div>span{display:block;max-width:900px;margin-top:8px;color:${colors.textMuted};font:12px ${typography.family.mono};overflow-wrap:anywhere}
      .shield-operational-strip{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:0;margin-top:18px;border-top:1px solid ${colors.borderSubtle}}.shield-operational-strip>div{min-width:0;padding:13px 12px 0;border-left:1px solid ${colors.borderSubtle}}.shield-operational-strip>div:first-child{padding-left:0;border-left:0}.shield-operational-strip span{display:block;color:${colors.textMuted};font-size:9px;font-weight:700;letter-spacing:.1em;text-transform:uppercase}.shield-operational-strip strong{display:block;margin-top:5px;color:${colors.textSecondary};font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
      .shield-investigation-layout{display:grid;grid-template-columns:minmax(0,1fr) 350px;gap:16px;margin-top:16px}.shield-investigation-main,.shield-investigation-aside{display:flex;flex-direction:column;gap:16px;min-width:0}.shield-investigation-aside{align-self:start;position:sticky;top:16px}
      .shield-panel{overflow:hidden;border:1px solid ${colors.border};border-radius:${radii.lg};background:${colors.surface}}.shield-panel>header{padding:14px 16px;border-bottom:1px solid ${colors.borderSubtle};background:color-mix(in srgb,${colors.surfaceAlt} 52%,${colors.surface})}.shield-panel>header span{display:block;color:${colors.accentHover};font-size:9px;font-weight:700;letter-spacing:.15em}.shield-panel>header h2{margin:5px 0 0;font-size:15px;letter-spacing:-.01em}.shield-panel-body{padding:16px}
      .shield-file-path{padding:14px;border-left:3px solid ${colors.accent};border-radius:0 ${radii.md} ${radii.md} 0;background:${colors.surfaceAlt}}.shield-file-path span,.shield-hash-compare span,.shield-case-linked>span,.shield-change-summary span{display:block;color:${colors.textMuted};font-size:9px;font-weight:700;letter-spacing:.12em}.shield-file-path code{display:block;margin-top:7px;color:${colors.textPrimary};font-size:12px;overflow-wrap:anywhere}
      .shield-hash-compare{display:grid;grid-template-columns:minmax(0,1fr) 20px minmax(0,1fr);align-items:stretch;gap:10px;margin-top:12px}.shield-hash-compare>div{min-width:0;padding:12px;border:1px solid ${colors.borderSubtle};border-radius:${radii.md};background:${colors.background}}.shield-hash-arrow{display:grid!important;place-items:center;color:${colors.accent}!important;font-size:18px!important}.shield-hash-label{display:flex;align-items:center;justify-content:space-between;gap:10px}.shield-hash-compare code{display:block;margin-top:9px;color:${colors.textSecondary};font-size:10px;line-height:1.55;overflow-wrap:anywhere;word-break:break-all}.shield-copy{padding:3px 7px;border:1px solid ${colors.border};border-radius:5px;background:transparent;color:${colors.accentHover};font-size:9px;cursor:pointer}.shield-copy:hover,.shield-copy:focus-visible{border-color:${colors.accent};outline:none}.shield-change-summary{margin-top:12px;padding:11px 12px;border:1px solid ${colors.borderSubtle};border-radius:${radii.md};background:color-mix(in srgb,${colors.accent} 5%,${colors.surfaceAlt})}.shield-change-summary p,.shield-evidence-empty p{margin:6px 0 0;color:${colors.textSecondary};font-size:11px;line-height:1.55}.shield-evidence-empty{padding:14px;border:1px dashed ${colors.border};border-radius:${radii.md};background:${colors.surfaceAlt}}.shield-evidence-empty strong{font-size:12px}
      .shield-data-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 18px;margin-top:14px}.shield-data-row{display:grid;grid-template-columns:minmax(90px,.6fr) minmax(0,1fr);gap:10px;padding:9px 0;border-bottom:1px solid ${colors.borderSubtle};font-size:11px}.shield-data-row>span{color:${colors.textMuted}}.shield-data-row>strong{color:${colors.textSecondary};font-weight:600;text-align:right;overflow:hidden;text-overflow:ellipsis}.mono,code{font-family:${typography.family.mono}}
      .shield-timeline{padding-left:4px}.shield-timeline-item{position:relative;display:grid;grid-template-columns:16px minmax(0,1fr);gap:10px;min-height:80px}.shield-timeline-item>i{position:absolute;left:4px;top:15px;bottom:-2px;width:1px;background:${colors.border}}.shield-timeline-dot{position:relative;z-index:1;width:9px;height:9px;margin-top:3px;border-radius:50%;background:${colors.accent};box-shadow:0 0 0 4px color-mix(in srgb,${colors.accent} 13%,transparent)}.shield-timeline-item strong{font-size:12px}.shield-timeline-item p{margin:4px 0;color:${colors.textSecondary};font-size:11px}.shield-timeline-item time{color:${colors.textMuted};font:10px ${typography.family.mono}}
      .shield-json summary{cursor:pointer;color:${colors.textSecondary};font-size:12px}.shield-json pre{max-height:360px;overflow:auto;margin:12px 0 0;padding:14px;border-radius:${radii.md};background:${colors.background};color:${colors.textSecondary};font-size:10px;line-height:1.55;white-space:pre-wrap;overflow-wrap:anywhere}.shield-muted{margin:0;color:${colors.textMuted};font-size:12px;line-height:1.55}.shield-entity-source{display:flex;align-items:center;gap:10px;margin-bottom:10px;padding:10px;border:1px solid ${colors.borderSubtle};border-radius:${radii.md};background:${colors.surfaceAlt}}.shield-entity-source strong,.shield-entity-source span{display:block}.shield-entity-source strong{font-size:12px}.shield-entity-source span{margin-top:2px;color:${colors.textMuted};font-size:10px}.shield-entity-relations{display:flex;gap:7px;margin-top:10px}.shield-entity-relations span{padding:5px 7px;border-radius:5px;background:${colors.surfaceAlt};color:${colors.textMuted};font-size:10px}.shield-mitre-list{display:flex;flex-direction:column;gap:8px}.shield-mitre-list article{padding:10px;border:1px solid color-mix(in srgb,${colors.accent} 26%,${colors.border});border-radius:${radii.md};background:color-mix(in srgb,${colors.accent} 6%,${colors.surfaceAlt})}.shield-mitre-list code,.shield-mitre-list strong,.shield-mitre-list span,.shield-mitre-list small{display:block}.shield-mitre-list code{color:${colors.accentHover};font-size:12px}.shield-mitre-list strong{margin-top:5px;font-size:11px}.shield-mitre-list span{margin-top:3px;color:${colors.textSecondary};font-size:10px}.shield-mitre-list small{margin-top:7px;color:${colors.textMuted};font-size:9px}
      .shield-decision-copy p,.shield-case-linked p{margin:0 0 14px;color:${colors.textSecondary};font-size:12px;line-height:1.55}.shield-case-linked>strong,.shield-case-linked>code{display:block;margin-top:7px}.shield-case-linked>strong{font-size:13px}.shield-case-linked>code{color:${colors.textMuted};font-size:10px;overflow-wrap:anywhere}.shield-decision-status{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}.shield-decision-status>div{padding:9px;border:1px solid ${colors.borderSubtle};border-radius:${radii.md};background:${colors.surfaceAlt}}.shield-decision-status span,.shield-decision-status strong{display:block}.shield-decision-status span{color:${colors.textMuted};font-size:9px}.shield-decision-status strong{margin-top:4px;font-size:10px}.shield-decision-status .sla-overdue,.shield-decision-status .sla-missed{border-color:color-mix(in srgb,${colors.danger} 40%,${colors.border})}.shield-decision-status .sla-warning{border-color:color-mix(in srgb,${colors.severity.medium} 40%,${colors.border})}.shield-case-facts{margin:10px 0 14px}.shield-decision-actions{display:flex;flex-direction:column;gap:7px}.shield-decision-actions button{width:100%}.shield-inline-error{margin:10px 0 0;color:${colors.danger};font-size:11px}
      @media(max-width:1180px){.shield-operational-strip{grid-template-columns:repeat(3,minmax(0,1fr));row-gap:10px}.shield-operational-strip>div:nth-child(4){padding-left:0;border-left:0}.shield-investigation-layout{grid-template-columns:minmax(0,1fr) 320px}}
      @media(max-width:960px){.shield-investigation-layout{grid-template-columns:1fr}.shield-investigation-aside{position:static;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));align-items:start}.shield-investigation-aside .shield-panel:last-child{grid-column:1/-1}}
      @media(max-width:640px){.shield-investigation-page{margin:-4px}.shield-investigation-hero{padding:16px}.shield-title-row{align-items:flex-start}.shield-provenance i,.shield-provenance span:nth-of-type(3){display:none}.shield-operational-strip{grid-template-columns:repeat(2,minmax(0,1fr))}.shield-operational-strip>div:nth-child(odd){padding-left:0;border-left:0}.shield-operational-strip>div:nth-child(4){padding-left:12px;border-left:1px solid ${colors.borderSubtle}}.shield-investigation-aside{display:flex}.shield-data-grid{grid-template-columns:1fr}.shield-hash-compare{grid-template-columns:1fr}.shield-hash-arrow{transform:rotate(90deg);justify-self:center}.shield-data-row{grid-template-columns:1fr}.shield-data-row>strong{text-align:left;white-space:normal;overflow-wrap:anywhere}.shield-title-row h1{font-size:25px}}
      @media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
    `}</style>
  </div>;
}
