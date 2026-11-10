// @vitest-environment node
import { readFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { expect, test } from 'vitest';
import { loadSlicerEngine } from './index';

const gen = fileURLToPath(new URL('../gen/', import.meta.url));
const pin = JSON.parse(
  readFileSync(new URL('../engine.pin.json', import.meta.url), 'utf8'),
) as {
  tag: string;
};

test('the fetched engine loads and reports the pinned version', async () => {
  const engine = await loadSlicerEngine(pathToFileURL(`${gen}CuraEngine.js`));

  // Release tags are v<engine version>-r<build>.
  expect(`v${engine.version()}`).toBe(pin.tag.replace(/-r\d+$/, ''));
});
