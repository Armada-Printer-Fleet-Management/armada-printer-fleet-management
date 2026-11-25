import { expect, test } from '@playwright/test';

import {
  limits,
  nonTokenColours,
  openPage,
  overflowingContent,
  pageErrors,
  tabThrough,
  themes,
  tokenNames,
} from '../src';
import { kitchenSinkStates } from './kitchen-sink-states';

// A common laptop window, and a common phone (390 by 844 CSS pixels) as the narrowest likely.
const widths = [
  { name: 'desktop', width: 1280, height: 800 },
  { name: 'narrow', width: 390, height: 844 },
];

for (const theme of themes) {
  test.describe(`${theme} theme`, () => {
    for (const state of kitchenSinkStates) {
      test(`${state.name} draws only theme colours`, async ({ page }) => {
        await openPage(page, state.path, theme);
        expect(await nonTokenColours(page, tokenNames())).toEqual([]);
      });

      test(`${state.name} loads without errors`, async ({ page }) => {
        const errors = await pageErrors(page, () =>
          openPage(page, state.path, theme),
        );
        expect(errors).toEqual([]);
      });
    }

    for (const size of widths) {
      test(`nothing spills out of its box at ${size.name} width`, async ({
        page,
      }) => {
        await page.setViewportSize(size);
        await openPage(page, '/', theme);
        // Open sections show their content, the part most likely to overflow.
        await page.locator('details').evaluateAll((sections) => {
          for (const section of sections)
            (section as HTMLDetailsElement).open = true;
        });
        expect(await overflowingContent(page)).toEqual([]);
      });
    }

    test('every control shows where keyboard focus is', async ({ page }) => {
      await openPage(page, '/', theme);
      const unmarked: string[] = [];
      await tabThrough(page, async (target, name) => {
        const box = await target.boundingBox();
        if (!box) return;
        // The element plus the band around it where its focus ring can draw, on every side.
        const reach = limits.focusRingReachPx;
        const clip = {
          x: Math.max(0, box.x - reach),
          y: Math.max(0, box.y - reach),
          width: box.width + 2 * reach,
          height: box.height + 2 * reach,
        };
        const focused = await page.screenshot({ clip });
        const focusedElement = await page.evaluateHandle(
          () => document.activeElement,
        );
        await focusedElement.evaluate((element) =>
          (element as HTMLElement).blur(),
        );
        const blurred = await page.screenshot({ clip });
        await focusedElement.evaluate((element) =>
          (element as HTMLElement).focus(),
        );
        if (focused.equals(blurred)) unmarked.push(name);
      });
      expect(unmarked, 'focused controls drawn no differently').toEqual([]);
    });
  });
}
