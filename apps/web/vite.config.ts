import { defineConfig, searchForWorkspaceRoot } from 'vite';
import react from '@vitejs/plugin-react';
import * as path from 'path';
import tailwindcss from '@tailwindcss/vite';
import { read } from '../../packages/organization-info/organization-info';
import { legalDocuments } from '../../packages/organization-info/vite';
import { slicerEngine } from '../../packages/slicer-engine/vite';
// A relative path, so Vite bundles it with this config; Node cannot resolve its extensionless
// imports from the package export.
import { OrganizationInfoSchema } from '../../packages/api-client/src/gen/common/v1/organization_info_pb';
import pkg from './package.json';

const { title } = read(OrganizationInfoSchema);

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    slicerEngine(),
    legalDocuments(),
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
    // Same-origin /api and /auth in development, as Caddy provides in deployment. The dev
    // compose stack points these at its containers.
    proxy: {
      '/api': process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000',
      '/auth': {
        target: process.env.KEYCLOAK_PROXY_TARGET ?? 'http://127.0.0.1:8080',
        xfwd: true,
      },
    },
  },
});
