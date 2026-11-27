// @vitest-environment jsdom

import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, expect, it } from 'vitest';

import {
  Skeleton,
  SkeletonText,
  TableSkeleton,
  TableSkeletonRows,
} from './skeleton';
import { Table, TableBody, TableCell, TableRow } from './table';

afterEach(cleanup);

function bars(container: HTMLElement) {
  return Array.from(container.querySelectorAll('div[aria-hidden="true"]'));
}

it('hides the skeleton block from assistive technology', () => {
  const { container } = render(<Skeleton />);

  expect(container.firstElementChild?.getAttribute('aria-hidden')).toBe('true');
});

it('pulses only when the person has not asked for reduced motion', () => {
  const { container } = render(<Skeleton />);

  const classes = container.firstElementChild?.classList;
  expect(classes?.contains('motion-safe:animate-pulse')).toBe(true);
  expect(classes?.contains('animate-pulse')).toBe(false);
});

it('merges a caller className over the default shape', () => {
  const { container } = render(<Skeleton className="h-8 rounded-full" />);

  const classes = container.firstElementChild?.classList;
  expect(classes?.contains('h-8')).toBe(true);
  expect(classes?.contains('rounded-full')).toBe(true);
  expect(classes?.contains('rounded-md')).toBe(false);
});

it('announces skeleton text once, with its label or the default', () => {
  render(<SkeletonText />);
  expect(screen.getByRole('status').textContent).toBe('Loading');
  cleanup();

  render(<SkeletonText label="Loading notes" />);
  expect(screen.getByRole('status').textContent).toBe('Loading notes');
});

it('draws the requested number of lines, three by default', () => {
  const { container, rerender } = render(<SkeletonText />);
  expect(bars(container)).toHaveLength(3);

  rerender(<SkeletonText lines={4} />);
  expect(bars(container)).toHaveLength(4);
});

it('shortens only the last of several lines, and never a single line', () => {
  const { container, rerender } = render(<SkeletonText lines={3} />);
  expect(bars(container).map((bar) => bar.classList.contains('w-3/5'))).toEqual(
    [false, false, true],
  );

  rerender(<SkeletonText lines={1} />);
  const [only] = bars(container);
  expect(only?.classList.contains('w-full')).toBe(true);
});

it('announces a status and keeps the placeholder table from assistive technology', () => {
  render(<TableSkeleton columns={3} label="Loading users" />);

  expect(screen.getByRole('status').textContent).toContain('Loading users');
  expect(screen.queryByRole('table')).toBeNull();
});

it('draws rows by columns of placeholders, five rows by default', () => {
  const { container, rerender } = render(
    <TableSkeleton rows={2} columns={3} />,
  );
  const rows = container.querySelectorAll('tbody tr');
  expect(rows).toHaveLength(2);
  rows.forEach((row) => expect(row.querySelectorAll('td')).toHaveLength(3));

  rerender(<TableSkeleton columns={3} />);
  expect(container.querySelectorAll('tbody tr')).toHaveLength(5);
});

it('shows real header names when given, and bars when not', () => {
  const { container, rerender } = render(
    <TableSkeleton columns={2} headers={['Name', 'Email']} />,
  );
  expect(
    Array.from(container.querySelectorAll('th')).map((th) => th.textContent),
  ).toEqual(['Name', 'Email']);
  expect(container.querySelectorAll('th div[aria-hidden="true"]')).toHaveLength(
    0,
  );

  rerender(<TableSkeleton columns={2} />);
  expect(container.querySelectorAll('th div[aria-hidden="true"]')).toHaveLength(
    2,
  );
});

it('adds hidden rows under real ones without changing them', () => {
  const { container } = render(
    <Table aria-label="People">
      <TableBody>
        <TableRow>
          <TableCell>An Operator</TableCell>
        </TableRow>
        <TableSkeletonRows rows={2} columns={1} />
      </TableBody>
    </Table>,
  );

  expect(container.querySelectorAll('tbody tr')).toHaveLength(3);
  const visibleRows = screen.getAllByRole('row');
  expect(visibleRows).toHaveLength(1);
  expect(visibleRows[0]?.textContent).toBe('An Operator');
});
