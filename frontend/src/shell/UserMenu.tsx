import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { colors, elevation, motion, radii, spacing, typography } from "../design-system/tokens";
import { useAlerts } from "../hooks";
import { useTheme } from "../theme/ThemeProvider";

const readNotificationsKey = "edysiem-read-notifications";

function storedReadNotifications() {
  try {
    const stored = JSON.parse(localStorage.getItem(readNotificationsKey) ?? "[]");
    return new Set(Array.isArray(stored) ? stored.filter((value): value is string => typeof value === "string") : []);
  } catch {
    return new Set<string>();
  }
}

function Chevron({ up = false }: { up?: boolean }) {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={up ? "m7 15 5-5 5 5" : "m7 9 5 5 5-5"} /></svg>;
}

function BellGlyph() {
  return <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M18 9a6 6 0 0 0-12 0c0 7-2.5 8-2.5 8h17S18 16 18 9Z" /><path d="M10 21h4" /></svg>;
}

const tone = (severity: string) => severity === "critical" ? colors.severity.critical : severity === "high" ? colors.severity.high : severity === "medium" ? colors.severity.medium : colors.accent;

export function UserMenu() {
  const navigate = useNavigate();
  const { mode, toggle } = useTheme();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onPointerDown = (event: MouseEvent) => { if (rootRef.current && !rootRef.current.contains(event.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, []);

  return <div ref={rootRef} style={{ position: "relative" }}>
    <button type="button" onClick={() => setOpen((value) => !value)} aria-haspopup="menu" aria-expanded={open} aria-label="Abrir menu do usuário" className="user-trigger" style={{ display: "flex", alignItems: "center", gap: spacing["2"], padding: "3px 7px 3px 3px", border: `1px solid ${open ? colors.accent : colors.border}`, borderRadius: radii.full, background: open ? colors.surfaceAlt : "transparent", color: colors.textSecondary, cursor: "pointer", transition: `border-color ${motion.transition.fast}, background ${motion.transition.fast}, box-shadow ${motion.transition.fast}` }}>
      <span aria-hidden="true" style={{ display: "grid", placeItems: "center", width: 30, height: 30, clipPath: "polygon(25% 6.7%,75% 6.7%,93.3% 25%,93.3% 75%,75% 93.3%,25% 93.3%,6.7% 75%,6.7% 25%)", background: `linear-gradient(135deg, ${colors.accentHover}, ${colors.accent})`, color: colors.textOnAccent, fontWeight: typography.weight.bold, fontSize: typography.size.xs }}>A</span>
      <span data-user-label style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", lineHeight: 1.12, minWidth: 0 }}><span style={{ color: colors.textPrimary, fontSize: typography.size.xs, fontWeight: typography.weight.semibold }}>Analyst SOC</span><span style={{ color: colors.textMuted, fontSize: 10 }}>analyst@edy</span></span>
      <span style={{ color: colors.textMuted, display: "inline-flex" }}><Chevron up={open} /></span>
    </button>
    {open && <div role="menu" aria-label="Menu do usuário" className="header-popover" style={{ position: "absolute", right: 0, top: "calc(100% + 8px)", width: 272, padding: spacing["2"], zIndex: 500, border: `1px solid ${colors.border}`, borderRadius: radii.lg, background: colors.surface, boxShadow: elevation.overlay, animation: "headerPopoverIn 150ms cubic-bezier(.2,0,0,1) both" }}>
      <div style={{ display: "flex", alignItems: "center", gap: spacing["3"], padding: spacing["2"], borderBottom: `1px solid ${colors.borderSubtle}` }}>
        <span aria-hidden="true" style={{ display: "grid", placeItems: "center", width: 38, height: 38, clipPath: "polygon(25% 6.7%,75% 6.7%,93.3% 25%,93.3% 75%,75% 93.3%,25% 93.3%,6.7% 75%,6.7% 25%)", background: `linear-gradient(135deg, ${colors.accentHover}, ${colors.accent})`, color: colors.textOnAccent, fontWeight: typography.weight.bold }}>A</span>
        <span><span style={{ display: "block", color: colors.textPrimary, fontWeight: typography.weight.semibold, fontSize: typography.size.sm }}>Analyst SOC</span><span style={{ display: "block", marginTop: 2, color: colors.textMuted, fontSize: typography.size.xs }}>analyst@edy · SOC Operations</span></span>
      </div>
      <div style={{ padding: `${spacing["2"]} ${spacing["2"]} 0`, color: colors.textMuted, fontSize: 10, fontWeight: typography.weight.semibold, letterSpacing: "0.1em" }}>SESSÃO</div>
      <div style={{ display: "flex", alignItems: "center", gap: 7, padding: `${spacing["2"]} ${spacing["2"]}`, color: colors.textSecondary, fontSize: typography.size.xs }}><span style={{ width: 6, height: 6, borderRadius: "50%", background: colors.status.online, boxShadow: `0 0 0 3px color-mix(in srgb, ${colors.status.online} 15%, transparent)` }} />Sessão operacional ativa</div>
      <button type="button" role="menuitem" onClick={() => { navigate("/settings"); setOpen(false); }} className="header-menu-item" style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 2, padding: `${spacing["2"]} ${spacing["2"]}`, border: 0, borderRadius: radii.md, background: "transparent", color: colors.textPrimary, cursor: "pointer", textAlign: "left", fontSize: typography.size.sm }}>Perfil e preferências<span style={{ color: colors.textMuted, display: "inline-flex" }}><Chevron /></span></button>
      <button type="button" role="menuitem" onClick={toggle} className="header-menu-item" style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 2, padding: `${spacing["2"]} ${spacing["2"]}`, border: 0, borderRadius: radii.md, background: "transparent", color: colors.textPrimary, cursor: "pointer", textAlign: "left", fontSize: typography.size.sm }}>Tema {mode === "dark" ? "claro" : "escuro"}<span style={{ color: colors.textMuted, fontSize: typography.size.xs }}>Aplicar</span></button>
      <button type="button" role="menuitem" disabled title="Autenticação local ainda não configurada" style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 2, padding: `${spacing["2"]} ${spacing["2"]}`, border: 0, borderRadius: radii.md, background: "transparent", color: colors.textMuted, cursor: "not-allowed", textAlign: "left", fontSize: typography.size.sm }}>Encerrar sessão<span style={{ fontSize: typography.size.xs }}>Integração pendente</span></button>
    </div>}
  </div>;
}

export function Notifications() {
  const navigate = useNavigate();
  const { alerts, loading } = useAlerts(6);
  const [open, setOpen] = useState(false);
  const [readIds, setReadIds] = useState<Set<string>>(storedReadNotifications);
  const rootRef = useRef<HTMLDivElement>(null);
  const active = alerts.filter((alert) => !["closed", "resolved", "false_positive"].includes(alert.status));
  const unread = active.filter((alert) => !readIds.has(alert.id));

  const saveRead = (next: Set<string>) => {
    setReadIds(next);
    localStorage.setItem(readNotificationsKey, JSON.stringify([...next]));
  };

  const markRead = (id: string) => {
    if (readIds.has(id)) return;
    const next = new Set(readIds);
    next.add(id);
    saveRead(next);
  };

  useEffect(() => {
    const onPointerDown = (event: MouseEvent) => { if (rootRef.current && !rootRef.current.contains(event.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, []);

  useEffect(() => {
    const openNotifications = () => setOpen(true);
    window.addEventListener("edysiem:open-notifications", openNotifications);
    return () => window.removeEventListener("edysiem:open-notifications", openNotifications);
  }, []);

  return <div ref={rootRef} style={{ position: "relative" }}>
    <button type="button" onClick={() => setOpen((value) => !value)} aria-haspopup="dialog" aria-expanded={open} aria-label="Abrir central de alertas" className="notification-trigger" style={{ position: "relative", display: "grid", placeItems: "center", width: 36, height: 36, padding: 0, border: `1px solid ${open ? colors.accent : colors.border}`, borderRadius: radii.md, background: open ? colors.surfaceAlt : "transparent", color: open ? colors.accentHover : colors.textSecondary, cursor: "pointer", transition: `border-color ${motion.transition.fast}, background ${motion.transition.fast}, color ${motion.transition.fast}` }}>
      <BellGlyph />
      {!loading && unread.length > 0 && <span aria-label={`${unread.length} alertas não lidos`} style={{ position: "absolute", top: -5, right: -5, minWidth: 16, height: 16, display: "grid", placeItems: "center", padding: "0 4px", borderRadius: radii.full, color: colors.textOnAccent, background: colors.severity.critical, border: `2px solid ${colors.surface}`, fontFamily: typography.family.mono, fontSize: 9, fontWeight: typography.weight.bold }}>{unread.length > 9 ? "9+" : unread.length}</span>}
    </button>
    {open && <div role="dialog" aria-label="Central de alertas" className="header-popover" style={{ position: "absolute", right: 0, top: "calc(100% + 8px)", width: 352, zIndex: 500, overflow: "hidden", border: `1px solid ${colors.border}`, borderRadius: radii.lg, background: colors.surface, boxShadow: elevation.overlay, animation: "headerPopoverIn 150ms cubic-bezier(.2,0,0,1) both" }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", padding: `${spacing["3"]} ${spacing["3"]} ${spacing["2"]}`, borderBottom: `1px solid ${colors.borderSubtle}` }}><span style={{ color: colors.textPrimary, fontSize: typography.size.sm, fontWeight: typography.weight.semibold }}>Alertas em acompanhamento</span><button type="button" onClick={() => saveRead(new Set(active.map((alert) => alert.id)))} disabled={loading || unread.length === 0} style={{ border: 0, padding: 0, color: unread.length ? colors.accentHover : colors.textMuted, background: "transparent", cursor: unread.length ? "pointer" : "default", fontSize: typography.size.xs }}>Marcar lidas</button></div>
      <div style={{ maxHeight: 320, overflowY: "auto", padding: spacing["1"] }}>{loading ? <div style={{ padding: spacing["4"], color: colors.textMuted, fontSize: typography.size.sm }}>Atualizando alertas…</div> : active.length === 0 ? <div style={{ padding: spacing["4"], color: colors.textMuted, textAlign: "center", fontSize: typography.size.sm }}>Nenhum alerta ativo.</div> : active.map((alert) => <button key={alert.id} type="button" onClick={() => { markRead(alert.id); navigate("/alerts"); setOpen(false); }} className="notification-row" style={{ width: "100%", display: "flex", gap: spacing["2"], alignItems: "flex-start", padding: spacing["2"], border: 0, borderRadius: radii.md, background: "transparent", textAlign: "left", cursor: "pointer", color: colors.textPrimary, opacity: readIds.has(alert.id) ? 0.7 : 1 }}><span style={{ width: 7, height: 7, marginTop: 5, borderRadius: "50%", background: tone(alert.severity), boxShadow: `0 0 0 3px color-mix(in srgb, ${tone(alert.severity)} 13%, transparent)` }} /><span style={{ flex: 1, minWidth: 0 }}><span style={{ display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontSize: typography.size.sm, fontWeight: typography.weight.medium }}>{alert.title}</span><span style={{ display: "block", marginTop: 2, color: colors.textMuted, fontSize: typography.size.xs }}>{alert.rule} · risco {alert.riskScore}</span></span><span style={{ padding: "2px 5px", color: tone(alert.severity), background: `color-mix(in srgb, ${tone(alert.severity)} 12%, transparent)`, borderRadius: 4, fontSize: 9, fontWeight: typography.weight.semibold, textTransform: "uppercase" }}>{alert.severity}</span></button>)}</div>
      <button type="button" onClick={() => { navigate("/alerts"); setOpen(false); }} className="notification-footer" style={{ width: "100%", border: 0, borderTop: `1px solid ${colors.borderSubtle}`, padding: `${spacing["2"]} ${spacing["3"]}`, background: "transparent", color: colors.accentHover, textAlign: "left", cursor: "pointer", fontSize: typography.size.xs, fontWeight: typography.weight.semibold }}>Abrir central de alertas →</button>
    </div>}
    <style>{`@keyframes headerPopoverIn { from { opacity: 0; transform: translateY(-5px) scale(.99); } to { opacity: 1; transform: translateY(0) scale(1); } } .user-trigger:hover, .notification-trigger:hover { border-color: color-mix(in srgb, var(--color-accent) 55%, var(--color-border)) !important; background: var(--color-surface-alt) !important; } .header-menu-item:hover, .notification-row:hover, .notification-footer:hover { background: var(--color-accent-subtle) !important; } @media (prefers-reduced-motion: reduce) { .header-popover { animation: none !important; } }`}</style>
  </div>;
}
