import { browserTestConfig } from '@armada/ui-tests/playwright-config';

// Apart from this app's own dev server (5174), so tests run while it is up.
const port = 5191;

// Signed out, the app renders its pages without the server, so none is started.
export default browserTestConfig({
  port,
  command: `pnpm exec vite --host 127.0.0.1 --port ${port} --strictPort`,
});
