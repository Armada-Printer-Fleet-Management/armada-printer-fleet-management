// @vitest-environment jsdom

import * as React from 'react';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, expect, it } from 'vitest';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './table';

afterEach(cleanup);

function renderTable(props: {
  tableRef?: React.Ref<HTMLTableElement>;
  tableClassName?: string;
  cellClassName?: string;
}) {
  render(
    <Table
      ref={props.tableRef}
      aria-label="People"
      className={props.tableClassName}
    >
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell className={props.cellClassName}>An Operator</TableCell>
        </TableRow>
      </TableBody>
    </Table>,
  );
}

it('renders native table semantics with column headers', () => {
  renderTable({});

  const table = screen.getByRole('table', { name: 'People' });
  expect(table.tagName).toBe('TABLE');
  const header = screen.getByRole('columnheader', { name: 'Name' });
  expect(header.getAttribute('scope')).toBe('col');
  expect(screen.getByRole('cell', { name: 'An Operator' })).toBeTruthy();
});

it('merges a caller className, letting a conflicting utility win', () => {
  renderTable({ tableClassName: 'text-base', cellClassName: 'px-2 italic' });

  const table = screen.getByRole('table');
  expect(table.classList.contains('text-base')).toBe(true);
  expect(table.classList.contains('text-sm')).toBe(false);
  const cell = screen.getByRole('cell');
  expect(cell.classList.contains('px-2')).toBe(true);
  expect(cell.classList.contains('px-4')).toBe(false);
  expect(cell.classList.contains('italic')).toBe(true);
  expect(cell.classList.contains('py-3')).toBe(true);
});

it('forwards its ref to the table element', () => {
  const ref = React.createRef<HTMLTableElement>();
  renderTable({ tableRef: ref });

  expect(ref.current).toBeInstanceOf(HTMLTableElement);
});
