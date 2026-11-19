// Runs generate-test-gcode.ts through Vite, which resolves the slicer's extensionless TypeScript
// imports the way the apps' builds do. Usage: node scripts/generate-test-gcode.mjs [server URL]
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';

const vite = await createServer({
  root: fileURLToPath(new URL('..', import.meta.url)),
  configFile: false,
  logLevel: 'error',
  server: { middlewareMode: true, hmr: false },
  appType: 'custom',
});
try {
  const script = await vite.ssrLoadModule('/scripts/generate-test-gcode.ts');
  await script.main(process.argv[2] ?? script.DEFAULT_SERVER_URL);
} finally {
  await vite.close();
}
