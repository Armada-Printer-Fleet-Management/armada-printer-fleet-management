// @vitest-environment jsdom

import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';

import { Pagination, type PaginationProps } from './pagination';

afterEach(cleanup);

function renderPagination(overrides: Partial<PaginationProps> = {}) {
  const props: PaginationProps = {
    page: 2,
    pageSize: 10,
    pageSizeOptions: [10, 20, 50, 100],
    rangeStart: 11,
    rangeEnd: 20,
    loadedCount: 50,
    hasMore: false,
    hasPrevious: true,
    hasNext: true,
    onPrevious: vi.fn(),
    onNext: vi.fn(),
    onPageSizeChange: vi.fn(),
    ...overrides,
  };
  render(<Pagination {...props} />);
  return props;
}

function isDisabled(name: string) {
  return screen.getByRole('button', { name }).hasAttribute('disabled');
}

it('marks the count as a lower bound while more can load', () => {
  renderPagination({ hasMore: true });
  expect(screen.getByText('Showing 11–20 of 50+')).toBeTruthy();
  cleanup();

  renderPagination({ hasMore: false });
  expect(screen.getByText('Showing 11–20 of 50')).toBeTruthy();
});

it('disables Previous and Next at the ends', () => {
  renderPagination({ hasPrevious: false, hasNext: true });
  expect([isDisabled('Previous'), isDisabled('Next')]).toEqual([true, false]);
  cleanup();

  renderPagination({ hasPrevious: true, hasNext: false });
  expect([isDisabled('Previous'), isDisabled('Next')]).toEqual([false, true]);
});

it('disables every control and reports busy while a page loads', () => {
  renderPagination({ busy: true });

  expect([isDisabled('Previous'), isDisabled('Next')]).toEqual([true, true]);
  expect(screen.getByLabelText('Rows per page').hasAttribute('disabled')).toBe(
    true,
  );
  expect(
    screen
      .getByRole('navigation', { name: 'Pagination' })
      .getAttribute('aria-busy'),
  ).toBe('true');
});

it('reports Previous, Next and a new page size', async () => {
  const props = renderPagination();

  await userEvent.click(screen.getByRole('button', { name: 'Previous' }));
  await userEvent.click(screen.getByRole('button', { name: 'Next' }));
  await userEvent.selectOptions(screen.getByLabelText('Rows per page'), '50');

  expect(props.onPrevious).toHaveBeenCalledOnce();
  expect(props.onNext).toHaveBeenCalledOnce();
  expect(props.onPageSizeChange).toHaveBeenCalledWith(50);
});
