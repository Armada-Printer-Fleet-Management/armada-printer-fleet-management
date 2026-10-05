import react from '@vitejs/plugin-react';
import { defineConfig, searchForWorkspaceRoot } from 'vite';
import tailwindcss from '@tailwindcss/vite';
import { read } from '../../../packages/organization-info/organization-info';
import { OrganizationInfoSchema } from './src/gen/common/v1/organization_info_pb';

const { title } = read(OrganizationInfoSchema);

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    {
      name: 'organization-title',
      transformIndexHtml: {
        order: 'pre',
        handler: (html) => html.replaceAll('%ORGANIZATION_TITLE%', title),
      },
    },
  ],
  // file:// loading (the default run mode) needs relative asset URLs, not root-absolute ones.
  base: './',
  resolve: {
    // packages/ sits outside this project, so its files would not find this project's installs.
    dedupe: ['@bufbuild/protobuf', 'react', 'react-dom'],
  },
  server: {
    port: 5173,
    strictPort: true,
    fs: { allow: [searchForWorkspaceRoot(process.cwd())] },
  },
});
