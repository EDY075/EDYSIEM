/**
 * Intelligence Page (Sprint 2.17 WP6) — Rules Manager, Rule Simulator, IOC e Assets.
 * Consome as APIs reais /soc/rules, /soc/simulator, /soc/iocs, /soc/assets.
 * Sem mocks.
 */
import { useState } from "react";
import { colors, radii, spacing, typography } from "../design-system/tokens";
import { Button } from "../design-system";
import { SeverityBadge } from "../design-system/components/badges";
import { EmptyState, LoadingSkeleton } from "../design-system/components/feedback";
import { Breadcrumb } from "../shell/Breadcrumb";
import { apiClient } from "../api/client";
import { useToast } from "../state/toast";

type Tab = "rules" | "simulator" | "iocs" | "assets";

interface RuleDto { rule_id: string; name: string; severity: string; category: string; mitre: string[]; tags: string[]; description: string; enabled: boolean; fire_count: number; last_fired: string | null; }
interface IocDto { value: string; ioc_type: string; reputation: string; first_seen: string; last_seen: string; hits: number; labels: string[]; }
interface AssetDto { hostname: string; ip: string; os: string; criticality: string; owner: string; status: string; last_seen: string; }

export function IntelligencePage() {
  const [tab, setTab] = useState<Tab>("rules");
  return (
    <div style={{ background: colors.background, minHeight: "100vh", padding: spacing["4"] }}>
      <Breadcrumb items={[{ label: "Operação", to: "/" }, { label: "Intelligence", to: "/intel" }]} />
      <h1 style={{ fontSize: typography.size["2xl"], color: colors.textPrimary, margin: "6px 0 16px" }}>Detection Intelligence</h1>
      <div style={{ display: "flex", gap: 8, marginBottom: spacing["4"], flexWrap: "wrap" }}>
        {(["rules", "simulator", "iocs", "assets"] as Tab[]).map((t) => (
          <button key={t} onClick={() => setTab(t)} style={{ padding: "7px 14px", borderRadius: radii.md, border: `1px solid ${tab === t ? colors.accent : colors.border}`, background: tab === t ? colors.accent + "18" : colors.surface, color: colors.textPrimary, cursor: "pointer", fontFamily: typography.family.ui }}>
            {t.toUpperCase()}
          </button>
        ))}
      </div>
      {tab === "rules" && <RulesPanel />}
      {tab === "simulator" && <SimulatorPanel />}
      {tab === "iocs" && <IocPanel />}
      {tab === "assets" && <AssetPanel />}
    </div>
  );
}

/* ---------------- Rules ---------------- */

function RulesPanel() {
  const [rules, setRules] = useState<RuleDto[] | null>(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  if (rules === null && loading) { loadRules().then((r) => { setRules(r); setLoading(false); }); }

  async function loadRules(): Promise<RuleDto[]> {
    const res = await apiClient.get<{ items: RuleDto[] }>("/soc/rules");
    return res.success && res.data ? res.data.items : [];
  }

  async function toggle(ruleId: string, enabled: boolean) {
    const r = await apiClient.post(`/soc/rules/${ruleId}/${enabled ? "enable" : "disable"}`);
    toast(r.success ? `Regra ${enabled ? "habilitada" : "desabilitada"}` : "Falha ao alterar regra", r.success ? "success" : "error");
    const items = await loadRules();
    setRules(items);
  }

  if (loading) return <LoadingSkeleton rows={6} />;
  if (!rules || rules.length === 0) return <EmptyState title="Nenhuma regra" description="Registre regras via POST /soc/rules ou aguarde o catálogo." />;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {rules.map((r) => (
        <div key={r.rule_id} style={{ display: "flex", justifyContent: "space-between", gap: spacing["3"], padding: spacing["3"], background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: radii.lg, flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: 220 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontFamily: typography.family.mono, fontSize: 12, color: colors.textMuted }}>{r.rule_id}</span>
              <SeverityBadge severity={r.severity as any}>{r.severity}</SeverityBadge>
              <span style={{ fontSize: typography.size.xs, color: r.enabled ? colors.status.online : colors.textMuted }}>{r.enabled ? "enabled" : "disabled"}</span>
              <span style={{ fontSize: typography.size.xs, color: colors.textMuted }}>fire: {r.fire_count}</span>
            </div>
            <div style={{ fontWeight: 600, color: colors.textPrimary, marginTop: 4 }}>{r.name}</div>
            {r.category && <div style={{ fontSize: typography.size.xs, color: colors.textSecondary }}>{r.category}</div>}
            {(r.mitre.length || r.tags.length) && (
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 6 }}>
                {r.mitre.map((m) => <Chip key={m}>{m}</Chip>)}
                {r.tags.map((t) => <Chip key={t} muted>{t}</Chip>)}
              </div>
            )}
          </div>
          <Button variant={r.enabled ? "secondary" : "primary"} onClick={() => toggle(r.rule_id, !r.enabled)}>
            {r.enabled ? "Desabilitar" : "Habilitar"}
          </Button>
        </div>
      ))}
    </div>
  );
}

/* ---------------- Simulator ---------------- */

function SimulatorPanel() {
  const [event, setEvent] = useState(JSON.stringify({ rule_id: "brute-force-ssh", category: "authentication" }, null, 2));
  const [result, setResult] = useState<{ applied: unknown[]; matches: number } | null>(null);

  async function run() {
    try {
      const payload = JSON.parse(event) as Record<string, unknown>;
      const r = await apiClient.post<{ applied: unknown[]; matches: number }>("/soc/simulator", { event: payload });
      if (r.success && r.data) setResult(r.data);
    } catch {
      setResult(null);
    }
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: spacing["4"] }}>
      <div>
        <textarea value={event} onChange={(e) => setEvent(e.target.value)} rows={12} style={{ width: "100%", fontFamily: typography.family.mono, fontSize: 12, background: colors.surface, color: colors.textPrimary, border: `1px solid ${colors.border}`, borderRadius: radii.md, padding: spacing["3"] }} />
        <div style={{ marginTop: 8 }}><Button variant="primary" onClick={run}>▶ Simular</Button></div>
      </div>
      <div style={{ fontFamily: typography.family.mono, fontSize: 12 }}>
        {result ? (
          <pre style={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: radii.md, padding: spacing["3"], color: colors.textPrimary }}>{JSON.stringify(result, null, 2)}</pre>
        ) : (
          <EmptyState title="Sem resultado" description="Edite o evento JSON e clique em Simular." />
        )}
      </div>
    </div>
  );
}

/* ---------------- IOC / Assets (compartilhado) ---------------- */

function IocPanel() {
  const [items, setItems] = useState<IocDto[] | null>(null);
  const [loading, setLoading] = useState(true);
  if (items === null && loading) apiClient.get<{ items: IocDto[] }>("/soc/iocs").then((r) => { setItems(r.success && r.data ? r.data.items : []); setLoading(false); });
  if (loading) return <LoadingSkeleton rows={6} />;
  return <EntityList items={items || []} ioc />;
}

function AssetPanel() {
  const [items, setItems] = useState<AssetDto[] | null>(null);
  const [loading, setLoading] = useState(true);
  if (items === null && loading) {
    apiClient.get<{ items: AssetDto[] }>("/soc/assets").then((r) => { setItems(r.success && r.data ? r.data.items : []); setLoading(false); });
  }
  if (loading) return <LoadingSkeleton rows={6} />;
  return <EntityList items={items || []} />;
}

function EntityList({ items, ioc }: { items: unknown[]; ioc?: boolean }) {
  if (!items || items.length === 0) return <EmptyState title={`Nenhum ${ioc ? "IOC" : "asset"}`} description={ioc ? "Registre IOCs para reputação e rastreio." : "Registre assets no inventário."} />;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {items.map((it: any) => (
        <div key={it.value || it.hostname} style={{ padding: spacing["3"], background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: radii.md }}>
          <Chip muted>{ioc ? it.ioc_type : it.criticality}</Chip>{" "}
          <span style={{ fontFamily: typography.family.mono, color: colors.textPrimary }}>{it.value || it.hostname}</span>
          <div style={{ fontSize: typography.size.xs, color: colors.textMuted, marginTop: 4 }}>
            {ioc ? `${it.reputation} · hits ${it.hits} · ${it.last_seen}` : `${it.ip} · ${it.os} · ${it.owner} · ${it.status} · ${it.last_seen}`}
          </div>
        </div>
      ))}
    </div>
  );
}

function Chip({ children, muted }: { children: string; muted?: boolean }) {
  return <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 9999, background: muted ? colors.surfaceAlt : colors.surfaceAlt, border: `1px solid ${colors.border}`, color: muted ? colors.textMuted : colors.textSecondary, fontFamily: typography.family.mono }}>{children}</span>;
}