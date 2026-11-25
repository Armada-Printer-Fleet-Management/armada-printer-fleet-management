import { defineConfig, devices } from '@playwright/test';

export interface BrowserTestOptions {
  /** A port no other dev server uses, so tests run while the app's own dev server is up. */
  port: number;
  /** Starts the page under test on `port`, run from the directory of the calling config. */
  command: string;
}

/**
 * The Playwright settings every browser test suite in the repository shares. Each suite's own
 * playwright.config.ts passes the server it tests; its tests are e2e/**\/*.e2e.ts, a name
 * Vitest does not pick up.
 */
export function browserTestConfig({ port, command }: BrowserTestOptions) {
  const ci = Boolean(process.env.CI);
  const url = `http://127.0.0.1:${port}`;
  return defineConfig({
    testDir: './e2e',
    testMatch: '**/*.e2e.ts',
    fullyParallel: true,
    forbidOnly: ci,
    retries: ci ? 1 : 0,
    reporter: [['list'], ['html', { open: ci ? 'never' : 'on-failure' }]],
    use: {
      ...devices['Desktop Chrome'],
      baseURL: url,
      // No baselines: a screenshot is kept only to show what a failing test saw.
      screenshot: 'only-on-failure',
      trace: 'retain-on-failure',
    },
    webServer: { command, url, reuseExistingServer: !ci },
  });
}
