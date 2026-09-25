import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // file:// loading (the default run mode) needs relative asset URLs, not root-absolute ones.
  base: "./",
  server: { port: 5173, strictPort: true },
});
