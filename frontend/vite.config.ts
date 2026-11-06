import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Same-origin in development: the browser only talks to Vite, which forwards /api to FastAPI.
// `vite preview` reuses this proxy.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://localhost:8000" } },
});
