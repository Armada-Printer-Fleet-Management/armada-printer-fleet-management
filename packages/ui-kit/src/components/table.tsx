import * as React from 'react';

import { cn } from '../lib/utils';

interface TableProps extends React.TableHTMLAttributes<HTMLTableElement> {
  /** Classes for the bordered box around the table, such as a height limit; it scrolls inside. */
  containerClassName?: string;
}

// A thin, themed scrollbar for the table.
const SCROLLBAR_CLASS = [
  'supports-[selector(::-webkit-scrollbar)]:[scrollbar-width:auto]',
  'supports-[selector(::-webkit-scrollbar)]:[scrollbar-color:auto]',
  '[&::-webkit-scrollbar]:size-2.5',
  '[&::-webkit-scrollbar:vertical]:[background:linear-gradient(to_bottom,var(--color-primary)_2.5rem,var(--color-border)_2.5rem,var(--color-border)_calc(2.5rem+1px),transparent_calc(2.5rem+1px))]',
  '[&::-webkit-scrollbar-track:vertical]:mt-[calc(2.5rem+1px)]',
  '[&::-webkit-scrollbar-track]:bg-transparent',
  '[&::-webkit-scrollbar-corner]:bg-transparent',
  '[&::-webkit-scrollbar-thumb]:rounded-full',
  '[&::-webkit-scrollbar-thumb]:bg-border',
  '[&::-webkit-scrollbar-thumb:hover]:bg-muted-foreground',
];

const Table = React.forwardRef<HTMLTableElement, TableProps>(
  ({ className, containerClassName, ...props }, ref) => (
    // The inner box scrolls, so a wide or tall table never stretches the page around it. The
    // outer box owns the rounded corners and clips to them: a box does not clip its own
    // scrollbar, so without it the coloured top of the scrollbar squares off the corner.
    <div
      className={cn(
        'flex w-full flex-col overflow-hidden rounded-lg border border-border bg-card',
        containerClassName,
      )}
    >
      <div className={cn('min-h-0 overflow-auto', SCROLLBAR_CLASS)}>
        <table
          ref={ref}
          className={cn(
            'w-full caption-bottom text-sm text-card-foreground',
            className,
          )}
          {...props}
        />
      </div>
    </div>
  ),
);
Table.displayName = 'Table';

const TableHeader = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  <thead
    ref={ref}
    className={cn(
      'bg-primary text-primary-foreground [&_tr]:border-b',
      className,
    )}
    {...props}
  />
));
TableHeader.displayName = 'TableHeader';

const TableBody = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  <tbody
    ref={ref}
    className={cn('[&_tr:last-child]:border-0', className)}
    {...props}
  />
));
TableBody.displayName = 'TableBody';

const TableRow = React.forwardRef<
  HTMLTableRowElement,
  React.HTMLAttributes<HTMLTableRowElement>
>(({ className, ...props }, ref) => (
  <tr
    ref={ref}
    className={cn('border-b border-border', className)}
    {...props}
  />
));
TableRow.displayName = 'TableRow';

const TableHead = React.forwardRef<
  HTMLTableCellElement,
  React.ThHTMLAttributes<HTMLTableCellElement>
>(({ className, scope = 'col', ...props }, ref) => (
  <th
    ref={ref}
    scope={scope}
    className={cn(
      'h-10 px-4 text-left align-middle font-semibold whitespace-nowrap',
      className,
    )}
    {...props}
  />
));
TableHead.displayName = 'TableHead';

const TableCell = React.forwardRef<
  HTMLTableCellElement,
  React.TdHTMLAttributes<HTMLTableCellElement>
>(({ className, ...props }, ref) => (
  <td
    ref={ref}
    className={cn('px-4 py-3 align-middle', className)}
    {...props}
  />
));
TableCell.displayName = 'TableCell';

const TableCaption = React.forwardRef<
  HTMLTableCaptionElement,
  React.HTMLAttributes<HTMLTableCaptionElement>
>(({ className, ...props }, ref) => (
  <caption ref={ref} className={cn('py-3 text-sm', className)} {...props} />
));
TableCaption.displayName = 'TableCaption';

export {
  Table,
  type TableProps,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
};
