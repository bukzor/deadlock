import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

/** The Python server (`vis-server serve`) listens here (`bin/serve` sets VIS_API); see docs/dev/decisions.kb/vis-app.md. */
const API = process.env.VIS_API ?? "http://localhost:8787";

export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": API } },
  test: { include: ["src/**/*.test.ts"] },
});
