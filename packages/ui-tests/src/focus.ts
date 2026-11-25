import type { Locator, Page } from '@playwright/test';

import { limits } from './limits';

const marker = 'data-ui-test-focused';
// Far more stops than any page here has, so only a focus loop that never ends reaches it.
const maximumStops = 200;

/**
 * Presses Tab through every focusable element once, calling `visit` at each stop with the
 * element a person sees: the focused element, or for a visually hidden input (a segmented
 * control's radio), the label drawn for it.
 */
export async function tabThrough(
  page: Page,
  visit: (target: Locator, name: string) => Promise<void>,
): Promise<void> {
  await page.mouse.move(0, 0);
  const seen = new Set<string>();
  for (let stop = 0; stop < maximumStops; stop++) {
    await page.keyboard.press('Tab');
    const identity = await page.evaluate(
      ({ name, screenReaderOnlyPx, excerptLength }) => {
        document.querySelector(`[${name}]`)?.removeAttribute(name);
        const active = document.activeElement;
        if (!active || active === document.body) return null;
        const rect = active.getBoundingClientRect();
        const drawn =
          rect.width <= screenReaderOnlyPx || rect.height <= screenReaderOnlyPx
            ? (active.closest('label') ?? active.parentElement ?? active)
            : active;
        drawn.setAttribute(name, '');
        const label =
          active.getAttribute('aria-label') ??
          (active.textContent?.trim() || active.getAttribute('value')) ??
          '';
        return `${active.tagName.toLowerCase()} "${label.slice(0, excerptLength)}" #${[...document.querySelectorAll('*')].indexOf(active)}`;
      },
      { name: marker, ...limits },
    );
    // Focus has left the page (to the browser) or come back round to where it started.
    if (identity === null || seen.has(identity)) return;
    seen.add(identity);
    await visit(page.locator(`[${marker}]`), identity);
  }
  throw new Error(`Tab did not cycle back within ${maximumStops} stops`);
}
