import type { Page } from '@playwright/test';

import { limits } from './limits';

// Each check runs inside the page and returns one readable line per problem. Playwright sends a
// function to the browser as source text, so each is self-contained: no shared helpers, and the
// shared limits are passed in as an argument.

/**
 * Text, background and border colours that are not one of the theme's tokens, in the theme the
 * page is showing now. Colours are compared as the pixels a canvas draws, so rgb(), color() and
 * color-mix() results all compare alike.
 */
export function nonTokenColours(
  page: Page,
  tokens: string[],
): Promise<string[]> {
  return page.evaluate((names) => {
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 1;
    const context = canvas.getContext('2d', { willReadFrequently: true });
    if (!context) throw new Error('No 2D canvas');
    const pixel = (colour: string): string => {
      context.clearRect(0, 0, 1, 1);
      context.fillStyle = colour;
      context.fillRect(0, 0, 1, 1);
      return context.getImageData(0, 0, 1, 1).data.join(',');
    };

    const probe = document.createElement('div');
    document.body.append(probe);
    const allowed = new Set([pixel('transparent')]);
    for (const name of names) {
      probe.style.color = `var(${name})`;
      allowed.add(pixel(getComputedStyle(probe).color));
    }
    probe.remove();

    const describe = (element: Element): string =>
      element.tagName.toLowerCase() +
      (element.id ? `#${element.id}` : '') +
      (element.getAttribute('class')
        ? `.${element.getAttribute('class')?.trim().split(/\s+/).join('.')}`
        : '');
    const ownText = (element: Element): boolean =>
      [...element.childNodes].some(
        (node) => node.nodeType === Node.TEXT_NODE && node.textContent?.trim(),
      );

    const problems = new Set<string>();
    for (const element of document.body.querySelectorAll('*')) {
      if (!element.checkVisibility()) continue;
      const style = getComputedStyle(element);
      if (style.visibility !== 'visible' || style.opacity === '0') continue;
      const drawn: [string, string][] = [];
      if (ownText(element) || element instanceof SVGElement)
        drawn.push(['color', style.color]);
      drawn.push(['background-color', style.backgroundColor]);
      for (const side of ['top', 'right', 'bottom', 'left']) {
        if (
          Number.parseFloat(style.getPropertyValue(`border-${side}-width`)) > 0
        ) {
          drawn.push([
            `border-${side}-color`,
            style.getPropertyValue(`border-${side}-color`),
          ]);
        }
      }
      for (const [property, value] of drawn) {
        if (!allowed.has(pixel(value))) {
          problems.add(`${describe(element)} ${property}: ${value}`);
        }
      }
    }
    return [...problems];
  }, tokens);
}

/**
 * Content that spills out of its box: a child element or a run of text drawn past its parent's
 * edge, where the parent does not scroll or clip. Absolutely positioned children, such as
 * tooltips, are placed outside on purpose and are skipped.
 */
export function overflowingContent(page: Page): Promise<string[]> {
  return page.evaluate(({ tolerancePx: tolerance, excerptLength }) => {
    const describe = (element: Element): string =>
      element.tagName.toLowerCase() +
      (element.getAttribute('class')
        ? `.${element.getAttribute('class')?.trim().split(/\s+/).join('.')}`
        : '');
    const problems: string[] = [];
    if (document.documentElement.scrollWidth > window.innerWidth + tolerance) {
      problems.push(
        `the page scrolls sideways: ${document.documentElement.scrollWidth}px wide in a ${window.innerWidth}px window`,
      );
    }
    for (const parent of document.body.querySelectorAll('*')) {
      if (!parent.checkVisibility()) continue;
      const style = getComputedStyle(parent);
      if (style.overflowX !== 'visible' || style.overflowY !== 'visible')
        continue;
      if (style.display === 'inline' || style.display === 'contents') continue;
      const box = parent.getBoundingClientRect();
      for (const child of parent.childNodes) {
        let rect: DOMRect;
        let what: string;
        let sidewaysOnly = false;
        if (child instanceof Element) {
          if (!child.checkVisibility()) continue;
          const position = getComputedStyle(child).position;
          if (position === 'absolute' || position === 'fixed') continue;
          rect = child.getBoundingClientRect();
          what = describe(child);
        } else if (
          child.nodeType === Node.TEXT_NODE &&
          child.textContent?.trim()
        ) {
          const range = document.createRange();
          range.selectNodeContents(child);
          rect = range.getBoundingClientRect();
          what = `text "${child.textContent.trim().slice(0, excerptLength)}"`;
          sidewaysOnly = true;
        } else {
          continue;
        }
        if (rect.width === 0 && rect.height === 0) continue;
        const sideways =
          rect.right > box.right + tolerance ||
          rect.left < box.left - tolerance;
        const vertically =
          rect.bottom > box.bottom + tolerance ||
          rect.top < box.top - tolerance;
        if (sideways || (vertically && !sidewaysOnly)) {
          problems.push(`${what} spills out of ${describe(parent)}`);
        }
      }
    }
    return problems;
  }, limits);
}

/**
 * Layout problems on a full page: a scrolling area inside another one on the same axis (two
 * scroll bars), content past the window's edge that nothing scrolls to, and content cut off by
 * a box that clips without scrolling. Screen-reader-only text is clipped on purpose and skipped.
 */
export function layoutProblems(page: Page): Promise<string[]> {
  return page.evaluate(({ tolerancePx: tolerance, screenReaderOnlyPx }) => {
    const describe = (element: Element): string =>
      element.tagName.toLowerCase() +
      (element.getAttribute('class')
        ? `.${element.getAttribute('class')?.trim().split(/\s+/).join('.')}`
        : '');
    const root = document.scrollingElement ?? document.documentElement;
    const scrolls = (element: Element, axis: 'x' | 'y'): boolean => {
      if (element === root) {
        return axis === 'y'
          ? root.scrollHeight > window.innerHeight + tolerance
          : root.scrollWidth > window.innerWidth + tolerance;
      }
      const style = getComputedStyle(element);
      const overflow = axis === 'y' ? style.overflowY : style.overflowX;
      const room =
        axis === 'y'
          ? element.scrollHeight > element.clientHeight + tolerance
          : element.scrollWidth > element.clientWidth + tolerance;
      return (overflow === 'auto' || overflow === 'scroll') && room;
    };
    const clips = (element: Element): boolean => {
      const style = getComputedStyle(element);
      return [style.overflowX, style.overflowY].some(
        (value) => value === 'hidden' || value === 'clip',
      );
    };
    const screenReaderOnly = (element: Element): boolean => {
      for (
        let node: Element | null = element;
        node;
        node = node.parentElement
      ) {
        const rect = node.getBoundingClientRect();
        if (
          rect.width <= screenReaderOnlyPx &&
          rect.height <= screenReaderOnlyPx &&
          clips(node)
        )
          return true;
      }
      return false;
    };

    const problems: string[] = [];
    const elements = [...document.body.querySelectorAll('*')].filter(
      (element) =>
        element.checkVisibility() &&
        getComputedStyle(element).visibility === 'visible',
    );

    for (const axis of ['x', 'y'] as const) {
      const scrollers = [root, ...elements].filter((element) =>
        scrolls(element, axis),
      );
      for (const scroller of scrollers) {
        const outer = scrollers.find(
          (other) => other !== scroller && other.contains(scroller),
        );
        if (outer) {
          problems.push(
            `two ${axis === 'y' ? 'vertical' : 'horizontal'} scroll bars: ${describe(scroller)} scrolls inside ${describe(outer)}`,
          );
        }
      }
    }

    for (const element of elements) {
      if (screenReaderOnly(element)) continue;
      const rect = element.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) continue;
      let scrolledBy: Element | null = null;
      for (
        let parent = element.parentElement;
        parent;
        parent = parent.parentElement
      ) {
        if (scrolls(parent, 'x') || scrolls(parent, 'y')) {
          scrolledBy = parent;
          break;
        }
        if (
          !clips(parent) ||
          getComputedStyle(parent).textOverflow === 'ellipsis'
        )
          continue;
        const box = parent.getBoundingClientRect();
        if (
          rect.right > box.right + tolerance ||
          rect.bottom > box.bottom + tolerance ||
          rect.left < box.left - tolerance ||
          rect.top < box.top - tolerance
        ) {
          problems.push(
            `${describe(element)} is cut off by ${describe(parent)}`,
          );
          break;
        }
      }
      const pastWindow =
        rect.bottom > window.innerHeight + tolerance ||
        rect.right > window.innerWidth + tolerance;
      if (
        pastWindow &&
        !scrolledBy &&
        !scrolls(root, 'y') &&
        !scrolls(root, 'x')
      ) {
        problems.push(
          `${describe(element)} is past the window's edge and nothing scrolls to it`,
        );
      }
    }
    return [...new Set(problems)];
  }, limits);
}

/** What the page logged as an error, and every request that failed, while `run` ran. */
export async function pageErrors(
  page: Page,
  run: () => Promise<void>,
): Promise<string[]> {
  const errors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(`console: ${message.text()}`);
  });
  page.on('pageerror', (error) => errors.push(`uncaught: ${error.message}`));
  page.on('requestfailed', (request) =>
    errors.push(
      `request failed: ${request.url()} (${request.failure()?.errorText ?? 'unknown'})`,
    ),
  );
  page.on('response', (response) => {
    if (response.status() >= limits.firstErrorStatus)
      errors.push(`HTTP ${response.status()}: ${response.url()}`);
  });
  await run();
  return errors;
}
