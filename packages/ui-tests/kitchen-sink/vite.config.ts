import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';
import { defineConfig, searchForWorkspaceRoot } from 'vite';

export default defineConfig({
  root: fileURLToPath(new URL('.', import.meta.url)),
  plugins: [react(), tailwindcss()],
  resolve: {
    // ui-kit sits outside this project, so its files would not find this project's React.
    dedupe: ['react', 'react-dom'],
  },
  server: {
    fs: { allow: [searchForWorkspaceRoot(process.cwd())] },
  },
});
