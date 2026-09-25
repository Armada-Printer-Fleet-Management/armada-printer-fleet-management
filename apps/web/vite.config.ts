import { defineConfig, searchForWorkspaceRoot } from 'vite';
import react from '@vitejs/plugin-react';
import * as path from 'path';
import { read } from '../../packages/organization-info/organization-info';
import { OrganizationInfoSchema } from './src/gen/common/v1/organization_info_pb';
import pkg from './package.json';

const organizationInfoDir = path.resolve(__dirname, '../../packages/organization-info');
const uiKitDir = path.resolve(__dirname, '../../packages/ui-kit');
const { title } = read(OrganizationInfoSchema);

export default defineConfig({
  plugins: [
    react(),
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
      '@organization-info': organizationInfoDir,
      '@ui-kit': uiKitDir,
    },
    // packages/ sits outside this project, so its files would not find this project's installs.
    dedupe: ['@bufbuild/protobuf', 'react', 'react-dom'],
  },
  server: {
    port: 5174,
    fs: { allow: [searchForWorkspaceRoot(process.cwd()), organizationInfoDir, uiKitDir] },
  },
});