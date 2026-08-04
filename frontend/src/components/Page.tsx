/**
 * Page — stub estrutural (UI 3.2)
 */
import { colors, typography } from "../design-system";

export function Page({ title }: { title: string }) {
  return (
    <div>
      <h1
        style={{
          fontSize: typography.size["2xl"],
          color: colors.textPrimary,
          margin: 0,
          marginBottom: 16,
        }}
      >
        {title}
      </h1>
      <p style={{ color: colors.textSecondary, fontSize: typography.size.base }}>
        Página estrutural — lógica a ser conectada.
      </p>
    </div>
  );
}
