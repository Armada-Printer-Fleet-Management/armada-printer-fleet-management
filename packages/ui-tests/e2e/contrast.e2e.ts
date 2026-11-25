import { expect, test } from '@playwright/test';

import {
  contrastFailures,
  expectWcagAA,
  openPage,
  tabThrough,
  themes,
} from '../src';
import { kitchenSinkStates } from './kitchen-sink-states';

// check_ui_theme.py checks every token pair before anything is drawn; these check what the
// browser actually draws, including states the tokens alone cannot show.
for (const theme of themes) {
  test.describe(`${theme} theme`, () => {
    for (const state of kitchenSinkStates) {
      test(`${state.name} meets WCAG A and AA`, async ({ page }) => {
        await openPage(page, state.path, theme);
        await expectWcagAA(page);
      });
    }

    test('text keeps its contrast on hover', async ({ page }) => {
      await openPage(page, '/', theme);
      const targets = page.locator(
        'button:visible, a[href]:visible, summary:visible, label:has(input):visible',
      );
      const failures: string[] = [];
      for (const target of await targets.all()) {
        await target.hover();
        failures.push(...(await contrastFailures(page, target)));
      }
      expect(failures, 'contrast failures while hovered').toEqual([]);
    });

    test('text keeps its contrast on keyboard focus', async ({ page }) => {
      await openPage(page, '/', theme);
      const failures: string[] = [];
      await tabThrough(page, async (target) => {
        failures.push(...(await contrastFailures(page, target)));
      });
      expect(failures, 'contrast failures while focused').toEqual([]);
    });
  });
}
