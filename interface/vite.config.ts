import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const apiPort = loadEnv(mode, ".", "INTERFACE_API_PORT").INTERFACE_API_PORT || "8765";
  if (!/^\d+$/.test(apiPort) || Number(apiPort) < 1 || Number(apiPort) > 65535) {
    throw new Error("INTERFACE_API_PORT must be a valid port");
  }
  return {
    plugins: [react(), {
      name: "reload-plain-typescript-hooks",
      apply: "serve",
      handleHotUpdate({ file, server }) {
        // React's refresh plugin does not track signatures in non-JSX .ts hooks.
        // Preserving App state after adding/removing a hook corrupts hook order.
        // Reload from saved chat/workflow state instead of accepting that update.
        if (/\/src\/.*\/use-[^/]+\.ts$/.test(file.replace(/\\/g, "/"))) {
          server.ws.send({ type: "full-reload" });
          return [];
        }
      },
    }],
    server: {
      proxy: { "/api": `http://127.0.0.1:${apiPort}` },
    },
  };
});
