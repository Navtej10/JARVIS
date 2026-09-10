import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import electron from "vite-plugin-electron";

// Transparent, always-on-top overlay is handled at the OS/Electron shell
// level (outside this scaffold) -- this dev server just serves the React
// app that gets embedded in that overlay window.
export default defineConfig({
  plugins: [
    react(),
    electron([
      {
        entry: "electron/main.ts",
      },
      {
        entry: "electron/preload.ts",
        onstart(options) {
          options.reload()
        },
      },
    ]),
  ],
  server: {
    port: 5173,
  },
});
