import { useCallback, useEffect, useMemo, useState } from "react";
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
  normalized: Record<string, unknown>;
  case: LinkedCase | null;
  case_created?: boolean;
}

type ViewState = "loading" | "ready" | "invalid" | "not-ingested" | "wrong-source" | "error";

const UUID4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
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

function hashPreview(value: string): string {
  return value.length > 24 ? `${value.slice(0, 12)}…${value.slice(-10)}` : value;
}

function DataRow({ label, value, mono = false }: { label: string; value: unknown; mono?: boolean }) {
  const text = value === undefined || value === null || value === "" ? "Não informado" : String(value);
  return <div className="shield-data-row"><span>{label}</span><strong className={mono ? "mono" : ""} title={text}>{text}</strong></div>;
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
    if (response.error?.status === 404) {
      setViewState("not-ingested");
      return;
    }
    if (response.error?.status === 422) {
      setViewState("invalid");
      return;
    }
    setErrorMessage(response.error?.message || "Não foi possível consultar o evento.");
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
    setErrorMessage(response.error?.message || "Não foi possível criar o caso.");
  };

  const mitre = useMemo(() => {
    if (!data) return [];
    const raw = data.metadata.x_mitre ?? data.metadata.mitre ?? data.metadata.mitre_attack;
    if (Array.isArray(raw)) return raw.filter((value): value is string => typeof value === "string");
    return typeof raw === "string" && raw.trim() ? [raw] : [];
  }, [data]);

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
  const title = EVENT_LABELS[data.event_type] || data.event_type;
  const timeline = [
    { title: "Evento observado no endpoint", time: data.timestamp, detail: title },
    { title: "Shield registrou a telemetria", time: data.timestamp, detail: `Sequência ${data.sequence} · ${data.source.component}` },
    { title: "SIEM recebeu o evento", time: data.received_at, detail: "Persistido de forma idempotente no inbox" },
    { title: "Estado atual", time: "", detail: data.processing_status === "pending" ? "Recebido · aguardando correlação downstream" : data.processing_status },
  ];

  return <div className="shield-investigation-page">
    <header className="shield-investigation-hero">
      <div className="shield-provenance"><span className="shield-source-mark">S</span><span>EDY Shield</span><i aria-hidden="true" /> <span>Ingestão v{data.schema_version}</span><i aria-hidden="true" /> <span className="mono">{data.event_id}</span></div>
      <div className="shield-title-row"><div><p>INVESTIGAÇÃO DE ENDPOINT</p><h1>{title}</h1><span>{data.asset.hostname} · {formatTime(data.timestamp)}</span></div><SeverityBadge severity={data.severity}>{data.severity}</SeverityBadge></div>
    </header>

    <div className="shield-investigation-layout">
      <main className="shield-investigation-main">
        <Panel eyebrow="EVIDÊNCIA PRIMÁRIA" title="Integridade e contexto do arquivo">
          {filePath ? <div className="shield-file-path"><span>CAMINHO LÓGICO</span><code>{filePath}</code></div> : <p className="shield-muted">Este tipo de evento não possui caminho de arquivo.</p>}
          {(previousHash || currentHash) && <div className="shield-hash-compare">
            <div><span>HASH ANTERIOR</span><code title={previousHash || "Não informado"}>{previousHash ? hashPreview(previousHash) : "Não informado"}</code></div>
            <span aria-hidden="true">→</span>
            <div><span>HASH ATUAL</span><code title={currentHash || "Não informado"}>{currentHash ? hashPreview(currentHash) : "Não informado"}</code></div>
          </div>}
          <div className="shield-data-grid">
            <DataRow label="Baseline" value={baselineStatus} />
            <DataRow label="Tipo" value={data.event_type} mono />
            <DataRow label="Status SIEM" value={data.processing_status} />
            <DataRow label="Componente" value={data.source.component} />
          </div>
        </Panel>

        <Panel eyebrow="CADEIA DE CUSTÓDIA" title="Timeline do evento">
          <div className="shield-timeline">{timeline.map((item, index) => <div key={item.title} className="shield-timeline-item">
            <span className="shield-timeline-dot" /><div><strong>{item.title}</strong><p>{item.detail}</p><time>{formatTime(item.time)}</time></div>{index < timeline.length - 1 && <i aria-hidden="true" />}
          </div>)}</div>
        </Panel>

        <Panel eyebrow="CONTEXTO RECEBIDO" title="Metadados e normalização">
          <details className="shield-json"><summary>Visualizar metadados técnicos</summary><pre>{JSON.stringify({ metadata: data.metadata, normalized: data.normalized }, null, 2)}</pre></details>
        </Panel>
      </main>

      <aside className="shield-investigation-aside">
        <Panel eyebrow="ATIVO" title={data.asset.hostname}>
          <DataRow label="Asset ID" value={data.asset.asset_id} mono />
          <DataRow label="IP" value={data.asset.ip} mono />
          <DataRow label="Sistema" value={data.asset.os} />
          <DataRow label="Instância Shield" value={data.source.instance_id} mono />
        </Panel>
        <Panel eyebrow="MITRE ATT&CK" title="Associação técnica">
          {mitre.length ? <div className="shield-mitre-list">{mitre.map((value) => <span key={value}>{value}</span>)}</div> : <p className="shield-muted">Técnica MITRE ainda não associada a este evento.</p>}
        </Panel>
        <Panel eyebrow="DECISÃO" title="Próxima ação">
          {data.case ? <div className="shield-case-linked"><span>CASO VINCULADO</span><strong>{data.case.title}</strong><code>{data.case.case_id}</code><p>Status: {data.case.status} · {data.case.evidence_count} evidência(s)</p><Button onClick={() => navigate("/cases")}>Abrir Central de Casos</Button></div> : <div className="shield-decision-copy"><p>Transforme este evento e seu payload original em um caso rastreável no SIEM.</p><Button disabled={creatingCase} onClick={() => void createCase()}>{creatingCase ? "Criando caso…" : "Criar caso a partir deste evento"}</Button></div>}
          {errorMessage && <p role="alert" className="shield-inline-error">{errorMessage}</p>}
        </Panel>
      </aside>
    </div>

    <style>{`
      .shield-investigation-page{max-width:1440px;margin:0 auto;color:${colors.textPrimary}}
      .shield-investigation-state{max-width:920px;margin:40px auto;padding:${spacing["5"]};border:1px solid ${colors.border};border-radius:${radii.xl};background:${colors.surface}}
      .shield-investigation-hero{padding:20px 22px;border:1px solid ${colors.border};border-radius:${radii.xl};background:linear-gradient(125deg,color-mix(in srgb,${colors.accent} 10%,${colors.surface}),${colors.surface} 58%);box-shadow:0 18px 42px color-mix(in srgb,${colors.textPrimary} 7%,transparent)}
      .shield-provenance{display:flex;align-items:center;gap:9px;color:${colors.textMuted};font-size:11px;min-width:0}.shield-provenance i{width:3px;height:3px;border-radius:50%;background:${colors.border}}.shield-provenance .mono{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
      .shield-source-mark{display:grid;place-items:center;width:22px;height:22px;border-radius:6px;background:${colors.accent};color:${colors.textOnAccent};font-weight:800}
      .shield-title-row{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;margin-top:18px}.shield-title-row p{margin:0 0 7px;color:${colors.accentHover};font-size:10px;font-weight:700;letter-spacing:.16em}.shield-title-row h1{margin:0;color:${colors.textPrimary};font-size:clamp(24px,3vw,38px);letter-spacing:-.035em}.shield-title-row div>span{display:block;margin-top:8px;color:${colors.textMuted};font-size:13px}
      .shield-investigation-layout{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:16px;margin-top:16px}.shield-investigation-main,.shield-investigation-aside{display:flex;flex-direction:column;gap:16px;min-width:0}
      .shield-panel{overflow:hidden;border:1px solid ${colors.border};border-radius:${radii.lg};background:${colors.surface}}.shield-panel>header{padding:14px 16px;border-bottom:1px solid ${colors.borderSubtle};background:color-mix(in srgb,${colors.surfaceAlt} 52%,${colors.surface})}.shield-panel>header span{display:block;color:${colors.accentHover};font-size:9px;font-weight:700;letter-spacing:.15em}.shield-panel>header h2{margin:5px 0 0;font-size:15px;letter-spacing:-.01em}.shield-panel-body{padding:16px}
      .shield-file-path{padding:14px;border-left:3px solid ${colors.accent};border-radius:0 ${radii.md} ${radii.md} 0;background:${colors.surfaceAlt}}.shield-file-path span,.shield-hash-compare span,.shield-case-linked>span{display:block;color:${colors.textMuted};font-size:9px;font-weight:700;letter-spacing:.12em}.shield-file-path code{display:block;margin-top:7px;color:${colors.textPrimary};font-size:12px;overflow-wrap:anywhere}
      .shield-hash-compare{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);align-items:center;gap:12px;margin-top:12px}.shield-hash-compare>div{min-width:0;padding:12px;border:1px solid ${colors.borderSubtle};border-radius:${radii.md};background:${colors.background}}.shield-hash-compare>span{font-size:18px;color:${colors.accent}}.shield-hash-compare code{display:block;margin-top:6px;color:${colors.textSecondary};font-size:11px;overflow:hidden;text-overflow:ellipsis}
      .shield-data-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 18px;margin-top:14px}.shield-data-row{display:grid;grid-template-columns:minmax(90px,.6fr) minmax(0,1fr);gap:10px;padding:9px 0;border-bottom:1px solid ${colors.borderSubtle};font-size:11px}.shield-data-row>span{color:${colors.textMuted}}.shield-data-row>strong{color:${colors.textSecondary};font-weight:600;text-align:right;overflow:hidden;text-overflow:ellipsis}.mono,code{font-family:${typography.family.mono}}
      .shield-timeline{padding-left:4px}.shield-timeline-item{position:relative;display:grid;grid-template-columns:16px minmax(0,1fr);gap:10px;min-height:80px}.shield-timeline-item>i{position:absolute;left:4px;top:15px;bottom:-2px;width:1px;background:${colors.border}}.shield-timeline-dot{position:relative;z-index:1;width:9px;height:9px;margin-top:3px;border-radius:50%;background:${colors.accent};box-shadow:0 0 0 4px color-mix(in srgb,${colors.accent} 13%,transparent)}.shield-timeline-item strong{font-size:12px}.shield-timeline-item p{margin:4px 0;color:${colors.textSecondary};font-size:11px}.shield-timeline-item time{color:${colors.textMuted};font:10px ${typography.family.mono}}
      .shield-json summary{cursor:pointer;color:${colors.textSecondary};font-size:12px}.shield-json pre{max-height:360px;overflow:auto;margin:12px 0 0;padding:14px;border-radius:${radii.md};background:${colors.background};color:${colors.textSecondary};font-size:10px;line-height:1.55;white-space:pre-wrap;overflow-wrap:anywhere}.shield-muted{margin:0;color:${colors.textMuted};font-size:12px;line-height:1.55}.shield-mitre-list{display:flex;flex-wrap:wrap;gap:7px}.shield-mitre-list span{padding:6px 8px;border:1px solid color-mix(in srgb,${colors.accent} 30%,transparent);border-radius:6px;background:color-mix(in srgb,${colors.accent} 9%,transparent);color:${colors.accentHover};font:11px ${typography.family.mono}}
      .shield-decision-copy p,.shield-case-linked p{margin:0 0 14px;color:${colors.textSecondary};font-size:12px;line-height:1.55}.shield-decision-copy button,.shield-case-linked button{width:100%}.shield-case-linked strong,.shield-case-linked code{display:block;margin-top:7px}.shield-case-linked strong{font-size:13px}.shield-case-linked code{color:${colors.textMuted};font-size:10px;overflow-wrap:anywhere}.shield-case-linked p{margin-top:9px}.shield-inline-error{margin:10px 0 0;color:${colors.danger};font-size:11px}
      @media(max-width:960px){.shield-investigation-layout{grid-template-columns:1fr}.shield-investigation-aside{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));align-items:start}.shield-investigation-aside .shield-panel:last-child{grid-column:1/-1}}
      @media(max-width:640px){.shield-investigation-page{margin:-4px}.shield-investigation-hero{padding:16px}.shield-title-row{align-items:flex-start}.shield-provenance i,.shield-provenance span:nth-of-type(3){display:none}.shield-investigation-aside{display:flex}.shield-data-grid{grid-template-columns:1fr}.shield-hash-compare{grid-template-columns:1fr}.shield-hash-compare>span{transform:rotate(90deg);justify-self:center}.shield-data-row{grid-template-columns:1fr}.shield-data-row>strong{text-align:left}.shield-title-row h1{font-size:25px}}
      @media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
    `}</style>
  </div>;
}
