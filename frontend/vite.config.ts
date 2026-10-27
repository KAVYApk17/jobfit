import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    // Polling makes hot reload work on Windows bind mounts inside Docker.
    watch: { usePolling: true },
  },
});
