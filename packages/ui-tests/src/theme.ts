import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import type { Page } from '@playwright/test';

export type Theme = 'light' | 'dark';
export const themes: readonly Theme[] = ['light', 'dark'];

const themeFolder = new URL('../../ui-kit/src/theme/', import.meta.url);

function themeFile(name: string): string {
  return readFileSync(fileURLToPath(new URL(name, themeFolder)), 'utf8');
}

/** Every token the theme declares, read from ui-kit's theme files so the tests never copy them. */
export function tokenNames(): string[] {
  const css = themeFile('defaults.css') + themeFile('fixed.css');
  return [...new Set(css.match(/--[a-z][a-z0-9-]*(?=\s*:)/g) ?? [])];
}

/** A token's Frost (light) and Graphite (dark) values, from its light-dark() in defaults.css. */
export function tokenValues(name: string): Record<Theme, string> {
  const pattern = new RegExp(
    `--${name}:[^;]*light-dark\\(\\s*(#[0-9a-f]+)\\s*,\\s*(#[0-9a-f]+)\\s*\\)`,
    'i',
  );
  const match = pattern.exec(themeFile('defaults.css'));
  if (!match?.[1] || !match[2]) {
    throw new Error(`--${name} has no light-dark() value in defaults.css`);
  }
  return { light: match[1], dark: match[2] };
}

/** #rrggbb as the rgb() string getComputedStyle reports. */
export function hexToRgb(hex: string): string {
  const value = Number.parseInt(hex.slice(1), 16);
  return `rgb(${(value >> 16) & 255}, ${(value >> 8) & 255}, ${value & 255})`;
}

// Tests check the state a colour settles in, so transitions are switched off rather than waited
// for.
const noMotion = `*, *::before, *::after {
  transition: none !important;
  animation: none !important;
}`;

/**
 * Opens a page with the OS reporting `theme`, then switches off motion. A page whose theme choice
 * is System, the default, follows the OS.
 */
export async function openPage(
  page: Page,
  path: string,
  theme: Theme,
): Promise<void> {
  await page.emulateMedia({ colorScheme: theme });
  await page.goto(path);
  await page.addStyleTag({ content: noMotion });
  await page.locator(`html[data-theme="${theme}"]`).waitFor();
}
