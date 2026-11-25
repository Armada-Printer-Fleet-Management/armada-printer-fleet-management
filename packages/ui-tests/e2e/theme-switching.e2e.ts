import { expect, type Page, test } from '@playwright/test';

import { hexToRgb, type Theme, themes, tokenValues } from '../src';

const background = tokenValues('background');

async function expectTheme(page: Page, theme: Theme): Promise<void> {
  await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
  await expect(page.locator('body')).toHaveCSS(
    'background-color',
    hexToRgb(background[theme]),
  );
}

function themeChoice(page: Page, label: string) {
  // The radio itself is visually hidden; a person clicks the label drawn for it.
  return page.locator('label', {
    has: page.getByRole('radio', { name: label, exact: true }),
  });
}

for (const theme of themes) {
  test(`choosing ${theme === 'light' ? 'Light' : 'Dark'} shows the ${theme} theme`, async ({
    page,
  }) => {
    const other: Theme = theme === 'light' ? 'dark' : 'light';
    await page.emulateMedia({ colorScheme: other });
    await page.goto('/');
    await expectTheme(page, other);

    await themeChoice(page, theme === 'light' ? 'Light' : 'Dark').click();
    await expectTheme(page, theme);
  });

  test(`System follows an operating system set to ${theme}`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: theme });
    await page.goto('/?theme=system');
    await expectTheme(page, theme);
  });
}

test('System follows the operating system when it changes, without a reload', async ({
  page,
}) => {
  await page.emulateMedia({ colorScheme: 'light' });
  await page.goto('/?theme=system');
  await expectTheme(page, 'light');

  await page.emulateMedia({ colorScheme: 'dark' });
  await expectTheme(page, 'dark');

  await page.emulateMedia({ colorScheme: 'light' });
  await expectTheme(page, 'light');
});
