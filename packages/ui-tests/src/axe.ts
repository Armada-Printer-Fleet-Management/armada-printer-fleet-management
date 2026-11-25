import AxeBuilder from '@axe-core/playwright';
import { expect, type Locator, type Page } from '@playwright/test';

// WCAG 2.0, 2.1 and 2.2, levels A and AA: the standard this project commits to.
const wcagAA = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];

const marker = 'data-ui-test-target';

async function report(builder: AxeBuilder): Promise<string[]> {
  const { violations } = await builder.analyze();
  return violations.flatMap((violation) =>
    violation.nodes.map(
      (node) =>
        `${violation.id}: ${node.target.join(' ')}\n    ${node.failureSummary?.split('\n').slice(1).join(' ').trim() ?? ''}`,
    ),
  );
}

/** Every WCAG A and AA rule axe has, over the whole page. */
export async function expectWcagAA(page: Page): Promise<void> {
  const failures = await report(new AxeBuilder({ page }).withTags(wcagAA));
  expect(failures, 'axe WCAG A/AA violations').toEqual([]);
}

/** Colour contrast for one element, in whatever state (hover, focus) it is in right now. */
export async function contrastFailures(
  page: Page,
  target: Locator,
): Promise<string[]> {
  await target.evaluate(
    (element, name) => element.setAttribute(name, ''),
    marker,
  );
  try {
    return await report(
      new AxeBuilder({ page })
        .withRules(['color-contrast'])
        .include(`[${marker}]`),
    );
  } finally {
    await target.evaluate(
      (element, name) => element.removeAttribute(name),
      marker,
    );
  }
}
