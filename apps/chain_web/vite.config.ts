import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// API calls go to the Go server in dev (make app-dev); the build is served by the Go binary.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": "http://127.0.0.1:8787" } },
  build: { outDir: "dist", chunkSizeWarningLimit: 1500 },
  test: { environment: "node" },
});
