import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  return {
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
          target: env.VITE_PROXY_TARGET ?? "http://localhost:8080",
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path, // mantém /api/v1 no path
        },
      },
    },
  };
});
