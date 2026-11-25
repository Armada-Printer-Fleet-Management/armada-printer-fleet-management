import { expect, test } from '@playwright/test';

import { layoutProblems } from '@armada/ui-tests';

const sizes = [
  { name: 'desktop', width: 1280, height: 800 },
  // Short, so a page with more content than fits has to scroll.
  { name: 'small laptop', width: 1024, height: 600 },
];

// The sidebar lists the main pages, so a page added to it is checked without changing this test.
test('every main navigation page lays out without clipping or doubled scroll bars', async ({
  page,
}) => {
  await page.goto('/');
  const paths = await page
    .getByRole('navigation')
    .getByRole('link')
    .evaluateAll((links) => [
      ...new Set(
        links.map((link) => new URL((link as HTMLAnchorElement).href).pathname),
      ),
    ]);
  expect(paths.length, 'sidebar links found').toBeGreaterThan(0);

  const problems: string[] = [];
  for (const size of sizes) {
    await page.setViewportSize(size);
    for (const path of paths) {
      await page.goto(path);
      await page.getByRole('main').waitFor();
      for (const problem of await layoutProblems(page)) {
        problems.push(`${path} at ${size.name} size: ${problem}`);
      }
    }
  }
  expect(problems).toEqual([]);
});
