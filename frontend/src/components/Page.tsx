/** Operational workspace state — intentionally without fictional actions. */
import { BrandMark, colors, elevation, radii, spacing, typography } from "../design-system";

export function Page({ title, description }: { title: string; description: string }) {
  return (
    <section style={{ maxWidth: 840, padding: `${spacing["6"]} 0` }} aria-labelledby="workspace-title">
      <div style={{ color: colors.accent, fontSize: "10px", fontWeight: typography.weight.semibold, letterSpacing: "0.12em", marginBottom: spacing["2"] }}>CONTROL PLANE</div>
      <h1 id="workspace-title" style={{ fontSize: typography.size.display, letterSpacing: "-0.03em", color: colors.textPrimary, margin: 0 }}>{title}</h1>
      <div style={{ marginTop: spacing["5"], padding: spacing["5"], border: `1px solid ${colors.border}`, borderRadius: radii.xl, background: `linear-gradient(135deg, color-mix(in srgb, ${colors.surfaceAlt} 55%, ${colors.surface}) 0%, ${colors.surface} 72%)`, boxShadow: elevation.floating, position: "relative", overflow: "hidden" }}>
        <div aria-hidden style={{ position: "absolute", width: 180, height: 180, right: -72, top: -86, borderRadius: "50%", background: "color-mix(in srgb, var(--color-accent) 9%, transparent)" }} />
        <div aria-hidden style={{ width: 36, height: 36, borderRadius: radii.lg, display: "grid", placeItems: "center", color: colors.accent, background: "color-mix(in srgb, var(--color-accent) 10%, transparent)", border: "1px solid color-mix(in srgb, var(--color-accent) 22%, transparent)" }}><BrandMark size={18} /></div>
        <p style={{ position: "relative", maxWidth: 560, margin: `${spacing["4"]} 0 0`, color: colors.textSecondary, fontSize: typography.size.base, lineHeight: typography.lineHeight.relaxed }}>{description}</p>
        <div style={{ position: "relative", display: "flex", alignItems: "center", gap: spacing["2"], marginTop: spacing["4"], color: colors.textMuted, fontSize: typography.size.xs, fontFamily: typography.family.mono }}><span style={{ width: 5, height: 5, borderRadius: "50%", background: colors.textMuted }} />WORKSPACE READY</div>
      </div>
    </section>
  );
}