import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { colors, elevation, motion, radii, spacing, typography } from "../design-system/tokens";
import { useTheme } from "../theme/ThemeProvider";

type CommandGroup = "Operação" | "Resposta" | "Detecção" | "Administração" | "Sistema";

interface Command {
  id: string;
  label: string;
  description: string;
  group: CommandGroup;
  to?: string;
  action?: "toggle-theme" | "refresh-data" | "open-notifications";
  glyph: "grid" | "bolt" | "bell" | "case" | "radar" | "settings";
}

const commands: Command[] = [
  { id: "overview", label: "Abrir overview", description: "Visão operacional do SOC", group: "Operação", to: "/", glyph: "grid" },
  { id: "war-room", label: "Abrir War Room", description: "Coordenação de resposta ativa", group: "Operação", to: "/war-room", glyph: "bolt" },
  { id: "alerts", label: "Ver alertas", description: "Fila de detecções e risco", group: "Operação", to: "/alerts", glyph: "bell" },
  { id: "incidents", label: "Ver incidentes", description: "Incidentes correlacionados", group: "Operação", to: "/incidents", glyph: "bolt" },
  { id: "investigation", label: "Abrir investigação", description: "Evidências e pivôs de um caso", group: "Operação", to: "/investigate", glyph: "radar" },
  { id: "cases", label: "Abrir cases", description: "Fila operacional e tratamento", group: "Resposta", to: "/cases", glyph: "case" },
  { id: "playbooks", label: "Abrir playbooks", description: "Automação de resposta", group: "Resposta", to: "/playbooks", glyph: "bolt" },
  { id: "rules", label: "Abrir regras", description: "Catálogo de detecções", group: "Detecção", to: "/rules", glyph: "grid" },
  { id: "intelligence", label: "Abrir intelligence", description: "IOCs e contexto de ameaça", group: "Detecção", to: "/intel", glyph: "radar" },
  { id: "settings", label: "Abrir configurações", description: "Preferências e ambiente", group: "Administração", to: "/settings", glyph: "settings" },
  { id: "toggle-theme", label: "Alternar tema", description: "Mudar entre tema escuro e claro", group: "Sistema", action: "toggle-theme", glyph: "settings" },
  { id: "refresh-data", label: "Recarregar dados", description: "Solicitar dados atuais ao console", group: "Sistema", action: "refresh-data", glyph: "bolt" },
  { id: "open-notifications", label: "Abrir notificações", description: "Ver alertas em acompanhamento", group: "Sistema", action: "open-notifications", glyph: "bell" },
];

function CommandGlyph({ glyph }: { glyph: Command["glyph"] }) {
  const common = { fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  const paths = {
    grid: <><rect x="4" y="4" width="6" height="6" rx="1" /><rect x="14" y="4" width="6" height="6" rx="1" /><rect x="4" y="14" width="6" height="6" rx="1" /><rect x="14" y="14" width="6" height="6" rx="1" /></>,
    bolt: <path d="m13 2-9 12h7l-1 8 10-13h-7l0-7Z" />,
    bell: <><path d="M18 9a6 6 0 0 0-12 0c0 7-2.5 8-2.5 8h17S18 16 18 9Z" /><path d="M10 21h4" /></>,
    case: <path d="M3 7h6l2 2h10v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z" />,
    radar: <><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="3" /><path d="M12 4V2M20 12h2M12 22v-2M2 12h2" /></>,
    settings: <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5v.2h-4v-.2a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1-2.8-2.8.1-.1A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-1.5-1H3v-4h.1A1.7 1.7 0 0 0 4.6 9a1.7 1.7 0 0 0-.3-1.8l-.1-.1 2.8-2.8.1.1a1.7 1.7 0 0 0 1.8.3 1.7 1.7 0 0 0 1-1.5V3h4v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1 2.8 2.8-.1.1a1.7 1.7 0 0 0-.3 1.8 1.7 1.7 0 0 0 1.5 1h.2v4h-.2a1.7 1.7 0 0 0-1.4 1Z" /></>,
  };
  return <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true" {...common}>{paths[glyph]}</svg>;
}

export function GlobalSearch() {
  const navigate = useNavigate();
  const { toggle } = useTheme();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(0);

  const results = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("pt-BR");
    if (!normalized) return commands;
    return commands.filter((command) => `${command.label} ${command.description} ${command.group}`.toLocaleLowerCase("pt-BR").includes(normalized));
  }, [query]);

  const execute = (command: Command | undefined) => {
    if (!command) return;
    if (command.to) navigate(command.to);
    if (command.action === "toggle-theme") toggle();
    if (command.action === "refresh-data") window.location.reload();
    if (command.action === "open-notifications") window.dispatchEvent(new Event("edysiem:open-notifications"));
    setOpen(false);
    setQuery("");
  };

  const shortcut = useMemo(() => {
    const platform = (navigator as Navigator & { userAgentData?: { platform?: string } }).userAgentData?.platform ?? navigator.platform ?? navigator.userAgent;
    return /mac|iphone|ipad/i.test(platform) ? "⌘K" : "Ctrl K";
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen(true);
        window.setTimeout(() => inputRef.current?.focus(), 0);
      }
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  const onInputKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown") { event.preventDefault(); setSelected((value) => Math.min(value + 1, Math.max(results.length - 1, 0))); }
    if (event.key === "ArrowUp") { event.preventDefault(); setSelected((value) => Math.max(value - 1, 0)); }
    if (event.key === "Enter") { event.preventDefault(); execute(results[selected]); }
    if (event.key === "Escape") setOpen(false);
  };

  useEffect(() => setSelected(0), [query]);

  const groups = Array.from(new Set(results.map((item) => item.group)));

  return (
    <div style={{ position: "relative", width: "100%" }}>
      <div
        className="command-trigger"
        onClick={() => { setOpen(true); inputRef.current?.focus(); }}
        style={{
          display: "flex", alignItems: "center", gap: spacing["2"], minHeight: 38,
          padding: `0 ${spacing["3"]}`, cursor: "text", background: colors.background,
          border: `1px solid ${open ? colors.accent : colors.border}`, borderRadius: radii.lg,
          boxShadow: open ? "0 0 0 3px color-mix(in srgb, var(--color-accent) 14%, transparent)" : "inset 0 1px 0 color-mix(in srgb, white 4%, transparent)",
          transition: `border-color ${motion.transition.fast}, box-shadow ${motion.transition.fast}, background ${motion.transition.fast}`,
        }}
      >
        <span style={{ color: colors.textMuted, display: "inline-flex" }}><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4 4" /></svg></span>
        <input ref={inputRef} value={query} onFocus={() => setOpen(true)} onChange={(event) => setQuery(event.target.value)} onKeyDown={onInputKeyDown} placeholder="Buscar ou executar comando…" aria-label="Buscar ou executar comando" autoComplete="off" spellCheck={false} style={{ flex: 1, minWidth: 0, border: 0, outline: 0, background: "transparent", color: colors.textPrimary, fontFamily: typography.family.ui, fontSize: typography.size.sm }} />
        <kbd aria-hidden style={{ color: colors.textMuted, border: `1px solid ${colors.border}`, borderRadius: 5, padding: "2px 5px", fontFamily: typography.family.mono, fontSize: 10, background: colors.surfaceAlt }}>{shortcut}</kbd>
      </div>
      {open && (
        <div role="dialog" aria-label="Paleta de comandos" className="command-palette" style={{ position: "absolute", top: "calc(100% + 8px)", left: 0, right: 0, zIndex: 500, overflow: "hidden", maxHeight: 430, background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: radii.lg, boxShadow: elevation.overlay, animation: "commandIn 160ms cubic-bezier(.2,0,0,1) both" }}>
          <div style={{ padding: `${spacing["2"]} ${spacing["3"]}`, borderBottom: `1px solid ${colors.borderSubtle}`, color: colors.textMuted, fontSize: typography.size.xs }}>Navegação rápida do workspace</div>
          <div style={{ maxHeight: 360, overflowY: "auto", padding: spacing["1"] }}>
            {results.length === 0 ? <div style={{ padding: spacing["4"], color: colors.textMuted, textAlign: "center", fontSize: typography.size.sm }}>Nenhum comando encontrado.</div> : groups.map((group) => (
              <section key={group} aria-label={group} style={{ paddingBottom: spacing["1"] }}>
                <div style={{ padding: `${spacing["2"]} ${spacing["2"]} ${spacing["1"]}`, color: colors.textMuted, fontSize: 10, letterSpacing: "0.11em", textTransform: "uppercase", fontWeight: typography.weight.semibold }}>{group}</div>
                {results.filter((command) => command.group === group).map((command) => {
                  const index = results.indexOf(command);
                  const isSelected = selected === index;
                  return <button key={command.id} type="button" onMouseEnter={() => setSelected(index)} onClick={() => execute(command)} style={{ width: "100%", display: "flex", alignItems: "center", gap: spacing["3"], padding: `${spacing["2"]} ${spacing["2"]}`, background: isSelected ? colors.accentSubtle : "transparent", color: colors.textPrimary, border: "none", borderRadius: radii.md, cursor: "pointer", textAlign: "left", transition: `background ${motion.transition.fast}` }}>
                    <span style={{ display: "inline-grid", placeItems: "center", width: 28, height: 28, borderRadius: radii.md, color: isSelected ? colors.accentHover : colors.textSecondary, background: isSelected ? "color-mix(in srgb, var(--color-accent) 13%, transparent)" : colors.surfaceAlt, border: `1px solid ${colors.borderSubtle}` }}><CommandGlyph glyph={command.glyph} /></span>
                    <span style={{ flex: 1, minWidth: 0 }}><span style={{ display: "block", fontSize: typography.size.sm, fontWeight: typography.weight.medium }}>{command.label}</span><span style={{ display: "block", marginTop: 2, color: colors.textMuted, fontSize: typography.size.xs }}>{command.description}</span></span>
                    <span style={{ color: colors.textMuted, fontSize: typography.size.xs, fontFamily: typography.family.mono }}>↵</span>
                  </button>;
                })}
              </section>
            ))}
          </div>
        </div>
      )}
      <style>{`@keyframes commandIn { from { opacity: 0; transform: translateY(-5px) scale(.99); } to { opacity: 1; transform: translateY(0) scale(1); } } .command-trigger:hover { border-color: color-mix(in srgb, var(--color-text-muted) 45%, transparent) !important; } @media (prefers-reduced-motion: reduce) { .command-palette { animation: none !important; } }`}</style>
    </div>
  );
}
