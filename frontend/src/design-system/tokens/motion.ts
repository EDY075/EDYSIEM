/**
 * Design Tokens — Motion (UI 3.1)
 *
 * Animações curtas e consistentes (transições discretas, sem chamar atenção).
 */

export const motion = {
  duration: {
    instant: "80ms",
    fast: "120ms",
    normal: "200ms",
    slow: "300ms",
  },
  easing: {
    standard: "cubic-bezier(0.2, 0, 0, 1)",
    emphasized: "cubic-bezier(0.2, 0, 0, 1.4)",
    linear: "linear",
  },
  /** Curvas de micro-interação padrão. */
  transition: {
    fast: "120ms cubic-bezier(0.2, 0, 0, 1)",
    normal: "200ms cubic-bezier(0.2, 0, 0, 1)",
  },
} as const;
