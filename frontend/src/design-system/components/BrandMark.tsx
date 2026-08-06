/** EDY SIEM - Echelon Step, an autonomous product mark. */
export interface BrandMarkProps { size?: number; title?: string; decorative?: boolean; className?: string; }
/** Three continuous reading steps. The silhouette remains clear at 16 px. */
export function BrandMark({ size = 24, title = "EDY SIEM", decorative = true, className }: BrandMarkProps) {
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" role={decorative ? undefined : "img"} aria-hidden={decorative || undefined} aria-label={decorative ? undefined : title} xmlns="http://www.w3.org/2000/svg">
      {!decorative && <title>{title}</title>}
      <path fill="currentColor" fillRule="evenodd" clipRule="evenodd" d="M4 3h16l-3 3H7v3h9l-3 3H7v3h13l-3 3H4V3Z" />
    </svg>
  );
}