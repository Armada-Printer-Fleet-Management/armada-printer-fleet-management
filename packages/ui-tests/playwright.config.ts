import { browserTestConfig } from './src/playwright-config';

// Apart from the apps' own dev servers (desktop 5173, web 5174), so tests run while those are up.
const port = 5190;

export default browserTestConfig({
  port,
  command: `pnpm exec vite --config kitchen-sink/vite.config.ts --host 127.0.0.1 --port ${port} --strictPort`,
});
