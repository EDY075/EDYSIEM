/// <reference types="vite/client" />

declare global {
  interface ImportMeta {
    readonly env: Record<string, string>;
  }
}