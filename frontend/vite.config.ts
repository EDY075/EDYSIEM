import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // Proxy de desenvolvimento: Vite → Backend FastAPI
      // Evita problemas de CORS durante desenvolvimento local
      "/api": {
        target: process.env.VITE_API_URL
          ? process.env.VITE_API_URL.replace("/api/v1", "")
          : "http://localhost:8080",
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path, // mantém /api/v1 no path
      },
    },
  },
});
