import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      // Con "^" Vite usa una expresión regular: "/lab" a secas también capturaría la ruta /laboratorio.
      "^/gov/": {
        target: "http://127.0.0.1:8100",
        changeOrigin: true,
      },
      "^/lab/": {
        target: "http://127.0.0.1:8200",
        changeOrigin: true,
      },
    },
  },
});
