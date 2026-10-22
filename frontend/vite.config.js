import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy API + WebSocket to Django so the browser sees one origin (no CORS fuss).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
});
