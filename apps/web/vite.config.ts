import { defineConfig, searchForWorkspaceRoot } from 'vite';
import react from '@vitejs/plugin-react';
import * as path from 'path';
import tailwindcss from '@tailwindcss/vite';
import { read } from '../../packages/organization-info/organization-info';
import { OrganizationInfoSchema } from './src/gen/common/v1/organization_info_pb';
import pkg from './package.json';

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
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version),
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
    // packages/ sits outside this project, so its files would not find this project's installs.
    dedupe: ['@bufbuild/protobuf', 'react', 'react-dom'],
  },
  server: {
    port: 5174,
    fs: { allow: [searchForWorkspaceRoot(process.cwd())] },
  },
});