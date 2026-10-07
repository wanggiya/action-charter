import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const apiPort = loadEnv(mode, ".", "INTERFACE_API_PORT").INTERFACE_API_PORT || "8765";
  if (!/^\d+$/.test(apiPort) || Number(apiPort) < 1 || Number(apiPort) > 65535) {
    throw new Error("INTERFACE_API_PORT must be a valid port");
  }
  return {
    plugins: [react()],
    server: {
      proxy: { "/api": `http://127.0.0.1:${apiPort}` },
    },
  };
});
