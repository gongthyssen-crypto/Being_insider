import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 18422,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:18421",
        changeOrigin: true,
      },
    },
  },
});

