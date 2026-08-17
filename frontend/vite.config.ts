import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

export default defineConfig(() => {
  const apiProxy = {
    // Version 0.3.0 is deliberately loopback-only. Do not make this target
    // environment-configurable: operator credentials are forwarded by this proxy.
    target: "http://127.0.0.1:8080",
    changeOrigin: true,
    secure: false,
    rewrite: (path: string) => path,
  };
  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    server: {
      // Localhost-only by policy: never publish the development UI to the LAN.
      host: "127.0.0.1",
      port: 5173,
      strictPort: true,
      proxy: {
        // Proxy de desenvolvimento: Vite → Backend FastAPI
        // Evita problemas de CORS durante desenvolvimento local
        "/api": apiProxy,
      },
    },
    preview: {
      host: "127.0.0.1",
      port: 4173,
      strictPort: true,
      proxy: {
        "/api": apiProxy,
      },
    },
  };
});
